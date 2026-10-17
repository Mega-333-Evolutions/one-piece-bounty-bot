"""
Download of images (and of any other file) from hosts that don't like being scripted.

This module deliberately imports nothing from the project (no constants, no Environment): the bot
uses it through download_utils.py, and scripts/download_character_images.py uses it standing on its
own, outside the bot's environment.

A download goes through these ways, in order, until one of them works:
1. urllib, sending the headers of a browser that is loading an image (see get_browser_headers)
2. curl_cffi, if it is installed: the same request, but with the TLS and HTTP/2 handshake of a real
   Chrome. A CDN can tell a script from a browser by that handshake alone, whatever the User-Agent
   header says, and answer 403 to the first one
3. An image proxy, if the IMAGE_PROXY_URL environment variable is set: another server downloads the
   image instead of this one, which is the way around a CDN that blocks the IP address of this one

Why a failure happened is never lost: every way that failed is logged, with its reason.
"""

from __future__ import annotations

import hashlib
import http
import logging
import os
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request

# The User-Agent of a real desktop Chrome. urllib's default one ("Python-urllib/3.x") is rejected
# outright by many hosts - Fandom's image CDN, where every Who's Who character image
# (assets/items/character.json) lives, among them - so every download has to look like a browser.
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Environment variable with the url of an image proxy, with {url} where the (url encoded) url of the
# image goes. For example: https://wsrv.nl/?url={url}&output=jpg
IMAGE_PROXY_ENV_NAME = "IMAGE_PROXY_URL"

# The file is not there (or the request is wrong): no other way of asking is going to change that
DEAD_LINK_STATUS_CODES = {400, 404, 410}

# Temporary problems of the server, worth asking again
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


class NotAnImageError(Exception):
    """The host answered successfully, but with something that isn't an image (e.g. a web page)."""


def get_browser_headers(url: str) -> dict:
    """
    Get the headers of a browser loading an image embedded in a web page: not only the
    User-Agent but everything a real browser sends along with it, since some hosts tell a script
    from a browser by that combination (and, for hotlink protection, by the Referer)
    :param url: The url of the file to download
    :return: The headers
    """

    parsed_url = urllib.parse.urlparse(url)
    referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    # Fandom's image CDN (https://static.wikia.nocookie.net/<wiki>/images/...): those images are
    # embedded by the pages of that wiki (https://<wiki>.fandom.com/), which is the page a browser
    # would send as the Referer
    if parsed_url.netloc.endswith("wikia.nocookie.net"):
        wiki = parsed_url.path.strip("/").split("/")[0]
        if wiki:
            referer = f"https://{wiki}.fandom.com/"

    return {
        "User-Agent": BROWSER_USER_AGENT,
        # No image/avif, which a browser would advertise: Pillow 10 can't open it
        "Accept": "image/webp,image/apng,image/png,image/jpeg,image/*;q=0.8,*/*;q=0.5",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer,
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }


def looks_like_image(head: bytes) -> bool:
    """
    Check if the first bytes of a file are those of an image format (by its signature, not by the
    file name or the Content-Type, which a host that is blocking you can set to anything)
    :param head: The first bytes of the file, at least 12 of them
    :return: True if it starts like an image
    """

    return (
        head.startswith(b"\xff\xd8\xff")  # JPEG
        or head.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
        or head.startswith((b"GIF87a", b"GIF89a"))  # GIF
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")  # WebP
        or head[4:8] == b"ftyp"  # AVIF, HEIC
        or head.startswith(b"BM")  # BMP
    )


