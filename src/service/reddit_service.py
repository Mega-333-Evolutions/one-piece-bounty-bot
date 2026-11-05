import asyncio
import logging
import os
from typing import AsyncIterator

import asyncpraw
from asyncpraw import Reddit
from asyncpraw.models import Submission, Subreddit
from peewee import DoesNotExist
from src.tg_compat import Message
from src.tg_compat.error import BadRequest, NetworkError, TimedOut
from src.tg_compat.ext import ContextTypes

import constants as c
import resources.Environment as Env
from src.model.RedditGroupPost import RedditGroupPost
from src.model.enums.SavedMedia import SavedMedia
from src.model.enums.SavedMediaType import SavedMediaType
from src.service.message_service import full_media_send, escape_valid_markdown_chars
from src.utils.download_utils import download_temp_file
from src.utils.image_utils import compress_image

# How many posts Telegram may fail to send (it answers with internal errors, or the connection to
# it fails) in one run before the run gives up and waits for the next one. When Telegram is
# having issues the next posts fail the same way, and every failure takes long: Telethon tries
# the request several times, 2 seconds apart
MAX_TELEGRAM_FAILURES_PER_RUN = 2


async def manage(context: ContextTypes.DEFAULT_TYPE, subreddit_name: str) -> None:
    """
    Send a reddit post to the chat group_chat
    :param context: Context of callback
    :param subreddit_name: Name of the subreddit
    """

    main_group_id = Env.MAIN_GROUP_ID.get()
    if main_group_id is None:
        logging.error("Main group ID is not set, can't send reddit post")
        return

    # Create connection using async with to ensure the session closes properly and prevents memory leaks
    async with asyncpraw.Reddit(
        client_id=Env.REDDIT_CLIENT_ID.get(),
        client_secret=Env.REDDIT_CLIENT_SECRET.get(),
        user_agent=Env.REDDIT_USER_AGENT.get(),
    ) as connection:

        # Get first 10 hot posts
        subreddit: Subreddit = await connection.subreddit(subreddit_name)
        hot_posts: AsyncIterator = subreddit.hot(limit=10)

        telegram_failures = 0
        async for post in hot_posts:
            post: Submission = post  # Type hinting

            # Post stickied - skip
            if post.stickied:
                continue

            # Post nsfw - skip
            if post.over_18:
                continue

            # Post already sent - skip
            try:
                RedditGroupPost.get(RedditGroupPost.short_link == post.shortlink)
                continue
            except DoesNotExist:
                pass

            # Caption
            author_name = post.author.name
            author_url = c.REDDIT_USER_URL_PREFIX + post.author.name
            subreddit_url = c.REDDIT_SUBREDDIT_URL_PREFIX + post.subreddit.display_name

            caption = "[{}]({})".format(escape_valid_markdown_chars(post.title), post.shortlink)
            caption += "\n\n"
            caption += "_Posted by [u/{}]({}) on [r/{}]({})_".format(
                escape_valid_markdown_chars(author_name),
                author_url,
                escape_valid_markdown_chars(post.subreddit.display_name),
                subreddit_url,
            )

            # Send in group_chat
            try:
                # Send only media
                if post.url.startswith("https://i.redd.it") or post.url.startswith(
                    "https://v.redd.it"
                ):
                    saved_media: SavedMedia = SavedMedia()
                    if post.url.startswith("https://v.redd.it"):
                        saved_media.type = SavedMediaType.VIDEO
                    elif post.url.endswith(".gif"):
                        saved_media.type = SavedMediaType.ANIMATION
                    else:
                        saved_media.type = SavedMediaType.PHOTO
                    saved_media.media_id = post.url

                    try:
                        # If video, download to local
                        if saved_media.type == SavedMediaType.VIDEO:
                            try:
                                url = post.media["reddit_video"]["fallback_url"]
                                url = url.split("?")[0]
                                with open(download_temp_file(url), "rb") as media_id:
                                    saved_media.media_id = media_id.read()
                            except KeyError:
                                logging.error("Reddit post {} has no video".format(post.shortlink))
                                continue

                        # Send media
                        message: Message = await full_media_send(
                            context, saved_media, caption=caption, chat_id=main_group_id
                        )
                    except (BadRequest, NetworkError, TimedOut) as send_error:
                        # Telegram fetches the picture from reddit by itself, and it may refuse
                        # it (BadRequest) or fail trying (internal errors, timeouts). Either way
                        # the picture is then downloaded here and sent as a file, resized if type
                        # is image
                        if saved_media.type == SavedMediaType.PHOTO:
                            logging.error(
                                "Error sending image {} ({}). Trying to resize it.".format(
                                    post.url, send_error
                                )
                            )

                            # Try resending with a smaller image. Downloaded in a thread, so that
                            # the bot doesn't stand still while reddit is slow
                            image_path = await asyncio.to_thread(
                                compress_image, post.url, c.TG_DEFAULT_IMAGE_COMPRESSION_QUALITY
                            )
                            try:
                                with open(image_path, "rb") as media_id:
                                    saved_media.media_id = media_id.read()
                                message: Message = await full_media_send(
                                    context,
                                    saved_media,
                                    caption=caption,
                                    chat_id=main_group_id,
                                )
                            finally:
                                try:
                                    # Delete the temporary image
                                    os.remove(image_path)
                                except OSError:
                                    # Ignore, will be deleted by auto-cleanup timer
                                    logging.warning(
                                        "Error deleting temporary image {}".format(image_path)
                                    )
                        else:
                            raise

                    # Save post
                    reddit_group_post: RedditGroupPost = RedditGroupPost()
                    reddit_group_post.short_link = post.shortlink
                    reddit_group_post.message_id = message.message_id
                    reddit_group_post.save()

                    # If saved posts > 20, delete all but the last 20
                    if RedditGroupPost.select().count() > 20:
                        last_n_posts = list(
                            RedditGroupPost.select().order_by(RedditGroupPost.id.desc()).limit(20)
                        )
                        (
                            RedditGroupPost.delete()
                            .where(RedditGroupPost.id.not_in([p.id for p in last_n_posts]))
                            .execute()
                        )

                    break
            except BadRequest as bad_request:  # Try again if BadRequest
                logging.error("Error sending reddit post {}: {}".format(post.shortlink, bad_request))
                # Without this, a post that fails for a non-transient reason (e.g. Telegram
                # rejecting the media url/type) gets retried on every single cron run for as
                # long as it stays in the subreddit's top 10 hot posts, spamming the logs with
                # the same error indefinitely. Mark it as seen (no message_id) so it's skipped.
                try:
                    reddit_group_post: RedditGroupPost = RedditGroupPost()
                    reddit_group_post.short_link = post.shortlink
                    reddit_group_post.message_id = None
                    reddit_group_post.save()
                except Exception as save_exception:
                    logging.error(
                        "Error saving skipped reddit post {}: {}".format(
                            post.shortlink, save_exception
                        )
                    )
                continue
            except (NetworkError, TimedOut) as telegram_error:
                # Telegram (or the connection to it) failed, not the post and not the bot: this
                # goes away by itself, so it's no reason to report an error, and the post is not
                # marked as seen, so that it's sent as soon as Telegram is back. Another post is
                # tried (this one may be the problem), unless Telegram keeps failing
                telegram_failures += 1
                logging.warning(
                    "Telegram failed to send reddit post {} ({}/{}): {}".format(
                        post.shortlink,
                        telegram_failures,
                        MAX_TELEGRAM_FAILURES_PER_RUN,
                        telegram_error,
                    )
                )
                if telegram_failures >= MAX_TELEGRAM_FAILURES_PER_RUN:
                    logging.warning("Telegram keeps failing, no more reddit posts in this run")
                    break
                continue
            except Exception as e:  # Stop if any other error
                logging.error("Error sending reddit post {}: {}".format(post.shortlink, e))
                raise e
