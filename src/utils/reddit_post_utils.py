"""
A post of reddit, as what the bot needs of it (its text, its media, if it is a spoiler...) and as
the blocks of the rich message that is sent for it. Nothing in here goes to the network, so that
all of it can be tried with the data that reddit gives (see reddit_service.py for what is sent, and
when).

The message is, from the top: the title (H1, in bold, with no link), the media (several of them are
a slideshow that is swiped), the description in a quote whose author is the subreddit of the post
(linked to it), #Reddit and a button that opens the post.
"""

from __future__ import annotations

import html
import re
import urllib.parse
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

import constants as c
from src.utils.reddit_markdown_utils import reddit_markdown_to_paragraphs
from src.utils.reddit_media_utils import RedditVideoSource
from src.utils.rich_message_utils import (
    RichText,
    animation_block,
    bold,
    buttons_block,
    heading_block,
    link,
    paragraph_block,
    photo_block,
    quote_block,
    slideshow_block,
    spoiler,
    video_block,
)

# The kinds of media
PHOTO = "photo"
ANIMATION = "animation"
VIDEO = "video"

BUTTON_TEXT = "Reddit post link"
HASHTAG_TEXT = "#Reddit"

# What the author of a post is called when the user is gone
DELETED_AUTHOR = "[deleted]"
# What the title of a post is when it has none (reddit always has one: this is only not to send a
# heading without text, which Telegram would not take)
UNTITLED_POST = "Reddit post"

# Where the images of reddit are, and the ones of imgur, which reddit's members link to as well
IMAGE_HOSTS = ("i.redd.it", "i.imgur.com")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
ANIMATION_EXTENSIONS = (".gif",)

