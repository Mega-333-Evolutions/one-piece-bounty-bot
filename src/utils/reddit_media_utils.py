"""
The media of the reddit posts, as files that Telegram takes: the videos (v.redd.it), with their
sound and subtitles, the pictures and the GIFs.

Reddit keeps the picture of a video, its sound and its subtitles in different files, and the
address that the post gives for the video (fallback_url) is the picture alone. A video sent like
that has no audio track, and Telegram shows a video without sound as a GIF. So here the pieces are
put together (without converting anything: the file is not re-encoded, so it takes seconds and no
processing power) into one mp4 that has the picture, the sound and the subtitles that the video has
on reddit:

1. Through the HLS playlist of the video, which lists the picture (in every quality), the sound
   and the subtitles of it. The picture of the best quality that fits in what Telegram takes is
   used.
2. If that doesn't work, through the files of the video (DASH_720.mp4, DASH_AUDIO_128.mp4 ...),
   which are next to the one of the post.
3. If that doesn't work either, or ffmpeg is not installed, the picture alone, as it was sent
   before.

ffmpeg is the one of the system if there is one, or the one that the imageio-ffmpeg package brings
(it is in requirements.txt, so there is one wherever the bot is installed with pip).

A media that can't be sent for good (it is gone, or too big) raises RedditMediaUnavailableError,
and one that failed for a reason that may go away (reddit or the network are failing) raises
RedditMediaError or a urllib error, so that whoever sends the post can tell what to do with each.
"""

from __future__ import annotations

import functools
import logging
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from PIL import Image, UnidentifiedImageError

from src.utils.download_utils import generate_temp_file_path
from src.utils.image_fetch import (
    BROWSER_USER_AGENT,
    NotAnImageError,
    describe_error,
    fetch_to_file,
    get_browser_headers,
)
from src.utils.rich_message_utils import BOT_API_UPLOAD_LIMIT_BYTES

# What of the limit of the upload is left free, for what is not the video (the rest of the message)
UPLOAD_MARGIN_BYTES = 2 * 1024 * 1024
MAX_VIDEO_BYTES = BOT_API_UPLOAD_LIMIT_BYTES - UPLOAD_MARGIN_BYTES

# How long ffmpeg may take to put a video together
FFMPEG_TIMEOUT_SECONDS = 300

# The seconds the files of a video may take to download
DOWNLOAD_TIMEOUT_SECONDS = 60

# Telegram takes photos of 10 MB at most, and not of more than 10000 pixels between the width and
# the height. A photo that has more is made smaller, in the way that loses the least
MAX_PHOTO_BYTES = 9 * 1024 * 1024
MAX_PHOTO_SIDES_SUM = 9800
# (how much smaller than the picture, quality of the JPEG), from the one that loses the least
PHOTO_SHRINK_STEPS = ((1.0, 88), (1.0, 75), (0.8, 75), (0.6, 70), (0.45, 65), (0.3, 60))

# The status codes with which a host says that a file is not there (v.redd.it says 403 for it too)
GONE_STATUS_CODES = (400, 403, 404, 410)

# What ffmpeg says, as a warning before it goes on, of a piece of a playlist it could not get
SKIPPED_PIECE_MESSAGE = "Failed to open segment"

# How many qualities of the video are tried when the first one is too big
MAX_QUALITIES_TRIED = 3

# The names that reddit has given to the file with the sound of a video, next to the picture
AUDIO_FILE_NAMES = ("DASH_AUDIO_128.mp4", "DASH_AUDIO_64.mp4", "DASH_audio.mp4", "audio")
# The qualities (the height of the picture) that a video may have a file for
DASH_HEIGHTS = (1080, 720, 480, 360, 240)
# Where reddit keeps the (English) captions of a video, when the playlists don't list them
CAPTIONS_FILE_NAME = "wh_ben_en.vtt"

# The code of the language in the subtitles of the mp4 (3 letters)
LANGUAGE_CODES = {
    "ar": "ara",
    "de": "deu",
    "en": "eng",
    "es": "spa",
    "fa": "fas",
    "fr": "fra",
    "hi": "hin",
    "id": "ind",
    "it": "ita",
    "ja": "jpn",
    "ko": "kor",
    "nl": "nld",
    "pl": "pol",
    "pt": "por",
    "ru": "rus",
    "sv": "swe",
    "th": "tha",
    "tr": "tur",
    "uk": "ukr",
    "vi": "vie",
    "zh": "zho",
}
UNKNOWN_LANGUAGE_CODE = "und"


