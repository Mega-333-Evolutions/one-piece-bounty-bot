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

from .error import BadRequest, Forbidden, TimedOut, NetworkError, RetryAfter, TelegramError


class _NeverMatches(Exception):
    """Placeholder used when an expected Telethon error class can't be found."""


def _lookup(name: str):
    return getattr(tl_errors, name, _NeverMatches)


_FloodWaitError = _lookup("FloodWaitError")
_MessageNotModifiedError = _lookup("MessageNotModifiedError")
_MessageIdInvalidError = _lookup("MessageIdInvalidError")
_QueryIdInvalidError = _lookup("QueryIdInvalidError")
_UserNotParticipantError = _lookup("UserNotParticipantError")
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
        raise BadRequest("Message to edit not found") from e
    except _QueryIdInvalidError as e:
        raise BadRequest(
            "Query is too old and response timeout expired or query id is invalid"
        ) from e
    except _UserNotParticipantError as e:
        raise BadRequest(str(e)) from e
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
