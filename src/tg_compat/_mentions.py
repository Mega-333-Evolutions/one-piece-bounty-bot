"""
Pre-resolves user mentions before a message is sent, so a mention that can't
be resolved degrades to a plain bold name instead of risking the whole send
failing (or the mention silently rendering as unstyled text with no
indication anything went wrong).

Constructing a working "text mention" (an inline mention of a user by ID,
Telethon's ``MessageEntityMentionName`` - what ``<a href="tg://user?id=X">``
in HTML mode, or ``[name](tg://user?id=X)`` in this codebase's MarkdownV2,
both produce) requires the sending account to know that user's access_hash.
Telegram only ever gives a bot a user's access_hash once that bot has
"encountered" them somehow (a message, a shared chat, a callback query, ...)
- an ID alone is never enough. See:
https://docs.telethon.dev/en/stable/concepts/entities.html

This module checks, for every mention in an outgoing message, whether the
target user is actually resolvable - first via this compat layer's own
access_hash cache (``_types.remember_access_hash``, populated from every
user entity this bot has ever observed, anywhere in the codebase), then by
attempting a live ``get_entity()`` call as a fallback. If neither succeeds,
the mention is rewritten from a link into plain bold text so the person's
name still shows and the rest of the message is unaffected.
"""

import re
import logging

from ._types import get_cached_access_hash, remember_access_hash

logger = logging.getLogger(__name__)


# The "=" is optionally backslash-escaped: message_service.py's
# escape_invalid_markdown_chars runs over the *whole* outgoing message
# (including already-built mentions) before this function ever sees the
# text, and "=" is one of the characters it escapes - so a mention built as
# "[name](tg://user?id=123)" typically arrives here as
# "[name](tg://user?id\=123)". Without tolerating that, this regex simply
# never matched, silently skipping the resolvability check below for every
# mention (not erroring - just never firing), which meant the bold-text
# fallback for unresolvable users wasn't actually reachable.
_MENTION_RE = re.compile(r"\[([^\]]*)\]\(tg://user\?id\\?=(\d+)\)")


async def resolve_mentions(client, text: str) -> str:
    """
    Scans `text` (MarkdownV2) for [name](tg://user?id=X) mentions and
    rewrites any unresolvable ones to plain *bold* text. Returns the
    (possibly modified) text, ready for markdown-to-HTML conversion.
    """
    # Deliberately checks for "tg://user?id" without the trailing "=" - by the
    # time this runs, message_service.py's escape_invalid_markdown_chars has
    # already swept the whole message and may have turned "id=" into "id\=".
    # The regex below handles both forms; this is just the fast-path
    # early-exit, and checking for "=" here would defeat it the same way the
    # regex needed fixing above.
    if text is None or "tg://user?id" not in text:
        return text

    matches = list(_MENTION_RE.finditer(text))
    if not matches:
        return text

    replacements = {}
    for match in matches:
        name, user_id_str = match.group(1), match.group(2)
        user_id = int(user_id_str)
        full_match = match.group(0)
        if full_match in replacements:
            continue

        if get_cached_access_hash(user_id) is not None:
            continue  # known good - leave the mention link as-is

        try:
            entity = await client.get_entity(user_id)
            remember_access_hash(entity)
        except Exception:
            logger.info(
                f"tg_compat: user {user_id} is not resolvable (never encountered by "
                f"this bot session) - sending their name as plain bold text instead "
                f"of a clickable mention"
            )
            replacements[full_match] = f"*{name}*"

    if not replacements:
        return text

    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
