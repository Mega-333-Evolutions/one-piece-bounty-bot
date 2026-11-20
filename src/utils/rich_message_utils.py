"""
Rich messages, the messages Telegram added to the Bot API in version 10.1: headings, slideshows of
photos and videos, quotes with an author, buttons between the paragraphs and so on, in one message.
The blocks that are sent here need version 10.2 and the buttons 10.3, so a Bot API server of your
own (TELEGRAM_BOT_API_URL) has to be that new. The one of Telegram, api.telegram.org, is.

Only the Bot API (HTTP) sends them: Telethon, through which the rest of the bot talks to Telegram,
has no way of sending them. So this file builds the blocks of a rich message (the types are
described at https://core.telegram.org/bots/api#inputrichblock) and sends them with
sendRichMessage, failing with the errors (BadRequest, Forbidden, NetworkError...) that the rest of
the bot already knows how to handle.

The bot token is in the address of every request of the Bot API, and the libraries put the address
in the text of their errors. So the token is never kept in a variable that outlives the request,
and whatever an error says about it is removed before the error leaves this file.
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
from typing import NamedTuple

import requests

import resources.Environment as Env
from src.tg_compat.error import (
    BadRequest,
    Forbidden,
    NetworkError,
    RetryAfter,
    TelegramError,
    TimedOut,
)

SEND_RICH_MESSAGE_METHOD = "sendRichMessage"

# urllib3, which sends the requests, writes the address of every one of them to the log at DEBUG
# level ('"POST /bot<token>/sendRichMessage HTTP/1.1" 200'), and the address has the bot token in
# it. With LOG_LEVEL=DEBUG the token would be in the log (and in what is sent to Sentry), so this
# logger is kept from saying it. It still says its warnings, which have no address in them
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

# Seconds to wait to connect to the Bot API, and to wait for it between two pieces of the exchange
# (a video being uploaded takes much longer than that, but it never stands still)
CONNECT_TIMEOUT_SECONDS = 15
READ_TIMEOUT_SECONDS = 300

# The biggest file the Bot API takes from a bot in an upload (50 MB). Photos have a limit of their
# own (10 MB), which Telegram applies by itself
BOT_API_UPLOAD_LIMIT_BYTES = 50 * 1024 * 1024

# What a RichText is: a plain string, a list of RichText, or a dict with a "type" (bold, url...)
RichText = str | list | dict


class RichMessageFile(NamedTuple):
    """A file that goes with a rich message, which refers to it as attach://<name>"""

    name: str
    path: str
    file_name: str | None = None
    content_type: str | None = None


def get_attach_reference(name: str) -> str:
    """
    Get how a block refers to a file that is uploaded with the message
    :param name: The name of the file (RichMessageFile.name)
    :return: The reference
    """

    return f"attach://{name}"


# -------------------------------------------------------------------------------------------------
# Rich text
# -------------------------------------------------------------------------------------------------


def bold(text: RichText) -> dict:
    """Bold text"""
    return {"type": "bold", "text": text}


def italic(text: RichText) -> dict:
    """Italic text"""
    return {"type": "italic", "text": text}


def strikethrough(text: RichText) -> dict:
    """Strikethrough text"""
    return {"type": "strikethrough", "text": text}


def code(text: RichText) -> dict:
    """Monospace text"""
    return {"type": "code", "text": text}


def spoiler(text: RichText) -> dict:
    """Text hidden behind Telegram's own spoiler"""
    return {"type": "spoiler", "text": text}


def superscript(text: RichText) -> dict:
    """Superscript text"""
    return {"type": "superscript", "text": text}


def link(text: RichText, url: str) -> dict:
    """Text that opens a link"""
    return {"type": "url", "text": text, "url": url}


# -------------------------------------------------------------------------------------------------
# Blocks
# -------------------------------------------------------------------------------------------------


def heading_block(text: RichText, size: int = 1) -> dict:
    """
    A heading
    :param text: The text
    :param size: 1 (the biggest, H1) to 6 (the smallest)
    :return: The block
    """

    return {"type": "heading", "text": text, "size": size}


def paragraph_block(text: RichText) -> dict:
    """A paragraph of text"""
    return {"type": "paragraph", "text": text}


def _with_caption(block: dict, caption: RichText | None) -> dict:
    """
    Add the caption to a block of media, if there is one
    :param block: The block
    :param caption: The caption
    :return: The block
    """

    if caption:
        block["caption"] = {"text": caption}
    return block