class RedditMediaError(Exception):
    """The media can't be got (and it may work another time)"""


class RedditMediaUnavailableError(RedditMediaError):
    """The media can't be sent, and never will: it is gone, or too big for Telegram"""


@dataclass
class RedditVideoSource:
    """Where reddit has the video of a post"""

    fallback_url: str | None = None
    hls_url: str | None = None
    dash_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None


@dataclass
class PreparedVideo:
    """A video, as a file that is ready to be sent"""

    path: str
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    has_audio: bool = False
    subtitle_count: int = 0


@dataclass
class HlsRendition:
    """The sound or the subtitles of a video, in a playlist"""

    url: str
    language: str | None = None
    is_default: bool = False


@dataclass
class HlsVariant:
    """The picture of a video in one quality, in a playlist"""

    url: str
    bandwidth: int = 0
    width: int | None = None
    height: int | None = None
    audios: list[HlsRendition] = field(default_factory=list)
    subtitles: list[HlsRendition] = field(default_factory=list)


@functools.lru_cache(maxsize=1)
def get_ffmpeg_path() -> str | None:
    """
    Get the ffmpeg to use: the one of the system, or the one of the imageio-ffmpeg package
    :return: The path of ffmpeg, None if there is none
    """

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # Not installed, or without a binary for this system
        return None


def get_language_code(language: str | None) -> str:
    """
    Get the code of a language that the mp4 takes
    :param language: The code of the playlist (en, en-US, eng...)
    :return: The code of 3 letters (eng), und if it is not known
    """

    if not language:
        return UNKNOWN_LANGUAGE_CODE

    language = language.lower().split("-")[0]
    if language in LANGUAGE_CODES:
        return LANGUAGE_CODES[language]

    return language if len(language) == 3 and language.isalpha() else UNKNOWN_LANGUAGE_CODE


# -------------------------------------------------------------------------------------------------
# The playlist of the video (HLS)
# -------------------------------------------------------------------------------------------------

_ATTRIBUTE_REGEX = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')


def _parse_attributes(text: str) -> dict[str, str]:
    """
    Parse the attributes of a line of a playlist (BANDWIDTH=2400000,RESOLUTION=720x1280...)
    :param text: The attributes
    :return: The attributes, without the quotes of their values
    """

    return {name: value.strip('"') for name, value in _ATTRIBUTE_REGEX.findall(text)}


def parse_hls_master_playlist(text: str, base_url: str) -> list[HlsVariant]:
    """
    Parse the playlist of a video, which lists the picture of it in every quality, with its sound
    and subtitles
    :param text: The playlist
    :param base_url: The address of the playlist, which the addresses in it are relative to
    :return: The qualities of the picture, with the best one first. A playlist that is not of the
    kind that lists them (it is the picture itself) is the only quality of it
    """

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # The sound and the subtitles, by the group that the qualities of the picture ask for
    media: dict[tuple[str, str], list[HlsRendition]] = {}
    for line in lines:
        if not line.startswith("#EXT-X-MEDIA:"):
            continue

        attributes = _parse_attributes(line.split(":", 1)[1])
        media_type = attributes.get("TYPE", "")
        if media_type not in ("AUDIO", "SUBTITLES") or not attributes.get("URI"):
            continue

        media.setdefault((media_type, attributes.get("GROUP-ID", "")), []).append(
            HlsRendition(
                url=urllib.parse.urljoin(base_url, attributes["URI"]),
                language=attributes.get("LANGUAGE"),
                is_default=attributes.get("DEFAULT", "NO").upper() == "YES",
            )
        )

    variants: list[HlsVariant] = []
    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:"):
            continue
        if index + 1 >= len(lines) or lines[index + 1].startswith("#"):
            continue

        attributes = _parse_attributes(line.split(":", 1)[1])
        width = height = None
        if match := re.fullmatch(r"(\d+)x(\d+)", attributes.get("RESOLUTION", "")):
            width, height = int(match.group(1)), int(match.group(2))

        bandwidth = attributes.get("AVERAGE-BANDWIDTH") or attributes.get("BANDWIDTH") or "0"
        variants.append(
            HlsVariant(
                url=urllib.parse.urljoin(base_url, lines[index + 1]),
                bandwidth=int(bandwidth) if bandwidth.isdigit() else 0,
                width=width,
                height=height,
                audios=media.get(("AUDIO", attributes.get("AUDIO", "")), []),
                subtitles=media.get(("SUBTITLES", attributes.get("SUBTITLES", "")), []),
            )
        )

    # The playlist is the one of the picture itself, not the one that lists its qualities
    if not variants and any(line.startswith("#EXTINF") for line in lines):
        variants.append(HlsVariant(url=base_url))

    return sorted(
        variants, key=lambda variant: (variant.height or 0, variant.bandwidth), reverse=True
    )


