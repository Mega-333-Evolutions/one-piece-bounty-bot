"""
Drop-in replacements for the ``telegram.error`` exception hierarchy, so that
every ``except BadRequest`` / ``except Forbidden`` / ``except TelegramError``
clause in the original codebase keeps working unchanged.

These are pure Python exception classes - they carry no Telethon-specific
behaviour. All the translation from real Telethon/MTProto errors into these
types happens in ``src/tg_compat/_bot.py``.
"""


class TelegramError(Exception):
    """Base class for all compat Telegram errors (mirrors telegram.error.TelegramError)."""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message


class BadRequest(TelegramError):
    """Mirrors telegram.error.BadRequest (Bot API 'Bad Request' responses)."""


class Forbidden(TelegramError):
    """Mirrors telegram.error.Forbidden (bot was blocked / kicked / lacks rights)."""


class TimedOut(TelegramError):
    """Mirrors telegram.error.TimedOut (request timed out)."""

    def __init__(self, message: str = "Timed out"):
        super().__init__(message)


class NetworkError(TelegramError):
    """Mirrors telegram.error.NetworkError (connection-level failures)."""


class RetryAfter(TelegramError):
    """Mirrors telegram.error.RetryAfter (flood control)."""

    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__(f"Flood control exceeded. Retry in {retry_after} seconds")


class ChatMigrated(TelegramError):
    """Mirrors telegram.error.ChatMigrated (basic group upgraded to supergroup)."""

    def __init__(self, new_chat_id: int):
        self.new_chat_id = new_chat_id
        super().__init__(f"Group migrated to supergroup {new_chat_id}")


class InvalidToken(TelegramError):
    """Mirrors telegram.error.InvalidToken."""


# Texts of the errors that _errors.py raises for "the bot can't (or no longer can) reach this
# user / chat / message". Defined here so the code that recognises them - runtime.py's
# background-task wrapper and chat/manage_message.py - matches on the very same strings that
# are raised, and treats them as expected, non-fatal outcomes rather than as bugs. The first two
# are Bot API's own wording for the same conditions (what python-telegram-bot surfaced
# verbatim).
BOT_BLOCKED_BY_USER_MESSAGE = "bot was blocked by the user"
USER_DEACTIVATED_MESSAGE = "user is deactivated"
CHAT_NOT_ACCESSIBLE_MESSAGE = "Chat is not accessible (bot was kicked/banned, or the chat is private)"
MESSAGE_TO_EDIT_NOT_FOUND_MESSAGE = "Message to edit not found"
# The recipient is itself a bot, and bots can't message each other, so there is nothing to deliver.
# notification_service.py's send_notification_execute recognises "a DM to another bot" by a
# "bot_to_bot" marker in a BadRequest's text and skips that recipient quietly, but MTProto's own
# wording ("Bots can't send messages to other bots") has no such marker - so _errors.py raises this
# text instead: still a BadRequest, with the marker, and still saying what happened. runtime.py
# matches on the marker too.
BOT_TO_BOT_MARKER = "bot_to_bot"
BOT_TO_BOT_MESSAGE = f"Bots can't send messages to other bots ({BOT_TO_BOT_MARKER})"
# The bot has never "encountered" this user in any way MTProto lets it resolve a peer from (no
# message from them, no shared chat, no callback query... - Telegram only hands a bot a user's
# access_hash the first time it sees them), so it simply can't message them. Deliberately worded
# to contain "invalid peer", which notification_service.py and runtime.py already recognise as an
# expected, non-fatal outcome - and NOT any of broadcast_service.py's "permanently gone"
# snippets ("chat not found", "user not found", "user is deactivated", "peer_id_invalid"): this
# says nothing about the account itself, so it must never deactivate the player.
PEER_NOT_RESOLVABLE_MESSAGE = (
    "Invalid peer: the bot has never encountered this user, so it cannot message them"
)
