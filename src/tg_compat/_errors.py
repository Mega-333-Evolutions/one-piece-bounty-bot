"""
Shared Telethon -> telegram.error translation, used by every compat module
that makes a real Telethon call (Chat.leave, Message.delete, Bot.send_message,
etc), so that every `except BadRequest` / `except Forbidden` / `except
TelegramError` clause throughout the original codebase keeps behaving the
same regardless of which compat method raised it.

Telethon groups its RPC errors into a handful of base classes matching the
Bot-API-ish status categories (see telethon.errors.rpcbaseerrors), which is
what this maps onto telegram.error's hierarchy. A few specific, very common
errors are special-cased first because the original codebase string-matches
on their message text (e.g. "message is not modified").

Exception classes are looked up defensively (getattr with a dummy fallback)
rather than imported by name directly: if a Telethon version ever renames one
of these, the corresponding `except` clause just quietly never matches
instead of raising AttributeError while Python is trying to walk the except
chain - the outer `except Exception` catch-all still guarantees every error
surfaces as *some* telegram.error subclass.
"""

from telethon import errors as tl_errors

from .error import (
    BadRequest,
    Forbidden,
    TimedOut,
    NetworkError,
    RetryAfter,
    TelegramError,
    BOT_BLOCKED_BY_USER_MESSAGE,
    USER_DEACTIVATED_MESSAGE,
    CHAT_NOT_ACCESSIBLE_MESSAGE,
    MESSAGE_TO_EDIT_NOT_FOUND_MESSAGE,
)


class _NeverMatches(Exception):
    """Placeholder used when an expected Telethon error class can't be found."""


def _lookup(name: str):
    return getattr(tl_errors, name, _NeverMatches)


_FloodWaitError = _lookup("FloodWaitError")
_MessageNotModifiedError = _lookup("MessageNotModifiedError")
_MessageIdInvalidError = _lookup("MessageIdInvalidError")
_QueryIdInvalidError = _lookup("QueryIdInvalidError")
_UserNotParticipantError = _lookup("UserNotParticipantError")
_UserIsBlockedError = _lookup("UserIsBlockedError")
_InputUserDeactivatedError = _lookup("InputUserDeactivatedError")
_ChannelPrivateError = _lookup("ChannelPrivateError")
_ForbiddenError = _lookup("ForbiddenError")
_UnauthorizedError = _lookup("UnauthorizedError")
_BadRequestError = _lookup("BadRequestError")
_NotFoundError = _lookup("NotFoundError")


async def translate_errors(coro):
    """Await `coro`, re-raising any Telethon/MTProto error as the matching
    telegram.error type. Pass an *unawaited* coroutine/awaitable in."""
    try:
        return await coro
    except _FloodWaitError as e:
        raise RetryAfter(getattr(e, "seconds", 5)) from e
    except _MessageNotModifiedError as e:
        raise BadRequest("Message is not modified") from e
    except _MessageIdInvalidError as e:
        raise BadRequest(MESSAGE_TO_EDIT_NOT_FOUND_MESSAGE) from e
    except _QueryIdInvalidError as e:
        raise BadRequest(
            "Query is too old and response timeout expired or query id is invalid"
        ) from e
    except _UserNotParticipantError as e:
        raise BadRequest(str(e)) from e
    except _UserIsBlockedError as e:
        # Bot API (and so the python-telegram-bot code this codebase was written against)
        # reports "the user blocked the bot" as a 403 Forbidden, and every
        # `except Forbidden` / `ignore_forbidden_exception=True` that deals with an unreachable
        # user (notification_service.py, the DM sends in game_service.py, broadcast_service.py's
        # _is_permanent_failure, ...) is written for that. MTProto reports the very same
        # condition as a 400 (UserIsBlockedError subclasses BadRequestError), so without this it
        # fell through to the generic BadRequest branch below and slipped past all of them.
        raise Forbidden(BOT_BLOCKED_BY_USER_MESSAGE) from e
    except _InputUserDeactivatedError as e:
        # Same story: Bot API's 403 "user is deactivated" (the account was deleted).
        raise Forbidden(USER_DEACTIVATED_MESSAGE) from e
    except _ChannelPrivateError as e:
        # Bot API reports this one - the bot was kicked/banned from the group, or the chat went
        # private - as a 403 Forbidden too. It is deliberately still a BadRequest here, unlike
        # the two above: existing call sites already depend on it being one (e.g.
        # _types._get_chat_member treats it as "not a member", and several game-end edits of a
        # group message use ignore_bad_request_exception=True), so changing its type could turn
        # a quietly-tolerated situation into a new crash. The fixed text just gives
        # manage_message.py and runtime.py something stable to recognise it by.
        raise BadRequest(f"{CHAT_NOT_ACCESSIBLE_MESSAGE}: {e}") from e
    except _ForbiddenError as e:
        raise Forbidden(str(e)) from e
    except _UnauthorizedError as e:
        raise Forbidden(str(e)) from e
    except _BadRequestError as e:
        raise BadRequest(str(e)) from e
    except _NotFoundError as e:
        raise BadRequest(str(e)) from e
    except (TimeoutError, ConnectionError, OSError) as e:
        raise TimedOut(str(e)) from e
    except TelegramError:
        raise
    except Exception as e:
        raise TelegramError(str(e)) from e