# The extension that the file of an image of a gallery has, by its mime type
GALLERY_MIME_EXTENSIONS = {
    "image/jpg": "jpg",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

# The hosts that are reddit itself, whose links are not the page that a link post shares
REDDIT_HOSTS = ("reddit.com", "redd.it")

MAX_LINK_TEXT_LENGTH = 60
# The most the text of the description is let to be, whatever the setting says: all of the message
# (32,768 characters) has to have room for the rest of it
MAX_DESCRIPTION_LENGTH_LIMIT = 20000

# The most links to posts of a message that are looked at: someone who sends more is not asking for
# the posts one by one, and each of them is a download
MAX_LINKS_PER_MESSAGE = 3

# Where a link to reddit is in a text: with the protocol or without it (Telegram makes a link of
# "reddit.com/r/..." as well), until a space or a bracket. It can't start in the middle of a word,
# a dot, a hyphen or a path, so a site that only ends like reddit (notreddit.com,
# reddit.com.example.org) is not taken for it. Whether it is a link to a post is decided by
# parse_reddit_post_link
LINK_PATTERN = re.compile(
    r"(?<![\w.@/-])(?:https?://)?(?:[a-z0-9-]+\.)*(?:reddit\.com|redd\.it)(?![\w.-])"
    r"(?:/[^\s<>\"'()\[\]]*)?",
    re.IGNORECASE,
)
# What a link has at its end that is not a part of it, but of the sentence it is in
LINK_TRAILING_CHARACTERS = ".,;:!?'\"*>}"

SUBREDDIT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{2,21}$")
POST_ID_PATTERN = re.compile(r"^[a-z0-9]{3,10}$", re.IGNORECASE)
SHARE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{4,32}$")

# The addresses of the posts that reddit hosts. The ones of the apps (/s/) say where the post is
# only when they are opened
SHORT_LINK_HOSTS = ("redd.it", "www.redd.it")


@dataclass
class RedditMedia:
    """A picture, a GIF or a video of a post, as reddit has it"""

    kind: str
    url: str
    caption: str | None = None
    video: RedditVideoSource | None = None
    width: int | None = None
    height: int | None = None
    # A video that has no sound on reddit either (the loops that reddit makes of the GIFs)
    is_silent: bool = False


@dataclass
class RedditPost:
    """A post of reddit"""

    short_link: str
    url: str
    title: str
    author_name: str | None
    subreddit_name: str
    text: str = ""
    is_spoiler: bool = False
    media: list[RedditMedia] = field(default_factory=list)
    # The page that a link post shares (not one of reddit)
    external_url: str | None = None


@dataclass
class RichMedia:
    """A media that goes in the message, and how the message has it (an address, or an upload)"""

    kind: str
    reference: str
    caption: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None


# -------------------------------------------------------------------------------------------------
# What reddit gives
# -------------------------------------------------------------------------------------------------


def _read(source: Any, name: str, default: Any = None) -> Any:
    """
    Read a field of a post. The posts of asyncpraw have no attribute for what reddit doesn't send
    (a post that is not a gallery has no gallery_data), and the original of a crosspost is a dict
    :param source: The post, or a dict of what reddit sent
    :param name: The name of the field
    :param default: What to give if the post doesn't have it (or has nothing in it)
    :return: The value of the field
    """

    if isinstance(source, dict):
        value = source.get(name)
    else:
        value = getattr(source, name, None)

    return default if value is None else value


def _get_int(value: Any) -> int | None:
    """
    Get a number that reddit sent
    :param value: The value
    :return: The number, None if it is not one (or it is zero)
    """

    try:
        number = int(value)
    except (TypeError, ValueError):
        return None

    return number if number > 0 else None


def _get_clean_text(text: Any) -> str | None:
    """
    Get a text that reddit sent (a title, a caption), which has HTML entities in it
    :param text: The text
    :return: The text, None if there is nothing in it
    """

    if not text:
        return None

    return html.unescape(str(text)).strip() or None


def _get_host(url: str) -> str:
    """
    Get the host of an address
    :param url: The address
    :return: The host, in lower case
    """

    return (urllib.parse.urlparse(url).hostname or "").lower()


def _is_reddit_host(host: str) -> bool:
    """
    Check if a host is one of reddit
    :param host: The host
    :return: True if it is
    """

    return any(
        host == reddit_host or host.endswith("." + reddit_host) for reddit_host in REDDIT_HOSTS
    )


def _extract_gallery(source: Any) -> list[RedditMedia]:
    """
    Get the pictures of a gallery (a post with several of them)
    :param source: The post
    :return: The pictures, in the order of the gallery. Empty if the post is not a gallery
    """

    if not _read(source, "is_gallery", False):
        return []

    gallery_data = _read(source, "gallery_data", {})
    metadata = _read(source, "media_metadata", {})
    if not isinstance(gallery_data, dict) or not isinstance(metadata, dict):
        return []

    gallery: list[RedditMedia] = []
    for item in gallery_data.get("items") or []:
        media_id = item.get("media_id") if isinstance(item, dict) else None
        entry = metadata.get(media_id) if media_id else None

        # A picture that reddit took down or didn't process has no file
        if not isinstance(entry, dict) or entry.get("status", "valid") != "valid":
            continue

        kind = entry.get("e")
        size = entry.get("s") if isinstance(entry.get("s"), dict) else {}
        caption = _get_clean_text(item.get("caption"))
        width, height = _get_int(size.get("x")), _get_int(size.get("y"))

        if kind == "AnimatedImage":
            gallery.append(
                RedditMedia(
                    ANIMATION, f"https://i.redd.it/{media_id}.gif", caption, None, width, height
                )
            )
        elif kind == "Image":
            extension = GALLERY_MIME_EXTENSIONS.get(str(entry.get("m", "")).lower(), "jpg")
            media_kind = ANIMATION if extension == "gif" else PHOTO
            gallery.append(
                RedditMedia(
                    media_kind,
                    f"https://i.redd.it/{media_id}.{extension}",
                    caption,
                    None,
                    width,
                    height,
                )
            )

    return gallery


def _extract_video(source: Any) -> RedditMedia | None:
    """
    Get the video that reddit hosts (v.redd.it) in a post
    :param source: The post
    :return: The video, None if the post has none
    """

    reddit_video = None
    for field_name in ("media", "secure_media"):
        media = _read(source, field_name)
        if isinstance(media, dict) and isinstance(media.get("reddit_video"), dict):
            reddit_video = media["reddit_video"]
            break

    if reddit_video is None or not reddit_video.get("fallback_url"):
        return None

    # (the addresses of the API of reddit have &amp; in them when it is asked for the escaped
    # version)
    video_source = RedditVideoSource(
        fallback_url=html.unescape(reddit_video["fallback_url"]),
        hls_url=html.unescape(reddit_video["hls_url"]) if reddit_video.get("hls_url") else None,
        dash_url=html.unescape(reddit_video["dash_url"]) if reddit_video.get("dash_url") else None,
        width=_get_int(reddit_video.get("width")),
        height=_get_int(reddit_video.get("height")),
        duration=_get_int(reddit_video.get("duration")),
    )
    is_silent = bool(reddit_video.get("is_gif"))

    return RedditMedia(
        kind=ANIMATION if is_silent else VIDEO,
        url=video_source.fallback_url,
        video=video_source,
        width=video_source.width,
        height=video_source.height,
        is_silent=is_silent,
    )


def _extract_image(source: Any) -> RedditMedia | None:
    """
    Get the picture or the GIF that a post links to
    :param source: The post
    :return: The picture, None if the post doesn't link to one that is in a host that is trusted
    """

    url = str(_read(source, "url_overridden_by_dest") or _read(source, "url", ""))
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()

    if parsed.scheme not in ("http", "https") or _get_host(url) not in IMAGE_HOSTS:
        return None

    if path.endswith(ANIMATION_EXTENSIONS):
        return RedditMedia(ANIMATION, url)
    if path.endswith(IMAGE_EXTENSIONS):
        return RedditMedia(PHOTO, url)

    return None


def _extract_media(source: Any) -> list[RedditMedia]:
    """
    Get the media of a post
    :param source: The post
    :return: The media, empty if it has none
    """

    gallery = _extract_gallery(source)
    if gallery:
        return gallery

    video = _extract_video(source)
    if video is not None:
        return [video]

    image = _extract_image(source)
    return [image] if image is not None else []


def _extract_external_url(source: Any) -> str | None:
    """
    Get the page that a link post shares
    :param source: The post
    :return: The address, None if the post doesn't share a page that is not one of reddit
    """

    if _read(source, "is_self", False):
        return None

    url = str(_read(source, "url_overridden_by_dest") or _read(source, "url", ""))
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or _is_reddit_host(_get_host(url)):
        return None

    return url


def get_submission_subreddit_name(submission: Any) -> str:
    """
    Get the name of the subreddit that a post is in
    :param submission: The post (a Submission of asyncpraw)
    :return: The name (as reddit writes it), an empty text if the post doesn't say
    """

    subreddit = _read(submission, "subreddit")
    return getattr(subreddit, "display_name", None) or str(subreddit or "")


def extract_post(submission: Any) -> RedditPost:
    """
    Get what the bot needs of a post of reddit
    :param submission: The post (a Submission of asyncpraw)
    :return: The post
    """

    short_link = str(_read(submission, "shortlink", ""))
    permalink = str(_read(submission, "permalink", ""))
    if permalink.startswith("/"):
        permalink = c.REDDIT_BASE_URL + permalink

    # A crosspost has nothing but the title: the rest (the media, the text) is in the original
    parents = _read(submission, "crosspost_parent_list", [])
    parent = parents[0] if parents and isinstance(parents[0], dict) else None
    sources = ([parent] if parent else []) + [submission]

    author = _read(submission, "author")
    author_name = getattr(author, "name", None) or (author if isinstance(author, str) else None)

    subreddit_name = get_submission_subreddit_name(submission)

    media: list[RedditMedia] = []
    for source in sources:
        media = _extract_media(source)
        if media:
            break

    external_url = None
    if not media:
        external_url = next(
            (url for url in (_extract_external_url(source) for source in sources) if url), None
        )

    text = next((_read(source, "selftext") for source in sources if _read(source, "selftext")), "")

    return RedditPost(
        short_link=short_link,
        url=permalink or short_link,
        title=_get_clean_text(_read(submission, "title")) or UNTITLED_POST,
        author_name=None if author_name in (None, "", DELETED_AUTHOR) else author_name,
        subreddit_name=subreddit_name,
        text=text,
        # What a post of reddit says about itself, or what the original of a crosspost says
        is_spoiler=any(bool(_read(source, "spoiler", False)) for source in sources),
        media=media,
        external_url=external_url,
    )


# -------------------------------------------------------------------------------------------------
# The links to posts that people send
# -------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RedditPostLink:
    """
    A link to a post of reddit that someone sent. It is the id of the post, or, in the links that
    the apps of reddit make to share a post (reddit.com/r/<subreddit>/s/<code>), the code that
    reddit turns into the post when the link is opened
    """

    post_id: str | None = None
    share_code: str | None = None
    # The subreddit that the link says the post is in, None if it doesn't say (redd.it/<id>)
    subreddit_name: str | None = None

    @property
    def key(self) -> str:
        """What tells this post from the others (to not get the same one twice)"""
        return f"id:{self.post_id}" if self.post_id else f"s:{self.share_code}"

    @property
    def share_url(self) -> str | None:
        """
        The address that reddit turns into the post, for a link of the apps. It is made here and
        not taken from the message, so that what is asked of reddit is always one of its own pages
        """

        if not self.share_code:
            return None

        subreddit = (
            f"r/{urllib.parse.quote(self.subreddit_name, safe='')}/" if self.subreddit_name else ""
        )
        return f"{c.REDDIT_BASE_URL}/{subreddit}s/{urllib.parse.quote(self.share_code, safe='')}"


def parse_reddit_post_link(text: str) -> RedditPostLink | None:
    """
    Check if an address is the link to a post of reddit (not to a comment of it, a subreddit, a
    user or a media of reddit), and which post it is. These are the ones that are taken:
    reddit.com/r/<subreddit>/comments/<id>[/<title>], reddit.com/comments/<id>,
    reddit.com/gallery/<id>, reddit.com/user/<user>/comments/<id>, redd.it/<id> and the ones of the
    apps, reddit.com/r/<subreddit>/s/<code>, in all the hosts of reddit (www, old, np, m...)
    :param text: The address, with the protocol or without it
    :return: The link, None if it is not the link to a post
    """

    candidate = text.strip().rstrip(LINK_TRAILING_CHARACTERS)
    if not re.match(r"https?://", candidate, re.IGNORECASE):
        candidate = "https://" + candidate

    try:
        parsed = urllib.parse.urlparse(candidate)
        host = (parsed.hostname or "").lower()
    except ValueError:  # e.g. an IPv6 address that is not closed
        return None

    segments = [segment for segment in parsed.path.split("/") if segment]

    if host in SHORT_LINK_HOSTS:
        if len(segments) == 1 and POST_ID_PATTERN.match(segments[0]):
            return RedditPostLink(post_id=segments[0].lower())
        return None

    if host != "reddit.com" and not host.endswith(".reddit.com"):
        return None

    subreddit_name = None
    if len(segments) >= 2 and segments[0].lower() == "r":
        if not SUBREDDIT_NAME_PATTERN.match(segments[1]):
            return None
        subreddit_name, segments = segments[1], segments[2:]
    elif len(segments) >= 2 and segments[0].lower() in ("user", "u"):
        # The posts that someone makes in the page of their user
        # (reddit.com/user/<user>/comments/...)
        segments = segments[2:]

    kind = segments[0].lower() if segments else None

    # reddit.com/.../comments/<id>, with the title of the post after it, and nothing else: one more
    # segment is the id of a comment
    if kind == "comments" and 2 <= len(segments) <= 3 and POST_ID_PATTERN.match(segments[1]):
        return RedditPostLink(post_id=segments[1].lower(), subreddit_name=subreddit_name)

    if kind == "gallery" and len(segments) == 2 and POST_ID_PATTERN.match(segments[1]):
        return RedditPostLink(post_id=segments[1].lower())

    if kind == "s" and len(segments) == 2 and SHARE_CODE_PATTERN.match(segments[1]):
        return RedditPostLink(share_code=segments[1], subreddit_name=subreddit_name)

    return None


def find_reddit_post_links(
    text: str | None,
    urls: Iterable[str] = (),
    is_wanted: Callable[[RedditPostLink], bool] | None = None,
    limit: int = MAX_LINKS_PER_MESSAGE,
) -> list[RedditPostLink]:
    """
    Find the links to posts of reddit that a message has
    :param text: The text of the message (or its caption)
    :param urls: The addresses that the message has behind its words (a link made of text)
    :param is_wanted: Tells which of the links count (the others are as if they weren't in the
    message, and don't use the places of the limit). All of them count if it is not given
    :param limit: The most links that are given
    :return: The links, in the order that they are in the message, with none of them twice
    """

    candidates = [match.group(0) for match in LINK_PATTERN.finditer(text or "")]
    candidates.extend(urls)

    post_links: list[RedditPostLink] = []
    keys: set[str] = set()
    for candidate in candidates:
        post_link = parse_reddit_post_link(candidate)
        if post_link is None or post_link.key in keys:
            continue
        if is_wanted is not None and not is_wanted(post_link):
            continue

        keys.add(post_link.key)
        post_links.append(post_link)
        if len(post_links) >= limit:
            break

    return post_links


# -------------------------------------------------------------------------------------------------
# What is sent
# -------------------------------------------------------------------------------------------------


def _get_media_block(item: RichMedia, has_spoiler: bool) -> dict:
    """
    Get the block of a media
    :param item: The media
    :param has_spoiler: If it is covered by the spoiler of Telegram (and so is its caption)
    :return: The block
    """

    caption: RichText | None = item.caption
    if caption and has_spoiler:
        caption = spoiler(caption)

    if item.kind == VIDEO:
        return video_block(
            item.reference, item.width, item.height, item.duration, has_spoiler, caption
        )
    if item.kind == ANIMATION:
        return animation_block(
            item.reference, item.width, item.height, item.duration, has_spoiler, caption
        )

    return photo_block(item.reference, has_spoiler, caption)


def _get_link_text(url: str) -> str:
    """
    Get how an address is shown as the text of its own link
    :param url: The address
    :return: The address without what makes it long (the protocol, www), cut if it is still long
    """

    text = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    if len(text) > MAX_LINK_TEXT_LENGTH:
        text = text[: MAX_LINK_TEXT_LENGTH - 1] + "…"
    return text


def get_subreddit_link(post: RedditPost) -> RichText:
    """
    Get the subreddit that a post is in, linked to it
    :param post: The post
    :return: r/<name>, with the link of the subreddit in it
    """

    return link(
        f"r/{post.subreddit_name}",
        c.REDDIT_SUBREDDIT_URL_PREFIX + urllib.parse.quote(post.subreddit_name, safe=""),
    )


def get_quote_block(post: RedditPost, max_description_length: int | None) -> dict | None:
    """
    Get the quote with the description of a post, which has the subreddit that it is in as its
    author (linked to it). What the post hides behind a spoiler is hidden behind the one of
    Telegram
    :param post: The post
    :param max_description_length: The most characters of the description that are sent
    :return: The block, None if the post has nothing to quote (Telegram doesn't say that a quote
    with nothing in it is taken)
    """

    if max_description_length is not None:
        max_description_length = max(1, min(max_description_length, MAX_DESCRIPTION_LENGTH_LIMIT))

    blocks = [
        paragraph_block(paragraph)
        for paragraph in reddit_markdown_to_paragraphs(
            post.text, hide_everything=post.is_spoiler, max_length=max_description_length
        )
    ]

    # A post that shares a page has no description: the page is what it has to say
    if post.external_url:
        page = link(_get_link_text(post.external_url), post.external_url)
        blocks.append(paragraph_block(spoiler(page) if post.is_spoiler else page))

    if not blocks:
        return None

    return quote_block(blocks, get_subreddit_link(post))


def build_rich_blocks(
    post: RedditPost, media: list[RichMedia], max_description_length: int | None = None
) -> list[dict]:
    """
    Build the blocks of the rich message of a post
    :param post: The post
    :param media: The media that goes in the message, which can be fewer than the ones of the post
    (the ones that couldn't be got are not in it), or none: a post without media is sent without it
    :param max_description_length: The most characters of the description that are sent
    :return: The blocks, in the order of the message
    """

    blocks = [heading_block(bold(post.title), 1)]

    media_blocks = [_get_media_block(item, post.is_spoiler) for item in media]
    if len(media_blocks) == 1:
        blocks.append(media_blocks[0])
    elif media_blocks:
        blocks.append(slideshow_block(media_blocks))

    # A post without a description has no quote: the subreddit, which is the author of the quote
    # when there is one, is in a line of its own
    quote = get_quote_block(post, max_description_length)
    blocks.append(quote if quote is not None else paragraph_block(get_subreddit_link(post)))
    blocks.append(paragraph_block(HASHTAG_TEXT))
    blocks.append(buttons_block([(BUTTON_TEXT, post.url)], "center"))

    return blocks