def add_subtitles_to_playlist_url(url: str) -> str:
    """
    Ask for the subtitles in the address of the playlist of a video. Reddit doesn't list them
    in the playlist unless it is asked to ("f=...,subsAll")
    :param url: The address of the playlist
    :return: The address that asks for them
    """

    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

    qualities = [part for part in query.get("f", ["hd"])[0].split(",") if part]
    if "subsAll" not in qualities:
        qualities.append("subsAll")
    query["f"] = [",".join(qualities)]

    return urllib.parse.urlunparse(
        parsed._replace(query=urllib.parse.urlencode(query, doseq=True))
    )


# -------------------------------------------------------------------------------------------------
# ffmpeg
# -------------------------------------------------------------------------------------------------


def _get_input_options(source: str) -> list[str]:
    """
    Get the options of ffmpeg for a file that it reads
    :param source: The file, or its address
    :return: The options
    """

    if not source.startswith(("http://", "https://")):
        return []

    options = [
        "-user_agent",
        BROWSER_USER_AGENT,
        "-rw_timeout",
        "30000000",
        "-protocol_whitelist",
        "http,https,tcp,tls,crypto",
    ]
    if urllib.parse.urlparse(source).path.endswith(".m3u8"):
        # The pieces of the video of reddit are not all named the way ffmpeg wants them to be
        options += ["-allowed_extensions", "ALL"]

    return options


def build_ffmpeg_command(
    ffmpeg: str,
    video: str,
    audio: str | None,
    subtitles: list[tuple[str, str | None]],
    output_path: str,
) -> list[str]:
    """
    Build the command of ffmpeg that puts the picture, the sound and the subtitles of a video
    together
    :param ffmpeg: The path of ffmpeg
    :param video: The file with the picture, or its address
    :param audio: The file with the sound, or its address. None if the video has none
    :param subtitles: (the file with the subtitles or its address, the language of them)
    :param output_path: Where to save the video
    :return: The command
    """

    # (warnings are what says that a piece of a playlist was left out, see run_ffmpeg)
    command = [ffmpeg, "-hide_banner", "-loglevel", "warning", "-nostdin", "-y"]
    sources = [video] + ([audio] if audio else []) + [subtitle for subtitle, _ in subtitles]
    for source in sources:
        command += _get_input_options(source) + ["-i", source]

    command += ["-map", "0:v:0", "-c:v", "copy"]
    if audio:
        # (the bitstream filter is what an mp4 needs for the audio of the segments of a playlist,
        # and it leaves alone the audio that doesn't need it)
        command += ["-map", "1:a:0", "-c:a", "copy", "-bsf:a", "aac_adtstoasc"]

    first_subtitle_index = 2 if audio else 1
    for index, (_, language) in enumerate(subtitles):
        command += [
            "-map",
            f"{first_subtitle_index + index}:s:0",
            f"-metadata:s:s:{index}",
            f"language={get_language_code(language)}",
        ]
    if subtitles:
        command += ["-c:s", "mov_text"]

    # The video can be watched while it is downloaded, which is what Telegram wants
    command += ["-movflags", "+faststart", output_path]
    return command


