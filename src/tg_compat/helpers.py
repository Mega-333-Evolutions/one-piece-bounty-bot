"""Drop-in replacement for the (small) subset of ``telegram.helpers`` used by
the original codebase - just ``mention_markdown``, used 95 times across the
codebase to build clickable user mentions."""

import re

_V1_SPECIAL_CHARS = r"_*`["
_V2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"


def escape_markdown(text: str, version: int = 1, entity_type: str = None) -> str:
    """
    Mirrors telegram.helpers.escape_markdown. Escapes markdown special
    characters so arbitrary user-supplied text can be safely embedded in a
    MarkdownV2 (or legacy Markdown) formatted message.
    """
    if version == 1:
        chars_to_escape = _V1_SPECIAL_CHARS
    elif version == 2:
        if entity_type in ("pre", "code"):
            chars_to_escape = "\\`"
        elif entity_type in ("text_link", "text_mention", "custom_emoji"):
            chars_to_escape = "\\)"
        else:
            chars_to_escape = _V2_SPECIAL_CHARS
    else:
        raise ValueError("Markdown version must be either 1 or 2!")

    return re.sub(f"([{re.escape(chars_to_escape)}])", r"\\\1", text)


def mention_markdown(user_id: int, name: str, version: int = 1) -> str:
    """
    Mirrors telegram.helpers.mention_markdown. Builds a MarkdownV2 (or legacy
    Markdown) inline mention of a user by id, e.g. [name](tg://user?id=123).
    """
    escaped_name = escape_markdown(name, version=version)
    return f"[{escaped_name}](tg://user?id={user_id})"