def get_bundled_image_file_name(url: str) -> str:
    """
    Get the name the file of an image gets when it is saved next to the bot (bundled with it)
    instead of being downloaded each time. It is made from the url alone, and not from the
    revision of the file the url may point to, so the same image always gets the same name
    (https://static.wikia.nocookie.net/onepiece/images/f/f1/Abdullah_Anime_Infobox.png/revision/latest?cb=1
    -> Abdullah_Anime_Infobox.jpg)
    :param url: The url of the image
    :return: The file name, safe on any file system
    """

    parts = [part for part in urllib.parse.urlparse(url).path.split("/") if part]
    if "revision" in parts:
        parts = parts[: parts.index("revision")]

    original_name = urllib.parse.unquote(parts[-1]) if parts else ""
    original_stem = original_name.rsplit(".", 1)[0] if "." in original_name else original_name

    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", original_stem).strip("._")

    # Names that had to be changed could end up the same (or empty), so they carry what tells them apart
    if stem != original_stem or not stem:
        digest = hashlib.sha1(original_stem.encode("utf-8") or url.encode("utf-8")).hexdigest()
        stem = f"{stem}-{digest[:8]}" if stem else digest[:16]

    return f"{stem}.jpg"


def get_image_proxy_url() -> str | None:
    """
    Get the image proxy url template that is set up, if there is one and it is usable
    :return: The template, or None
    """

    template = (os.environ.get(IMAGE_PROXY_ENV_NAME) or "").strip()
    if not template:
        return None

    if "{url}" not in template:
        logging.warning(
            f"Ignoring {IMAGE_PROXY_ENV_NAME}: it has to contain {{url}}, where the url of the "
            f"image goes (e.g. https://wsrv.nl/?url={{url}}&output=jpg)"
        )
        return None

    return template


def is_browser_impersonation_available() -> bool:
    """
    Check if curl_cffi, which downloads like a real Chrome, is installed
    :return: True if it is
    """

    try:
        import curl_cffi  # noqa: F401

        return True
    except Exception:  # Not installed, or not working on this platform
        return False


def describe_error(error: BaseException) -> str:
    """
    Describe an error in a line
    :param error: The error
    :return: What happened
    """

    if isinstance(error, urllib.error.HTTPError):
        return str(error)

    return f"{type(error).__name__}: {error}"


def fetch_to_file(
    url: str,
    file_path: str,
    timeout: float = 30,
    expect_image: bool = False,
    proxy_url: str | None = None,
) -> str:
    """
    Download a file the way a browser would, trying every way there is (see the top of this file)
    until one works
    :param url: The url of the file
    :param file_path: Where to save it
    :param timeout: Seconds to wait for the host in every request
    :param expect_image: If the file has to be an image. A host that blocks you often answers with a
    web page instead of an error, which is then not taken as a download that worked
    :param proxy_url: Url template of the image proxy to use as the last way. Default: the one of
    the IMAGE_PROXY_URL environment variable, if any
    :return: The name of the way that worked
    :raises: The error of the first way (urllib) if none of them worked, so that whoever calls
    this can tell a dead link (HTTPError 404) from a blocked one (HTTPError 403) as always
    """

    if proxy_url is None:
        proxy_url = get_image_proxy_url()

    first_error = None
    failures = []

    for way_name, way in _iter_ways(url, file_path, timeout, proxy_url):
        try:
            way()
            if expect_image:
                _check_file_is_image(file_path)

            if failures:
                logging.info(f"Downloaded {url} through {way_name} after: {'; '.join(failures)}")
            return way_name

        except Exception as e:
            _remove_quietly(file_path)
            failures.append(f"{way_name}: {describe_error(e)}")
            if first_error is None:
                first_error = e

            # The file is gone, there is no better way to ask for it
            if _is_dead_link(e):
                break

    logging.warning(f"Could not download {url} - {'; '.join(failures)}")

    # For whoever wants to show why every way failed, not only the first
    first_error.download_failures = failures
    raise first_error