def run_ffmpeg(command: list[str]) -> None:
    """
    Run ffmpeg
    :param command: The command
    :return: None
    :raises RedditMediaError: If ffmpeg fails
    """

    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise RedditMediaError(f"ffmpeg took more than {FFMPEG_TIMEOUT_SECONDS} seconds") from None
    except OSError as e:
        raise RedditMediaError(f"ffmpeg can't run: {e}") from None

    if result.returncode != 0:
        raise RedditMediaError(f"ffmpeg failed: {result.stderr.strip()[-400:]}")

    # ffmpeg leaves out a piece of a playlist that it can't get and makes the video without it (a
    # part of the sound or the picture is missing), with nothing but this warning to say so
    skipped = next(
        (line for line in result.stderr.splitlines() if SKIPPED_PIECE_MESSAGE in line), None
    )
    if skipped is not None:
        raise RedditMediaError(f"ffmpeg left out a piece of the video: {skipped.strip()[-200:]}")


def _mux(
    ffmpeg: str,
    video: str,
    audio: str | None,
    subtitles: list[tuple[str, str | None]],
    output_path: str,
) -> int:
    """
    Put the picture, the sound and the subtitles of a video together. A subtitle that ffmpeg can't
    take is no reason to lose the sound: it is tried again without them
    :param ffmpeg: The path of ffmpeg
    :param video: The file with the picture, or its address
    :param audio: The file with the sound, or its address
    :param subtitles: (the file with the subtitles or its address, the language of them)
    :param output_path: Where to save the video
    :return: How many subtitles the video has
    :raises RedditMediaError: If ffmpeg fails
    """

    try:
        run_ffmpeg(build_ffmpeg_command(ffmpeg, video, audio, subtitles, output_path))
        return len(subtitles)
    except RedditMediaError as e:
        if not subtitles:
            raise
        subtitles_error = e

    # If it fails again it was not because of the subtitles, and it is what is raised
    run_ffmpeg(build_ffmpeg_command(ffmpeg, video, audio, [], output_path))
    logging.warning(f"Reddit video: no subtitles, ffmpeg could not take them ({subtitles_error})")
    return 0


def _remove_quietly(*paths: str | None) -> None:
    """
    Remove files, if they are there
    :param paths: The files
    :return: None
    """

    for path in paths:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass


def _get_size(path: str) -> int:
    """
    Get the size of a file
    :param path: The file
    :return: Its size, in bytes
    """

    return os.path.getsize(path)


# -------------------------------------------------------------------------------------------------
# The ways to get the video
# -------------------------------------------------------------------------------------------------


def _get_video_id(source: RedditVideoSource) -> str | None:
    """
    Get the id of a video of reddit (the one in https://v.redd.it/<id>/...)
    :param source: The video
    :return: The id, None if the video doesn't say it
    """

    for url in (source.fallback_url, source.hls_url, source.dash_url):
        if url and (match := re.match(r"https?://v\.redd\.it/([^/?#]+)", url)):
            return match.group(1)

    return None


def _prepare_with_hls(ffmpeg: str, source: RedditVideoSource, max_bytes: int) -> PreparedVideo:
    """
    Get the video through its playlist (HLS)
    :param ffmpeg: The path of ffmpeg
    :param source: The video
    :param max_bytes: The most bytes that the video may have
    :return: The video
    :raises RedditMediaError: If it can't be done
    :raises RedditMediaUnavailableError: If it is too big in every quality
    """

    playlist_url = source.hls_url
    if not playlist_url and (video_id := _get_video_id(source)):
        playlist_url = f"https://v.redd.it/{video_id}/HLSPlaylist.m3u8"
    if not playlist_url:
        raise RedditMediaError("the video has no playlist")

    playlist_url = add_subtitles_to_playlist_url(playlist_url)
    playlist_path = generate_temp_file_path(".m3u8")
    try:
        # (quiet: if the playlist is not there the files of the video are tried next, and whoever
        # asks says what failed if nothing works)
        fetch_to_file(playlist_url, playlist_path, timeout=DOWNLOAD_TIMEOUT_SECONDS, quiet=True)
        with open(playlist_path, encoding="utf-8", errors="replace") as playlist_file:
            variants = parse_hls_master_playlist(playlist_file.read(), playlist_url)
    finally:
        _remove_quietly(playlist_path)

    if not variants:
        raise RedditMediaError("the playlist has no video in it")

    # The qualities that fit, estimated with the bitrate of them (a playlist may not say it)
    candidates = variants
    if source.duration:
        fitting = [
            variant
            for variant in variants
            if variant.bandwidth == 0 or variant.bandwidth * source.duration / 8 <= max_bytes
        ]
        candidates = fitting or variants[-1:]

    was_too_big = False
    for variant in candidates[:MAX_QUALITIES_TRIED]:
        audio = next(
            (rendition for rendition in variant.audios if rendition.is_default),
            variant.audios[0] if variant.audios else None,
        )
        subtitles = list({rendition.url: rendition for rendition in variant.subtitles}.values())

        output_path = generate_temp_file_path(".mp4")
        try:
            subtitle_count = _mux(
                ffmpeg,
                variant.url,
                audio.url if audio else None,
                [(subtitle.url, subtitle.language) for subtitle in subtitles],
                output_path,
            )
            if _get_size(output_path) <= max_bytes:
                return PreparedVideo(
                    path=output_path,
                    width=variant.width or source.width,
                    height=variant.height or source.height,
                    duration=source.duration,
                    has_audio=audio is not None,
                    subtitle_count=subtitle_count,
                )

            was_too_big = True
            _remove_quietly(output_path)
        except BaseException:
            _remove_quietly(output_path)
            raise

    if was_too_big:
        raise RedditMediaUnavailableError("the video is too big for Telegram, in every quality")
    raise RedditMediaError("no quality of the video could be put together")


