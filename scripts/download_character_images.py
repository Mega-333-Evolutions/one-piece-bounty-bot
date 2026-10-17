#!/usr/bin/env python3
"""
Download the images of the Who's Who characters once, so that they come with the bot instead of
being downloaded from Fandom's image server every time a game starts.

Why: that server can refuse the downloads of the machine the bot runs on (answering 403 whatever
headers are sent), and then Who's Who can't start a single game. Run this on any machine that CAN
download them - your own computer, where the images open in a browser - and deploy the result with
the bot, which uses these images first and only downloads the ones that are missing.

Usage, from the project folder:
    pip install Pillow          (the bot needs it already)
    pip install curl_cffi       (optional: downloads like a real Chrome, for hosts that tell a
                                 script from a browser by the TLS handshake)
    python scripts/download_character_images.py

It's safe to stop it and run it again: the images already downloaded are skipped.
Then commit the new files (they are .jpg, like the other images of the bot):
    git add assets/images/characters
    git commit -m "Add the images of the characters"
    git push
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import logging
import os
import sys
import tempfile
import threading
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CHARACTERS_FILE = os.path.join(ROOT_DIR, "assets", "items", "character.json")
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "assets", "images", "characters")

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is needed to run this: pip install Pillow")


def load_image_fetch():
    """
    Load src/utils/image_fetch.py, the code the bot downloads images with, from its file: it
    needs nothing else of the bot, so this works without the bot's environment (or its packages)
    :return: The module
    """

    path = os.path.join(ROOT_DIR, "src", "utils", "image_fetch.py")
    spec = importlib.util.spec_from_file_location("image_fetch", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["image_fetch"] = module  # (a module needs to be there to define classes)
    spec.loader.exec_module(module)
    return module


image_fetch = load_image_fetch()
print_lock = threading.Lock()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the images of the Who's Who characters to ship them with the bot."
    )
    parser.add_argument(
        "--characters-file",
        default=DEFAULT_CHARACTERS_FILE,
        help="The json with the characters (default: assets/items/character.json)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help="Where to save the images (default: assets/images/characters)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=1200,
        help="Longest side, in pixels, of the saved images; bigger ones are shrunk (default: 1200)",
    )
    parser.add_argument(
        "--quality", type=int, default=85, help="JPEG quality of the saved images (default: 85)"
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Downloads at the same time (default: 4)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Seconds every download waits before the next one, to be gentle (default: 0.2)",
    )
    parser.add_argument(
        "--timeout", type=float, default=30, help="Seconds to wait for the host (default: 30)"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Only download this many images, to try it out"
    )
    parser.add_argument(
        "--force", action="store_true", help="Download again the images that are already there"
    )
    parser.add_argument(
        "--proxy-url",
        default=None,
        help=f"Image proxy to use as the last way, with {{url}} where the image url goes "
        f"(default: the {image_fetch.IMAGE_PROXY_ENV_NAME} environment variable)",
    )
    return parser.parse_args()


def is_valid_image(path: str) -> bool:
    """
    Check that a file is a complete image
    :param path: The file
    :return: True if it is
    """

    try:
        with Image.open(path) as image:
            image.load()
        return True
    except Exception:
        return False


def save_as_bundled_image(source_path: str, target_path: str, max_size: int, quality: int) -> int:
    """
    Save a downloaded image the way the bot uses it: as a JPEG that isn't bigger than needed. The
    colors are converted the way the bot does it when it blurs the image, so the images the players
    get are the same as before
    :param source_path: The downloaded file
    :param target_path: Where to save the image
    :param max_size: The longest side, in pixels
    :param quality: The JPEG quality
    :return: The size of the saved image, in bytes
    """

    with Image.open(source_path) as image:
        image.load()
        image = image.convert("RGB")

    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.LANCZOS)

    # Written aside and renamed, so that stopping the script never leaves a half-written image
    partial_path = f"{target_path}.partial"
    image.save(partial_path, format="JPEG", quality=quality, optimize=True)
    os.replace(partial_path, target_path)

    return os.path.getsize(target_path)


def is_dead_link(error: BaseException) -> bool:
    """
    Check if an error of a download says that the image is not there
    :param error: The error
    :return: True if it does
    """

    return (
        isinstance(error, urllib.error.HTTPError)
        and error.code in image_fetch.DEAD_LINK_STATUS_CODES
    )


def classify_failure(error: BaseException) -> str:
    """
    Group the errors that mean the same
    :param error: The error of the download
    :return: What the error means
    """

    if isinstance(error, urllib.error.HTTPError):
        if is_dead_link(error):
            return f"HTTP {error.code}: the image is not there (dead link)"
        return f"HTTP {error.code} {error.reason}: the host refused the download"

    if isinstance(error, image_fetch.NotAnImageError):
        return "the host answered with something that is not an image (a block page?)"

    if isinstance(error, urllib.error.URLError):
        return f"network error: {error.reason}"

    return f"{type(error).__name__}: {error}"


def download_one(name: str, url: str, target_path: str, args: argparse.Namespace) -> tuple:
    """
    Download, convert and save the image of a character
    :return: (name, url, error or None, size of the saved image in bytes)
    """

    descriptor, temp_path = tempfile.mkstemp(prefix="character_image_", suffix=".download")
    os.close(descriptor)

    try:
        image_fetch.fetch_to_file(
            url, temp_path, timeout=args.timeout, expect_image=True, proxy_url=args.proxy_url
        )
        size = save_as_bundled_image(temp_path, target_path, args.max_size, args.quality)
        return name, url, None, size
    except Exception as e:
        return name, url, e, 0
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        time.sleep(args.delay)


def main() -> int:
    args = parse_args()

    # The way the bot downloads logs why every way failed; this script does it itself, in the end
    logging.basicConfig(level=logging.CRITICAL)

    if args.proxy_url is None:
        args.proxy_url = image_fetch.get_image_proxy_url()

    with open(args.characters_file, encoding="utf-8") as file:
        characters = json.load(file)

    # One file per image (characters can share one)
    images: dict[str, tuple[str, str]] = {}
    without_image = []
    for character in characters:
        url = character.get("anime_image_url")
        if not url:
            without_image.append(character.get("name", "?"))
            continue
        images.setdefault(image_fetch.get_bundled_image_file_name(url), (character["name"], url))

    os.makedirs(args.output, exist_ok=True)

    pending = []
    already_there = 0
    for file_name, (name, url) in images.items():
        target_path = os.path.join(args.output, file_name)
        if not args.force and os.path.isfile(target_path) and is_valid_image(target_path):
            already_there += 1
        else:
            pending.append((name, url, target_path))

    if args.limit:
        pending = pending[: args.limit]

    print(f"{len(characters)} characters, {len(images)} different images")
    print(f"{already_there} already downloaded, {len(pending)} to download into {args.output}")

    ways = ["urllib"]
    if image_fetch.is_browser_impersonation_available():
        ways.append("curl_cffi (like Chrome)")
    if args.proxy_url:
        ways.append(f"image proxy {args.proxy_url}")
    print(f"Downloading with: {', then '.join(ways)}")
    print()

    saved = 0
    saved_bytes = 0
    failures = []

    executor = ThreadPoolExecutor(max_workers=max(1, args.workers))
    try:
        futures = [executor.submit(download_one, *item, args) for item in pending]
        for done, future in enumerate(as_completed(futures), start=1):
            name, url, error, size = future.result()
            with print_lock:
                if error is None:
                    saved += 1
                    saved_bytes += size
                    print(f"[{done}/{len(pending)}] ok      {name} ({size // 1024} KB)")
                else:
                    failures.append((name, url, error))
                    print(f"[{done}/{len(pending)}] FAILED  {name}: {classify_failure(error)}")
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        print("\nStopped. Run it again to go on where it was left.")
        return 130
    executor.shutdown()

    print()
    print(f"Downloaded {saved} images ({saved_bytes / 1024 / 1024:.1f} MB)")
    if without_image:
        print(f"{len(without_image)} characters have no image url: {', '.join(without_image)}")

    if failures:
        reasons = collections.Counter(classify_failure(error) for _, _, error in failures)
        print(f"\n{len(failures)} images could not be downloaded:")
        for reason, count in reasons.most_common():
            print(f"  {count:>4} x {reason}")

        # What every way of downloading said about the first of them
        name, url, error = failures[0]
        print(f"\nFor example, {name} ({url}):")
        for failure in getattr(error, "download_failures", [image_fetch.describe_error(error)]):
            print(f"  - {failure}")

        dead = [name for name, _, error in failures if is_dead_link(error)]
        refused = len(failures) - len(dead)
        if dead:
            print(
                f"\n{len(dead)} images are not on the wiki anymore, so Who's Who can't use these "
                f"characters (it picks another one when it hits them): {', '.join(dead)}"
            )
        if refused:
            print(
                f"\n{refused} downloads were refused or failed. If this machine is refused too: "
                f"pip install curl_cffi (downloads like a real Chrome) and run it again, or set "
                f"{image_fetch.IMAGE_PROXY_ENV_NAME}=https://wsrv.nl/?url={{url}}&output=jpg "
                f"(an image proxy) and run it again - the images that were saved are skipped."
            )
        print()

    print(f"{already_there + saved} of {len(images)} images are in {args.output}")
    if saved:
        print(
            "\nNow commit them, so they get deployed with the bot:\n"
            "  git add assets/images/characters\n"
            '  git commit -m "Add the images of the characters"\n'
            "  git push"
        )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
