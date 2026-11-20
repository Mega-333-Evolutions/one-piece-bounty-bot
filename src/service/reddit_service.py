"""
The reddit posts that the bot sends to the main group, one at every time of the timers of
Timer.REDDIT_POST_ONE_PIECE and Timer.REDDIT_POST_MEME_PIECE (see the Reddit Post setting in the
features of the main group, which turns them on and off).

The post that is sent is the first one of the hot posts of a subreddit that wasn't sent before. The
subreddit of the timer is the first to be looked at, then the other of the two main ones, and when
none of them has a post that is new, r/OnePiecePowerScaling and r/onepiecetheories (in a random
order, REDDIT_FALLBACK_SUBREDDITS), so that there is a post at the time of the timer.

A post is sent as a rich message (rich_message_utils.py, reddit_post_utils.py): the title, the
media, the description in a quote, #Reddit and a button with the link of the post. It goes through
the Bot API, which is the only one that sends them, and it is tried in these ways, until one of
them works:
1. With the pictures and GIFs by address: Telegram gets them from reddit by itself
2. With every media uploaded: the pictures are downloaded here, made smaller if they are too big
3. As the bot has always sent the posts, with one media and a caption, if the Bot API doesn't take
   a rich message (it is logged as an error, to know that it happened)
The videos are never sent by address: the file of the post has no sound, so they are put together
here with their sound and subtitles (reddit_media_utils.py) and uploaded.

The same setting turns on the posts that people ask for: when someone sends the link of a post of
one of the four subreddits in the main group, the bot gets that post from reddit and sends it, as a
reply to the message with the link, the same way (see manage_message_links).
"""

import asyncio
import logging
import os
import random
import re
from dataclasses import dataclass

import asyncpraw
import asyncprawcore.exceptions as reddit_errors
from asyncpraw.exceptions import AsyncPRAWException, InvalidURL
from asyncpraw.models import Subreddit
from asyncprawcore.exceptions import AsyncPrawcoreException
from peewee import IntegrityError
from src.tg_compat import Update
from src.tg_compat.error import BadRequest, NetworkError, RetryAfter, TelegramError, TimedOut
from src.tg_compat.ext import ContextTypes

import constants as c
import resources.Environment as Env
from src.model.RedditGroupPost import RedditGroupPost
from src.model.enums.Feature import Feature
from src.model.enums.SavedMedia import SavedMedia
from src.model.enums.SavedMediaType import SavedMediaType
from src.service.group_service import main_group_feature_is_enabled
from src.service.message_service import (
    escape_valid_markdown_chars,
    full_media_send,
    full_message_send,
)
from src.utils.reddit_media_utils import (
    MAX_VIDEO_BYTES,
    RedditMediaError,
    RedditMediaUnavailableError,
    download_animation,
    download_photo,
    prepare_reddit_video,
)
from src.utils.reddit_post_utils import (
    ANIMATION,
    PHOTO,
    VIDEO,
    RedditMedia,
    RedditPost,
    RedditPostLink,
    RichMedia,
    build_rich_blocks,
    extract_post,
    find_reddit_post_links,
    get_submission_subreddit_name,
)
from src.utils.rich_message_utils import RichMessageFile, get_attach_reference, send_rich_message

# How many posts Telegram may fail to send (it answers with internal errors, or the connection to
# it fails) in one run before the run gives up and waits for the next one. When Telegram is
# having issues the next posts fail the same way, and every failure takes long: Telethon tries
# the request several times, 2 seconds apart
MAX_TELEGRAM_FAILURES_PER_RUN = 2

# How many of the hot posts of a subreddit are looked at
HOT_POSTS_LIMIT = 10

# How many of the posts that were sent are remembered, not to send them again while they are still
# hot. More than the hot posts of the four subreddits together
REMEMBERED_POSTS = 200

# What the description of a post is cut to if the setting of it is not a number
DEFAULT_MAX_DESCRIPTION_LENGTH = 3000

# The posts that people ask for with a link are got a few at a time (each can be a video that is
# downloaded and put together), and the ones that are asked for while all of them are busy wait
# their turn. When there are this many of them (the ones that are being got and the ones that wait)
# the links that are sent are not looked at until there are fewer: someone who sends links in a row
# can't make the bot do more than that
MAX_LINK_JOBS_AT_ONCE = 2
MAX_LINK_JOBS = 10