def _iter_ways(url: str, file_path: str, timeout: float, proxy_url: str | None):
    """
    Get the ways to download a file, in the order they are tried. It is a generator on purpose: the
    ones after urllib (curl_cffi isn't even loaded) are only looked at if urllib didn't work
    :param url: The url of the file
    :param file_path: Where to save it
    :param timeout: Seconds to wait for the host in every request
    :param proxy_url: The url template of the image proxy, if there is one
    :return: (name of the way, function that downloads the file that way)
    """

    yield "urllib", lambda: _fetch_with_urllib(url, file_path, timeout)

    if is_browser_impersonation_available():
        yield (
            "browser impersonation (curl_cffi)",
            lambda: _fetch_with_browser_impersonation(url, file_path, timeout),
        )

    if proxy_url:
        yield (
            "image proxy",
            lambda: _fetch_through_image_proxy(url, file_path, timeout, proxy_url),
        )


def _is_dead_link(error: BaseException) -> bool:
    """
    Check if an error says that the file is not there
    :param error: The error
    :return: True if it is
    """

    return isinstance(error, urllib.error.HTTPError) and error.code in DEAD_LINK_STATUS_CODES


def _remove_quietly(file_path: str) -> None:
    """
    Remove a (partially) downloaded file, if it is there
    :param file_path: The file
    :return: None
    """

    try:
        os.remove(file_path)
    except OSError:
        pass


def _check_file_is_image(file_path: str) -> None:
    """
    Check that a downloaded file is an image
    :param file_path: The file
    :return: None
    :raises NotAnImageError: If it is not
    """

    with open(file_path, "rb") as file:
        head = file.read(32)

    if not looks_like_image(head):
        raise NotAnImageError(f"the host sent something that is not an image: {head[:24]!r}")


def _fetch_with_urllib(url: str, file_path: str, timeout: float, attempts: int = 3) -> None:
    """
    Download a file with urllib, sending the headers of a browser
    :param url: The url of the file
    :param file_path: Where to save it
    :param timeout: Seconds to wait for the host in every request
    :param attempts: How many times to ask when the problem looks temporary
    :return: None
    """

    request = urllib.request.Request(url, headers=get_browser_headers(url))

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                with open(file_path, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)
            return

        except urllib.error.HTTPError as e:
            # Retry transient server-side or rate limit errors
            if attempt < attempts - 1 and e.code in RETRYABLE_STATUS_CODES:
                time.sleep(1)
                continue
            raise

        except urllib.error.URLError:
            if attempt < attempts - 1:
                time.sleep(1)
                continue
            raise


def _fetch_with_browser_impersonation(url: str, file_path: str, timeout: float) -> None:
    """
    Download a file with curl_cffi, which does the TLS and HTTP/2 handshake of a real Chrome (and
    sends the headers that go with it, so the User-Agent is left to it)
    :param url: The url of the file
    :param file_path: Where to save it
    :param timeout: Seconds to wait for the host
    :return: None
    """

    from curl_cffi import requests as curl_requests  # Optional dependency

    headers = get_browser_headers(url)
    for header in ("User-Agent", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform"):
        headers.pop(header)

    response = curl_requests.get(
        url, headers=headers, impersonate="chrome", timeout=timeout, allow_redirects=True
    )

    if response.status_code != 200:
        raise urllib.error.HTTPError(
            url, response.status_code, _get_status_phrase(response.status_code), None, None
        )

    with open(file_path, "wb") as out_file:
        out_file.write(response.content)


def _fetch_through_image_proxy(url: str, file_path: str, timeout: float, proxy_url: str) -> None:
    """
    Download a file through an image proxy: the proxy asks the host for it, not this server
    :param url: The url of the file
    :param file_path: Where to save it
    :param timeout: Seconds to wait for the proxy
    :param proxy_url: The url template of the proxy, with {url} where the url of the file goes
    :return: None
    """

    proxied_url = proxy_url.replace("{url}", urllib.parse.quote(url, safe=""))
    _fetch_with_urllib(proxied_url, file_path, timeout, attempts=2)


def _get_status_phrase(status_code: int) -> str:
    """
    Get the standard phrase of an HTTP status code
    :param status_code: The status code
    :return: The phrase (e.g. Forbidden)
    """

    try:
        return http.HTTPStatus(status_code).phrase
    except ValueError:
        return "Unknown status"