def photo_block(media: str, has_spoiler: bool = False, caption: RichText | None = None) -> dict:
    """
    A photo
    :param media: The address of the photo (for Telegram to get it), or the reference to a file
    that is uploaded with the message (see get_attach_reference)
    :param has_spoiler: If the photo is covered by the spoiler of Telegram
    :param caption: The caption of the photo
    :return: The block
    """

    photo = {"type": "photo", "media": media}
    if has_spoiler:
        photo["has_spoiler"] = True

    return _with_caption({"type": "photo", "photo": photo}, caption)


def video_block(
    media: str,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    has_spoiler: bool = False,
    caption: RichText | None = None,
) -> dict:
    """
    A video (one that can be watched while it is downloaded)
    :param media: The address of the video, or the reference to a file that is uploaded with the
    message
    :param width: The width of the video
    :param height: The height of the video
    :param duration: The duration of the video, in seconds
    :param has_spoiler: If the video is covered by the spoiler of Telegram
    :param caption: The caption of the video
    :return: The block
    """

    video = {"type": "video", "media": media, "supports_streaming": True}
    if width and height:
        video["width"] = int(width)
        video["height"] = int(height)
    if duration:
        video["duration"] = int(duration)
    if has_spoiler:
        video["has_spoiler"] = True

    return _with_caption({"type": "video", "video": video}, caption)


def animation_block(
    media: str,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    has_spoiler: bool = False,
    caption: RichText | None = None,
) -> dict:
    """
    An animation (a GIF, or a video without sound that plays by itself)
    :param media: The address of the animation, or the reference to a file that is uploaded with
    the message
    :param width: The width of the animation
    :param height: The height of the animation
    :param duration: The duration of the animation, in seconds
    :param has_spoiler: If the animation is covered by the spoiler of Telegram
    :param caption: The caption of the animation
    :return: The block
    """

    animation = {"type": "animation", "media": media}
    if width and height:
        animation["width"] = int(width)
        animation["height"] = int(height)
    if duration:
        animation["duration"] = int(duration)
    if has_spoiler:
        animation["has_spoiler"] = True

    return _with_caption({"type": "animation", "animation": animation}, caption)


def slideshow_block(blocks: list[dict]) -> dict:
    """
    A slideshow: media that is swiped through
    :param blocks: The blocks of media
    :return: The block
    """

    return {"type": "slideshow", "blocks": blocks}


def quote_block(blocks: list[dict], credit: RichText | None = None) -> dict:
    """
    A quote
    :param blocks: The blocks of the quote
    :param credit: The author of the quote
    :return: The block
    """

    block = {"type": "blockquote", "blocks": blocks}
    if credit:
        block["credit"] = credit
    return block


def buttons_block(buttons: list[tuple[str, str]], align: str = "center") -> dict:
    """
    A row of buttons that open a link
    :param buttons: (the text of the button, the link it opens)
    :param align: Where the buttons are: left, center or right
    :return: The block
    """

    return {
        "type": "buttons",
        "buttons": [{"text": text, "url": url} for text, url in buttons],
        "align": align,
    }


# -------------------------------------------------------------------------------------------------
# Sending
# -------------------------------------------------------------------------------------------------


def get_content_type(file_name: str) -> str:
    """
    Get the content type of a file
    :param file_name: The name of the file
    :return: The content type
    """

    return mimetypes.guess_type(file_name)[0] or "application/octet-stream"


def scrub_token(text: str) -> str:
    """
    Remove the bot token from a text
    :param text: The text
    :return: The text without the token
    """

    try:
        token = Env.BOT_TOKEN.get_or_none()
    except (
        Exception
    ):  # Not set: there is no token to remove, and this runs while an error is handled
        token = None

    if token:
        text = text.replace(token, "<bot token>")
    return text