def _get_content_length(url: str) -> int | None:
    """
    Ask how big a file is
    :param url: The address of the file
    :return: Its size in bytes, None if the host doesn't say it
    """

    request = urllib.request.Request(url, method="HEAD", headers=get_browser_headers(url))
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            length = response.headers.get("Content-Length")
            return int(length) if length and length.isdigit() else None
    except (urllib.error.URLError, OSError):
        return None


def _download_first_that_exists(urls: list[str], extension: str) -> tuple[str, str] | None:
    """
    Download the first of some files that is there
    :param urls: The addresses of the files
    :param extension: The extension for the file that is saved
    :return: (the path of the file, the address it was downloaded from), None if none is there
    """

    for url in urls:
        path = generate_temp_file_path(extension)
        try:
            # (quiet: most of the files that are asked for are not there, which is how it is known)
            fetch_to_file(url, path, timeout=DOWNLOAD_TIMEOUT_SECONDS, quiet=True)
            return path, url
        except urllib.error.HTTPError as e:
            # Reddit answers 403 (not 404) for a file that the video doesn't have
            if e.code not in GONE_STATUS_CODES:
                raise

    return None


def _prepare_with_dash_files(
    ffmpeg: str, source: RedditVideoSource, max_bytes: int
) -> PreparedVideo:
    """
    Get the video through its files, the one of the picture that the post gives and the ones that
    are next to it (the sound, the captions, the picture in a lower quality)
    :param ffmpeg: The path of ffmpeg
    :param source: The video
    :param max_bytes: The most bytes that the video may have
    :return: The video
    :raises RedditMediaError: If it can't be done
    :raises RedditMediaUnavailableError: If it is too big in every quality
    """

    if not source.fallback_url:
        raise RedditMediaError("the video has no file")

    video_url = source.fallback_url.split("?")[0]
    base_url = video_url.rsplit("/", 1)[0]
    height = source.height or 0

    audio_file = captions_file = None
    video_path = output_path = None
    try:
        audio_file = _download_first_that_exists(
            [f"{base_url}/{name}" for name in AUDIO_FILE_NAMES], ".mp4"
        )
        captions_file = _download_first_that_exists([f"{base_url}/{CAPTIONS_FILE_NAME}"], ".vtt")
        audio_bytes = _get_size(audio_file[0]) if audio_file else 0

        # The picture of the post first, then the ones of lower quality
        lower_urls = [
            f"{base_url}/DASH_{quality}.mp4"
            for quality in DASH_HEIGHTS
            if (height == 0 or quality < height) and f"{base_url}/DASH_{quality}.mp4" != video_url
        ]
        video_urls = [video_url] + lower_urls

        was_too_big = False
        for url in video_urls[: MAX_QUALITIES_TRIED + 1]:
            size = _get_content_length(url)
            if size is not None and size + audio_bytes > max_bytes:
                was_too_big = True
                continue

            video_path = generate_temp_file_path(".mp4")
            try:
                # (quiet: the qualities that the video has are not known, and whoever asks says
                # what failed if nothing works)
                fetch_to_file(url, video_path, timeout=DOWNLOAD_TIMEOUT_SECONDS, quiet=True)
            except urllib.error.HTTPError as e:
                # The video has no file for that quality
                if e.code in GONE_STATUS_CODES:
                    _remove_quietly(video_path)
                    video_path = None
                    continue
                raise

            if _get_size(video_path) + audio_bytes > max_bytes:
                was_too_big = True
                _remove_quietly(video_path)
                video_path = None
                continue

            output_path = generate_temp_file_path(".mp4")
            subtitle_count = _mux(
                ffmpeg,
                video_path,
                audio_file[0] if audio_file else None,
                [(captions_file[0], "en")] if captions_file else [],
                output_path,
            )
            prepared = PreparedVideo(
                path=output_path,
                width=source.width,
                height=source.height,
                duration=source.duration,
                has_audio=audio_file is not None,
                subtitle_count=subtitle_count,
            )
            output_path = None
            return prepared

        if was_too_big:
            raise RedditMediaUnavailableError(
                "the video is too big for Telegram, in every quality"
            )
        raise RedditMediaError("no file of the video could be downloaded")

    finally:
        _remove_quietly(
            audio_file[0] if audio_file else None,
            captions_file[0] if captions_file else None,
            video_path,
            output_path,
        )