class _TransientMediaError(Exception):
    """The media of a post can't be got for now (reddit or the network are failing)"""


@dataclass
class _RunState:
    """What happens in a run, over all the subreddits it looks at"""

    failures: int = 0
    should_stop: bool = False


@dataclass(frozen=True)
class _Destination:
    """Where a post is sent: a chat, and for the posts people ask for, the message it replies to"""

    chat_id: int | str
    reply_to_message_id: int | None = None
    message_thread_id: int | None = None


@dataclass
class _MediaPlan:
    """A media of a post, and its file when there is one (a video, or one that was downloaded)"""

    item: RedditMedia
    path: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    is_dropped: bool = False

    def __post_init__(self):
        self.width = self.item.width
        self.height = self.item.height

    @property
    def is_remote(self) -> bool:
        """If Telegram has to get it from reddit (it is still sent by its address)"""
        return not self.is_dropped and self.path is None


async def manage(context: ContextTypes.DEFAULT_TYPE, subreddit_name: str) -> None:
    """
    Send a reddit post to the main group
    :param context: Context of callback
    :param subreddit_name: Name of the subreddit of the timer
    """

    main_group_id = Env.MAIN_GROUP_ID.get()
    if main_group_id is None:
        logging.error("Main group ID is not set, can't send reddit post")
        return

    # The reddit posts are turned off in the features of the main group
    if not main_group_feature_is_enabled(Feature.REDDIT_POST):
        return

    state = _RunState()
    destination = _Destination(main_group_id)
    first_reddit_error = None

    # Create connection using async with to ensure the session closes properly and prevents memory leaks
    async with asyncpraw.Reddit(
        client_id=Env.REDDIT_CLIENT_ID.get(),
        client_secret=Env.REDDIT_CLIENT_SECRET.get(),
        user_agent=Env.REDDIT_USER_AGENT.get(),
    ) as connection:
        for name in get_subreddit_names(subreddit_name):
            try:
                if await _send_post_of_subreddit(context, connection, name, destination, state):
                    return
            except AsyncPrawcoreException as e:
                # A subreddit that reddit can't give (it is down, or the name is wrong) is no
                # reason not to look at the others
                logging.warning(f"Reddit API error getting the posts of r/{name}: {e}")
                first_reddit_error = first_reddit_error or e

            if state.should_stop:
                return

    # No post was sent because reddit failed (the timer logs it, as it did before)
    if first_reddit_error is not None:
        raise first_reddit_error

    logging.debug("No new reddit post to send")


def _get_subreddit_name(name: str) -> str:
    """
    Get the name of a subreddit as reddit knows it (the setting may say r/name, as people write it)
    :param name: The name
    :return: The name without the r/
    """

    return re.sub(r"^/?r/", "", name.strip(), flags=re.IGNORECASE)


def _get_unique_names(names: list[str]) -> list[str]:
    """
    Get the names of subreddits as reddit knows them, without the ones that are empty or repeated
    :param names: The names, as the settings say them
    :return: The names, in the same order
    """

    unique_names: list[str] = []
    for name in names:
        name = _get_subreddit_name(name)
        if name and name.lower() not in [existing.lower() for existing in unique_names]:
            unique_names.append(name)

    return unique_names


def get_subreddit_names(timer_subreddit_name: str) -> list[str]:
    """
    Get the subreddits that a post is looked for in, in order: the one of the timer, the other main
    one, and the subreddits of the settings that are used when there is no new post in those
    :param timer_subreddit_name: The subreddit of the timer
    :return: The names of the subreddits, without repeating any
    """

    fallback_names = _get_unique_names(Env.REDDIT_FALLBACK_SUBREDDITS.get_list())
    random.shuffle(fallback_names)

    return _get_unique_names(
        [
            timer_subreddit_name,
            Env.REDDIT_ONE_PIECE_SUBREDDIT.get(),
            Env.REDDIT_MEME_PIECE_SUBREDDIT.get(),
            *fallback_names,
        ]
    )


def get_all_subreddit_names() -> list[str]:
    """
    Get the subreddits that the bot uses: the two of its timers and the two that it uses when they
    have no new post (r/onepiece, r/memepiece, r/OnePiecePowerScaling, r/onepiecetheories)
    :return: The names of the subreddits
    """

    return _get_unique_names(
        [
            Env.REDDIT_ONE_PIECE_SUBREDDIT.get(),
            Env.REDDIT_MEME_PIECE_SUBREDDIT.get(),
            *Env.REDDIT_FALLBACK_SUBREDDITS.get_list(),
        ]
    )


