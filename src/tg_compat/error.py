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