def _prepare_video_only(source: RedditVideoSource, max_bytes: int) -> PreparedVideo:
    """
    Get the picture of the video alone, as the bot did before the sound was added to it
    :param source: The video
    :param max_bytes: The most bytes that the video may have
    :return: The video
    :raises RedditMediaError: If the post has no file for the video
    :raises RedditMediaUnavailableError: If it is too big
    """

    if not source.fallback_url:
        raise RedditMediaError("the video has no file")

    path = generate_temp_file_path(".mp4")
    try:
        fetch_to_file(source.fallback_url.split("?")[0], path, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        if _get_size(path) > max_bytes:
            raise RedditMediaUnavailableError("the video is too big for Telegram")
    except urllib.error.HTTPError as e:
        _remove_quietly(path)
        if e.code in GONE_STATUS_CODES:
            raise RedditMediaUnavailableError(f"the video is gone ({e})") from None
        raise
    except BaseException:
        _remove_quietly(path)
        raise

    return PreparedVideo(
        path=path, width=source.width, height=source.height, duration=source.duration
    )


def prepare_reddit_video(
    source: RedditVideoSource, max_bytes: int = MAX_VIDEO_BYTES, with_sound: bool = True
) -> PreparedVideo:
    """
    Get the video of a reddit post as a file that Telegram plays, with its sound and its subtitles.
    It blocks while it downloads, so it has to run in a thread
    :param source: The video
    :param max_bytes: The most bytes that the video may have
    :param with_sound: False for a video that has no sound (reddit makes videos of the GIFs that
    are posted, which are the picture alone): there is nothing to put together then
    :return: The video. It is a temporary file, which whoever asks for it removes
    :raises RedditMediaUnavailableError: If the video is too big for Telegram
    :raises RedditMediaError: If there is no way to get it
    :raises urllib.error.URLError: If reddit can't be reached
    """

    if not with_sound:
        return _prepare_video_only(source, max_bytes)

    ffmpeg = get_ffmpeg_path()
    failures: list[str] = []

    if ffmpeg:
        for way_name, way in (
            ("playlist", _prepare_with_hls),
            ("files", _prepare_with_dash_files),
        ):
            try:
                return way(ffmpeg, source, max_bytes)
            except RedditMediaUnavailableError:
                raise
            except Exception as e:
                failures.append(f"{way_name}: {describe_error(e)}")
    else:
        failures.append("ffmpeg is not installed")

    logging.warning(
        f"Reddit video {_get_video_id(source)} goes without sound and subtitles"
        f" ({'; '.join(failures)})"
    )
    return _prepare_video_only(source, max_bytes)


# -------------------------------------------------------------------------------------------------
# Pictures and GIFs
# -------------------------------------------------------------------------------------------------


def _get_extension(url: str, default: str, allowed: tuple[str, ...]) -> str:
    """
    Get the extension that the file of an address has
    :param url: The address
    :param default: The extension to give if the address has none that is allowed
    :param allowed: The extensions that are allowed
    :return: The extension, with its dot
    """

    extension = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    return extension if extension in allowed else default


def _fit_photo(path: str) -> str:
    """
    Make a photo what Telegram takes: of no more than 10 MB, and not too tall or wide
    :param path: The file of the photo
    :return: The same file if it already is, or the one of a JPEG that is (the first is removed
    then)
    :raises RedditMediaUnavailableError: If it is not a picture, or can't be made small enough
    """

    try:
        with Image.open(path) as image:
            width, height = image.size
            if _get_size(path) <= MAX_PHOTO_BYTES and width + height <= MAX_PHOTO_SIDES_SUM:
                return path

            # A JPEG has no transparency: what there is of it is put on white
            picture = image.convert("RGBA")
            background = Image.new("RGBA", picture.size, (255, 255, 255, 255))
            picture = Image.alpha_composite(background, picture).convert("RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError) as e:
        raise RedditMediaUnavailableError(f"the file is not a picture ({e})") from None

    sides_scale = min(1.0, MAX_PHOTO_SIDES_SUM / (width + height))
    output_path = generate_temp_file_path(".jpg")
    try:
        for scale, quality in PHOTO_SHRINK_STEPS:
            scale *= sides_scale
            size = (max(1, int(width * scale)), max(1, int(height * scale)))
            resized = (
                picture if size == picture.size else picture.resize(size, Image.Resampling.LANCZOS)
            )
            resized.save(output_path, "JPEG", quality=quality, optimize=True)

            if _get_size(output_path) <= MAX_PHOTO_BYTES:
                _remove_quietly(path)
                return output_path
    except BaseException:
        _remove_quietly(output_path)
        raise

    _remove_quietly(output_path)
    raise RedditMediaUnavailableError("the photo is too big for Telegram, even made smaller")


def _download(url: str, path: str, expect_image: bool, what: str) -> None:
    """
    Download a file of reddit
    :param url: The address of the file
    :param path: Where to save it
    :param expect_image: If it has to be a picture (a host that blocks the bot answers with a web
    page)
    :param what: What the file is, for the errors
    :return: None
    :raises RedditMediaUnavailableError: If the file is gone, or is not what it has to be
    :raises urllib.error.URLError: If the file can't be got right now
    """

    try:
        fetch_to_file(url, path, timeout=DOWNLOAD_TIMEOUT_SECONDS, expect_image=expect_image)
    except urllib.error.HTTPError as e:
        _remove_quietly(path)
        if e.code in GONE_STATUS_CODES:
            raise RedditMediaUnavailableError(f"the {what} is gone ({e})") from None
        raise
    except NotAnImageError as e:
        _remove_quietly(path)
        raise RedditMediaUnavailableError(f"the {what} is not a picture ({e})") from None
    except BaseException:
        _remove_quietly(path)
        raise


def download_photo(url: str) -> str:
    """
    Download a photo as a file that Telegram takes as a photo. It blocks while it downloads, so it
    has to run in a thread
    :param url: The address of the photo
    :return: The path of the file. It is a temporary file, which whoever asks for it removes
    :raises RedditMediaUnavailableError: If the photo is gone, or can't be made one for Telegram
    :raises urllib.error.URLError: If the photo can't be got right now
    """

    path = generate_temp_file_path(_get_extension(url, ".jpg", (".jpg", ".jpeg", ".png", ".webp")))
    _download(url, path, True, "photo")

    try:
        return _fit_photo(path)
    except BaseException:
        _remove_quietly(path)
        raise


def download_animation(url: str, max_bytes: int = MAX_VIDEO_BYTES) -> str:
    """
    Download a GIF as a file. It blocks while it downloads, so it has to run in a thread
    :param url: The address of the GIF
    :param max_bytes: The most bytes that it may have
    :return: The path of the file. It is a temporary file, which whoever asks for it removes
    :raises RedditMediaUnavailableError: If the GIF is gone, or too big for Telegram
    :raises urllib.error.URLError: If the GIF can't be got right now
    """

    path = generate_temp_file_path(_get_extension(url, ".gif", (".gif", ".mp4")))
    _download(url, path, False, "GIF")

    if _get_size(path) > max_bytes:
        _remove_quietly(path)
        raise RedditMediaUnavailableError("the GIF is too big for Telegram")

    return path