def is_subreddit_of_the_bot(subreddit_name: str) -> bool:
    """
    Check if a subreddit is one of the four that the bot uses
    :param subreddit_name: The name of the subreddit
    :return: True if it is
    """

    return _get_subreddit_name(subreddit_name).lower() in [
        name.lower() for name in get_all_subreddit_names()
    ]


def _get_max_description_length() -> int:
    """
    Get the most characters of the description of a post that are sent
    :return: The setting, or the default if it is not a number
    """

    try:
        return Env.REDDIT_POST_MAX_DESCRIPTION_LENGTH.get_int()
    except ValueError:
        logging.error("REDDIT_POST_MAX_DESCRIPTION_LENGTH is not a number, using the default")
        return DEFAULT_MAX_DESCRIPTION_LENGTH


async def _send_post_of_subreddit(
    context: ContextTypes.DEFAULT_TYPE,
    connection: asyncpraw.Reddit,
    subreddit_name: str,
    destination: _Destination,
    state: _RunState,
) -> bool:
    """
    Send the first post of the hot ones of a subreddit that wasn't sent
    :param context: Context of callback
    :param connection: The connection to reddit
    :param subreddit_name: The name of the subreddit
    :param destination: Where to send the post
    :param state: What happened in the run so far
    :return: True if a post was sent
    """

    # Get first hot posts
    subreddit: Subreddit = await connection.subreddit(subreddit_name)
    async for submission in subreddit.hot(limit=HOT_POSTS_LIMIT):
        # Post stickied - skip
        if getattr(submission, "stickied", False):
            continue

        # Post nsfw - skip
        if getattr(submission, "over_18", False):
            continue

        # Post that a moderator or the user took down - skip
        if getattr(submission, "removed_by_category", None):
            continue

        # Post already sent - skip
        if (
            RedditGroupPost.select()
            .where(RedditGroupPost.short_link == submission.shortlink)
            .exists()
        ):
            continue

        if await _send_submission(context, destination, submission, state):
            return True

        if state.should_stop:
            break

    return False


def _count_failure(state: _RunState, short_link: str, who: str, error: Exception) -> None:
    """
    Count a post that failed to be sent for a reason that goes away by itself, which is no reason
    to report an error, and the post is not marked as seen, so that it's sent as soon as it is
    over. Another post is tried (this one may be the problem), unless it keeps failing
    :param state: What happened in the run so far
    :param short_link: The link of the post
    :param who: Who failed (Telegram, reddit)
    :param error: The error
    :return: None
    """

    state.failures += 1
    logging.warning(
        "{} failed to send reddit post {} ({}/{}): {}".format(
            who, short_link, state.failures, MAX_TELEGRAM_FAILURES_PER_RUN, error
        )
    )
    if state.failures >= MAX_TELEGRAM_FAILURES_PER_RUN:
        logging.warning("It keeps failing, no more reddit posts in this run")
        state.should_stop = True


async def _send_submission(
    context: ContextTypes.DEFAULT_TYPE, destination: _Destination, submission, state: _RunState
) -> bool:
    """
    Send a post, and remember it (or the reason that it was not sent, when it is not going away)
    :param context: Context of callback
    :param destination: Where to send the post
    :param submission: The post (a Submission of asyncpraw)
    :param state: What happened in the run so far
    :return: True if the post was sent
    :raises TelegramError: If Telegram does not take messages of the bot (it was removed from the
    group...), which is for whoever runs the bot to see
    """

    short_link = submission.shortlink

    try:
        post = extract_post(submission)
    except Exception as e:
        logging.error(f"Error reading reddit post {short_link}: {e}", exc_info=True)
        _remember_post(short_link, None)
        return False

    try:
        message_id = await _send_post(context, destination, post)
    except BadRequest as bad_request:
        logging.error(f"Error sending reddit post {short_link}: {bad_request}")
        # Without this, a post that fails for a non-transient reason (e.g. Telegram
        # rejecting the media url/type) gets retried on every single cron run for as
        # long as it stays in the subreddit's top hot posts, spamming the logs with
        # the same error indefinitely. Mark it as seen (no message_id) so it's skipped.
        _remember_post(short_link, None)
        return False
    except TimedOut as timed_out:
        # Telegram got the post and didn't answer in time: it may have sent it, and sending it
        # again would repeat it in the group. It is marked as seen
        _count_failure(state, short_link, "Telegram", timed_out)
        _remember_post(short_link, None)
        return False
    except NetworkError as network_error:
        _count_failure(state, short_link, "Telegram", network_error)
        return False
    except _TransientMediaError as media_error:
        _count_failure(state, short_link, "Reddit", media_error)
        return False
    except RetryAfter as retry_after:
        logging.warning(f"Telegram asked to wait to send reddit post {short_link}: {retry_after}")
        state.should_stop = True
        return False
    except TelegramError as telegram_error:  # Stop if Telegram does not take the messages
        logging.error(f"Error sending reddit post {short_link}: {telegram_error}")
        raise
    except Exception as e:
        # Something of the post that the bot didn't expect. The post is skipped, so that it doesn't
        # stop all the ones after it for as long as it is among the hot ones
        logging.error(f"Error sending reddit post {short_link}: {e}", exc_info=True)
        _remember_post(short_link, None)
        return False

    _remember_post(short_link, message_id)
    return True