def _call_bot_api(method: str, data: dict, files: list[RichMessageFile] | None) -> dict:
    """
    Call a method of the Bot API
    :param method: The method
    :param data: The parameters of the method (the form fields of the request)
    :param files: The files that are uploaded with the request, if any
    :return: The answer of the Bot API (the "result" of it)
    :raises TimedOut, NetworkError: If Telegram can not be reached or fails
    :raises BadRequest, Forbidden, RetryAfter, TelegramError: If Telegram does not take the request
    """

    opened_files = []
    try:
        form_files = None
        if files:
            form_files = {}
            for file in files:
                opened_file = open(file.path, "rb")
                opened_files.append(opened_file)
                file_name = file.file_name or os.path.basename(file.path)
                form_files[file.name] = (
                    file_name,
                    opened_file,
                    file.content_type or get_content_type(file_name),
                )

        # The address (which has the token) is made here and kept nowhere
        response = requests.post(
            f"{Env.TELEGRAM_BOT_API_URL.get().rstrip('/')}/bot{Env.BOT_TOKEN.get()}/{method}",
            data=data,
            files=form_files,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
        )

    except requests.exceptions.ConnectTimeout:
        # The request never got to Telegram, so nothing was sent: it can be tried again as it is
        raise NetworkError(f"Timed out connecting to the Bot API ({method})") from None
    except requests.exceptions.Timeout:
        # The request got to Telegram, which may have sent the message by now (a video takes a
        # while to be processed): whoever calls this must not send the same message again blindly
        raise TimedOut(f"Timed out calling {method} of the Bot API") from None
    except requests.exceptions.RequestException as e:
        raise NetworkError(
            scrub_token(f"Could not reach the Bot API ({method}): {type(e).__name__}")
        ) from None
    finally:
        for opened_file in opened_files:
            opened_file.close()

    try:
        answer = response.json()
        if not isinstance(answer, dict):
            raise ValueError("not an object")
    except ValueError:
        # Not Telegram's answer: a proxy or a server that is down (e.g. 502 Bad Gateway)
        raise NetworkError(
            f"The Bot API answered {response.status_code} with something that is not JSON"
            f" ({method})"
        ) from None

    if answer.get("ok"):
        return answer.get("result")

    error_code = answer.get("error_code", response.status_code)
    description = scrub_token(str(answer.get("description") or f"Error {error_code}"))
    parameters = answer.get("parameters") or {}

    if error_code == 429:
        raise RetryAfter(parameters.get("retry_after", 1))
    if error_code == 403:
        raise Forbidden(description)
    if error_code in (400, 404):
        # 404 is a Bot API that doesn't know the method (e.g. one older than rich messages)
        raise BadRequest(description)
    if error_code >= 500:
        raise NetworkError(f"Telegram failed ({error_code}): {description}")

    raise TelegramError(f"{error_code}: {description}")


def send_rich_message_blocking(
    chat_id: int | str,
    blocks: list[dict],
    files: list[RichMessageFile] | None = None,
    disable_notification: bool = True,
    message_thread_id: int | None = None,
    reply_to_message_id: int | None = None,
) -> dict:
    """
    Send a rich message. Blocks until it is sent (a video takes a while), so the bot has to call
    send_rich_message instead
    :param chat_id: The chat
    :param blocks: The blocks of the message
    :param files: The files that are uploaded with the message, which the blocks refer to with
    get_attach_reference
    :param disable_notification: If the message is sent without sound
    :param message_thread_id: The topic of the chat, if it is a forum
    :param reply_to_message_id: The message of the chat that it is a reply to. If that message is
    gone (the user deleted it while the post was being got) the message is sent without the reply
    :return: The message that was sent, as the Bot API describes it (with its message_id)
    :raises TimedOut, NetworkError: If Telegram can not be reached or fails
    :raises BadRequest, Forbidden, RetryAfter, TelegramError: If Telegram does not take the message
    """

    data = {
        "chat_id": str(chat_id),
        "rich_message": json.dumps({"blocks": blocks}, ensure_ascii=False, separators=(",", ":")),
    }
    if disable_notification:
        data["disable_notification"] = "true"
    if message_thread_id is not None:
        data["message_thread_id"] = str(message_thread_id)
    if reply_to_message_id is not None:
        data["reply_parameters"] = json.dumps(
            {"message_id": reply_to_message_id, "allow_sending_without_reply": True},
            separators=(",", ":"),
        )

    sent_message = _call_bot_api(SEND_RICH_MESSAGE_METHOD, data, files)
    if not isinstance(sent_message, dict) or "message_id" not in sent_message:
        logging.warning("The Bot API sent a rich message but did not say which message it is")
        return {"message_id": None}

    return sent_message


async def send_rich_message(
    chat_id: int | str,
    blocks: list[dict],
    files: list[RichMessageFile] | None = None,
    disable_notification: bool = True,
    message_thread_id: int | None = None,
    reply_to_message_id: int | None = None,
) -> dict:
    """
    Send a rich message, without making the bot stand still while it is uploaded
    :param chat_id: The chat
    :param blocks: The blocks of the message
    :param files: The files that are uploaded with the message
    :param disable_notification: If the message is sent without sound
    :param message_thread_id: The topic of the chat, if it is a forum
    :param reply_to_message_id: The message of the chat that it is a reply to
    :return: The message that was sent, as the Bot API describes it (with its message_id)
    :raises TimedOut, NetworkError: If Telegram can not be reached or fails
    :raises BadRequest, Forbidden, RetryAfter, TelegramError: If Telegram does not take the message
    """

    return await asyncio.to_thread(
        send_rich_message_blocking,
        chat_id,
        blocks,
        files,
        disable_notification,
        message_thread_id,
        reply_to_message_id,
    )
