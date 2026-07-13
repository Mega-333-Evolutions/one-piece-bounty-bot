"""
Drop-in replacement for the ``telegram`` package (python-telegram-bot),
backed entirely by Telethon. This is a compatibility shim, not a general
reimplementation of PTB - it exposes exactly the classes this codebase's
288 files import from ``telegram`` / ``telegram.ext`` / ``telegram.error`` /
``telegram.constants`` / ``telegram.helpers``, see MIGRATION_NOTES.md for how
that surface was audited (every ``from telegram...`` import line in the
codebase, and every ``context.bot.*`` / ``update.*`` / ``.effective_*``
attribute access, were enumerated and cross-checked against this package).

Every business-logic file in src/ was mechanically updated to import from
``src.tg_compat`` instead of ``telegram`` - nothing else about those files
changed.
"""

from ._types import (
    Chat,
    TelegramUser as User,
    PhotoSize,
    Video,
    Animation,
    File,
    UserProfilePhotos,
    ChatMember,
    ChatMemberAdministrator,
    MessageOriginUser,
    MessageOriginChat,
    MessageOriginChannel,
    MessageOriginHidden,
    Poll,
    PollOption,
)
from ._message import Message, Update, CallbackQuery, InlineQuery, ForumTopicCreated
from ._keyboard import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaAnimation,
    InputTextMessageContent,
    InlineQueryResult,
    InlineQueryResultArticle,
)
from ._bot import Bot

__all__ = [
    "Chat",
    "User",
    "PhotoSize",
    "Video",
    "Animation",
    "File",
    "UserProfilePhotos",
    "ChatMember",
    "ChatMemberAdministrator",
    "MessageOriginUser",
    "MessageOriginChat",
    "MessageOriginChannel",
    "MessageOriginHidden",
    "Poll",
    "PollOption",
    "Message",
    "Update",
    "CallbackQuery",
    "InlineQuery",
    "ForumTopicCreated",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "InputMedia",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputMediaAnimation",
    "InputTextMessageContent",
    "InlineQueryResult",
    "InlineQueryResultArticle",
    "Bot",
]