def _remember_post(short_link: str, message_id: int | None) -> None:
    """
    Remember a post, to not send it again. Only the last posts are remembered
    :param short_link: The link of the post
    :param message_id: The message of the group that has it, None if it was not sent
    :return: None
    """

    try:
        reddit_group_post: RedditGroupPost = RedditGroupPost()
        reddit_group_post.short_link = short_link
        reddit_group_post.message_id = message_id
        reddit_group_post.save()
    except IntegrityError:
        return  # Already remembered
    except Exception as e:
        logging.error(f"Error saving reddit post {short_link}: {e}")
        return

    # If saved posts > REMEMBERED_POSTS, delete all but the last ones
    try:
        if RedditGroupPost.select().count() > REMEMBERED_POSTS:
            last_n_posts = list(
                RedditGroupPost.select()
                .order_by(RedditGroupPost.id.desc())
                .limit(REMEMBERED_POSTS)
            )
            (
                RedditGroupPost.delete()
                .where(RedditGroupPost.id.not_in([p.id for p in last_n_posts]))
                .execute()
            )
    except Exception as e:
        logging.error(f"Error deleting the old reddit posts: {e}")


# -------------------------------------------------------------------------------------------------
# Sending a post
# -------------------------------------------------------------------------------------------------


async def _send_post(
    context: ContextTypes.DEFAULT_TYPE, destination: _Destination, post: RedditPost
) -> int | None:
    """
    Send a post, in the first of the ways (see the top of this file) that works
    :param context: Context of callback
    :param destination: Where to send the post
    :param post: The post
    :return: The id of the message that was sent, None if Telegram didn't say it
    :raises BadRequest: If Telegram doesn't take the post in any way
    :raises TimedOut, NetworkError, RetryAfter, TelegramError: If Telegram fails
    :raises _TransientMediaError: If the media of the post can't be got for now
    """

    plans = [_MediaPlan(item) for item in post.media]
    temp_paths: list[str] = []

    try:
        await _prepare_videos(plans, temp_paths)

        # By address, if there is something that Telegram can get by itself
        if any(plan.is_remote for plan in plans):
            try:
                return await _send_rich_message(destination, post, plans, upload_everything=False)
            except BadRequest as e:
                logging.warning(
                    f"Telegram did not take reddit post {post.short_link} with its media by"
                    f" address ({e}), sending it with the media uploaded"
                )

        await _download_remote_media(plans, temp_paths)
        try:
            return await _send_rich_message(destination, post, plans, upload_everything=True)
        except BadRequest as e:
            logging.error(
                f"Telegram did not take the rich message of reddit post {post.short_link} ({e}),"
                " sending it as the bot did before the rich messages"
            )

        return await _send_legacy_message(context, destination, post, plans)

    finally:
        for temp_path in temp_paths:
            try:
                os.remove(temp_path)
            except OSError:
                # Ignore, will be deleted by auto-cleanup timer
                logging.warning("Error deleting temporary file {}".format(temp_path))


async def _prepare_videos(plans: list[_MediaPlan], temp_paths: list[str]) -> None:
    """
    Put together the videos of a post, with their sound and subtitles. Downloaded in a thread, so
    that the bot doesn't stand still while reddit is slow
    :param plans: The media of the post
    :param temp_paths: The temporary files, to which the ones of the videos are added
    :return: None
    :raises _TransientMediaError: If a video can't be got for now
    """

    for plan in plans:
        if plan.item.video is None:
            continue

        try:
            video = await asyncio.to_thread(
                prepare_reddit_video, plan.item.video, MAX_VIDEO_BYTES, not plan.item.is_silent
            )
        except RedditMediaUnavailableError as e:
            logging.warning(f"Reddit video {plan.item.url} is sent without the video: {e}")
            plan.is_dropped = True
            continue
        except (RedditMediaError, OSError) as e:  # OSError: reddit or the network failed
            raise _TransientMediaError(f"{type(e).__name__}: {e}") from None

        temp_paths.append(video.path)
        plan.path = video.path
        plan.width = video.width or plan.width
        plan.height = video.height or plan.height
        plan.duration = video.duration


async def _download_remote_media(plans: list[_MediaPlan], temp_paths: list[str]) -> None:
    """
    Download the pictures and the GIFs that Telegram would get from reddit by itself, to upload
    them. A picture is made smaller if it is too big. Downloaded in a thread, so that the bot
    doesn't stand still while reddit is slow
    :param plans: The media of the post
    :param temp_paths: The temporary files, to which the ones that are downloaded are added
    :return: None
    :raises _TransientMediaError: If a media can't be got for now
    """

    for plan in plans:
        if not plan.is_remote:
            continue

        download = download_photo if plan.item.kind == PHOTO else download_animation
        try:
            path = await asyncio.to_thread(download, plan.item.url)
        except RedditMediaUnavailableError as e:
            logging.warning(f"Reddit media {plan.item.url} is sent without it: {e}")
            plan.is_dropped = True
            continue
        except (RedditMediaError, OSError) as e:  # OSError: reddit or the network failed
            raise _TransientMediaError(f"{type(e).__name__}: {e}") from None

        temp_paths.append(path)
        plan.path = path


async def _send_rich_message(
    destination: _Destination, post: RedditPost, plans: list[_MediaPlan], upload_everything: bool
) -> int | None:
    """
    Send the rich message of a post
    :param destination: Where to send the post
    :param post: The post
    :param plans: The media of the post, the ones that couldn't be got are left out
    :param upload_everything: If every media that has a file is uploaded, and not only the videos
    (the ones that are not downloaded are sent by their address)
    :return: The id of the message that was sent, None if Telegram didn't say it
    """

    media: list[RichMedia] = []
    files: list[RichMessageFile] = []

    for index, plan in enumerate(plans):
        if plan.is_dropped:
            continue

        reference = plan.item.url
        if plan.path is not None and (upload_everything or plan.item.video is not None):
            name = f"media{index}"
            reference = get_attach_reference(name)
            files.append(
                RichMessageFile(name, plan.path, name + os.path.splitext(plan.path)[1].lower())
            )

        media.append(
            RichMedia(
                kind=plan.item.kind,
                reference=reference,
                caption=plan.item.caption,
                width=plan.width,
                height=plan.height,
                duration=plan.duration,
            )
        )

    blocks = build_rich_blocks(post, media, _get_max_description_length())
    message = await send_rich_message(
        destination.chat_id,
        blocks,
        files or None,
        message_thread_id=destination.message_thread_id,
        reply_to_message_id=destination.reply_to_message_id,
    )
    return message.get("message_id")


def _get_legacy_caption(post: RedditPost) -> str:
    """
    Get the caption that the posts had before the rich messages: the title, with the link of the
    post, and who posted it
    :param post: The post
    :return: The caption
    """

    caption = "[{}]({})".format(
        escape_valid_markdown_chars(post.title), post.short_link or post.url
    )
    caption += "\n\n"

    subreddit = "[r/{}]({})".format(
        escape_valid_markdown_chars(post.subreddit_name),
        c.REDDIT_SUBREDDIT_URL_PREFIX + post.subreddit_name,
    )
    if post.author_name is None:
        return caption + "_Posted on {}_".format(subreddit)

    return caption + "_Posted by [u/{}]({}) on {}_".format(
        escape_valid_markdown_chars(post.author_name),
        c.REDDIT_USER_URL_PREFIX + post.author_name,
        subreddit,
    )


async def _send_legacy_message(
    context: ContextTypes.DEFAULT_TYPE,
    destination: _Destination,
    post: RedditPost,
    plans: list[_MediaPlan],
) -> int | None:
    """
    Send a post as the bot did before the rich messages: the first media of it with a caption. A
    post that is a spoiler is sent without media, which that way can't hide
    :param context: Context of callback
    :param destination: Where to send the post
    :param post: The post
    :param plans: The media of the post
    :return: The id of the message that was sent
    """

    caption = _get_legacy_caption(post)
    plan = next((plan for plan in plans if not plan.is_dropped), None)

    if plan is not None and not post.is_spoiler:
        saved_media: SavedMedia = SavedMedia()
        saved_media.type = {
            PHOTO: SavedMediaType.PHOTO,
            VIDEO: SavedMediaType.VIDEO,
            ANIMATION: SavedMediaType.ANIMATION,
        }[plan.item.kind]
        saved_media.media_id = plan.item.url

        try:
            if plan.path is not None:
                with open(plan.path, "rb") as media_file:
                    saved_media.media_id = media_file.read()

            message = await full_media_send(
                context,
                saved_media,
                caption=caption,
                chat_id=destination.chat_id,
                reply_to_message_id=destination.reply_to_message_id,
            )
            return message.message_id
        except BadRequest as e:
            logging.warning(
                f"Telegram did not take the media of reddit post {post.short_link}: {e}"
            )

    message = await full_message_send(
        context,
        caption,
        chat_id=destination.chat_id,
        reply_to_message_id=destination.reply_to_message_id,
    )
    return getattr(message, "message_id", None)


# -------------------------------------------------------------------------------------------------
# The posts that people ask for with a link
# -------------------------------------------------------------------------------------------------

# The posts that are being got or wait to be (the ones of the links in the messages that are being
# done), so that a post that two people send is not got twice at the same time, and how many jobs
# (one for each message with links) there are. The jobs that run at the same time are limited by a
# semaphore, that is made when it is needed because it belongs to the loop that runs the bot
_pending_links: set[str] = set()
_jobs = 0
_link_semaphore: asyncio.Semaphore | None = None
_link_semaphore_loop: asyncio.AbstractEventLoop | None = None

# What reddit answers when a link doesn't lead to a post that can be got (the post is gone, the
# subreddit is private, the link has a mistake...). It is the fault of the link and not of reddit,
# so nobody has to know about it
_LINK_ERRORS = (
    InvalidURL,
    reddit_errors.NotFound,
    reddit_errors.Forbidden,
    reddit_errors.Redirect,
    reddit_errors.BadRequest,
    reddit_errors.UnavailableForLegalReasons,
)


def _is_link_of_the_bot(link: RedditPostLink) -> bool:
    """
    Check if a link is to a post of one of the subreddits of the bot, as far as the link says (the
    ones that don't say it, like redd.it/<id>, are checked when the post is got)
    :param link: The link
    :return: True if it can be
    """

    return link.subreddit_name is None or is_subreddit_of_the_bot(link.subreddit_name)


def _get_message_urls(message) -> list[str]:
    """
    Get the addresses that a message has behind its words (a link that is made of a text, where the
    address is not written in the message)
    :param message: The message
    :return: The addresses
    """

    entities = getattr(getattr(message, "_tl_message", None), "entities", None) or []
    return [
        url
        for url in (getattr(entity, "url", None) for entity in entities)
        if isinstance(url, str) and url
    ]


def _get_link_semaphore() -> asyncio.Semaphore:
    """
    Get what limits the posts that are got at the same time
    :return: The semaphore
    """

    global _link_semaphore, _link_semaphore_loop

    loop = asyncio.get_running_loop()
    if _link_semaphore is None or _link_semaphore_loop is not loop:
        _link_semaphore = asyncio.Semaphore(MAX_LINK_JOBS_AT_ONCE)
        _link_semaphore_loop = loop

    return _link_semaphore


def _release_links(links: list[RedditPostLink]) -> None:
    """
    Say that a job is over: its posts can be asked for again, and there is room for another job
    :param links: The links of the job
    :return: None
    """

    global _jobs

    _jobs = max(0, _jobs - 1)
    _pending_links.difference_update(link.key for link in links)


def _start_link_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start getting the posts that a message has the links of, if it has any that count
    :param update: The update
    :param context: Context of callback
    :return: None
    """

    global _jobs

    message = update.message
    user = update.effective_user
    if message is None or not message.text or user is None or user.is_bot:
        return

    # A command is a message for the bot, whatever it says
    if message.text.lstrip().startswith("/"):
        return

    # The links are looked for first, which is quick and is the only thing that most of the
    # messages of the group need, and then the settings
    if not Env.ENABLE_REDDIT_POSTS.get_bool():
        return

    links = find_reddit_post_links(message.text, _get_message_urls(message), _is_link_of_the_bot)
    if not links:
        return

    if not main_group_feature_is_enabled(Feature.REDDIT_POST):
        return

    # The posts that are already being got are not asked for again
    links = [link for link in links if link.key not in _pending_links]
    if not links:
        return

    if _jobs >= MAX_LINK_JOBS:
        logging.debug("There are too many reddit posts to get, ignoring the links of a message")
        return

    destination = _Destination(
        chat_id=update.effective_chat.id,
        reply_to_message_id=message.message_id,
        # The topic of the group that the message is in, if it is one (the general topic has none)
        message_thread_id=message.message_thread_id if message.is_topic_message else None,
    )

    _jobs += 1
    _pending_links.update(link.key for link in links)
    try:
        context.application.create_task(
            _post_links(context, destination, links), name="reddit-link-post"
        )
    except Exception:
        _release_links(links)
        raise


async def manage_message_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send the posts of reddit that a message of the main group has the links of. It is called for
    every message of the main group, and does something only if the Reddit Post setting of its
    features is on and the message has the link of a post of one of the four subreddits of the bot:
    the post is got from reddit and sent as a reply to the message. It is done in the background,
    so that whatever the users send next is not held back by a video that is being downloaded
    :param update: The update
    :param context: Context of callback
    :return: None
    """

    try:
        _start_link_job(update, context)
    except Exception as e:  # This is never a reason for what the user sent to not be managed
        logging.error(
            f"Error looking for the links of reddit posts in a message: {e}", exc_info=True
        )


async def _post_links(
    context: ContextTypes.DEFAULT_TYPE, destination: _Destination, links: list[RedditPostLink]
) -> None:
    """
    Get the posts of the links of a message and send them, one after the other
    :param context: Context of callback
    :param destination: Where to send the posts
    :param links: The links
    :return: None
    :raises TelegramError: If Telegram does not take the messages of the bot
    """

    try:
        async with _get_link_semaphore():
            state = _RunState()

            try:
                async with asyncpraw.Reddit(
                    client_id=Env.REDDIT_CLIENT_ID.get(),
                    client_secret=Env.REDDIT_CLIENT_SECRET.get(),
                    user_agent=Env.REDDIT_USER_AGENT.get(),
                ) as connection:
                    for link in links:
                        await _post_link(context, connection, destination, link, state)
                        if state.should_stop:
                            break

            except AsyncPRAWException as e:  # e.g. the credentials of reddit are not set
                logging.error(f"Reddit can't be used to get the posts of links: {e}")

    finally:
        _release_links(links)


async def _post_link(
    context: ContextTypes.DEFAULT_TYPE,
    connection: asyncpraw.Reddit,
    destination: _Destination,
    link: RedditPostLink,
    state: _RunState,
) -> bool:
    """
    Get the post of a link, and send it if it is one that the bot sends: of one of its four
    subreddits, that is not for adults and was not taken down. Whoever asked for it is not told if
    it is not (the link may be anything, and the bot doesn't answer to it)
    :param context: Context of callback
    :param connection: The connection to reddit
    :param destination: Where to send the post
    :param link: The link
    :param state: What happened so far with the links of the message
    :return: True if the post was sent
    """

    try:
        if link.post_id:
            submission = await connection.submission(id=link.post_id)
        else:
            submission = await connection.submission(url=link.share_url)
    except _LINK_ERRORS as e:
        logging.debug(f"The reddit link {link.key} doesn't lead to a post: {type(e).__name__}")
        return False
    except AsyncPrawcoreException as e:
        logging.warning(f"Reddit API error getting the post of the link {link.key}: {e}")
        return False

    subreddit_name = get_submission_subreddit_name(submission)
    if not is_subreddit_of_the_bot(subreddit_name):
        logging.debug(
            f"The reddit post of the link {link.key} is in r/{subreddit_name}, ignoring it"
        )
        return False

    # The same posts that the timers don't send
    if getattr(submission, "over_18", False) or getattr(submission, "removed_by_category", None):
        logging.debug(f"The reddit post of the link {link.key} is not for the group, ignoring it")
        return False

    return await _send_submission(context, destination, submission, state)
