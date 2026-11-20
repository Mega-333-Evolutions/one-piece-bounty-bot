"""
The text of a reddit post (markdown, as reddit's members write it) as the rich text of a Telegram
rich message: bold, italic, links, lists... and the spoilers of reddit (>!hidden!<), which become
the spoiler of Telegram.

A spoiler must never be shown, whatever happens to the text on the way: a text that is cut short is
cut with its spoilers closed, and a spoiler that goes over a blank line (which reddit wouldn't take
as one) is hidden to its end instead of showing what the author hid.
"""

from __future__ import annotations

import re

import constants as c
from src.utils.rich_message_utils import (
    RichText,
    bold,
    code,
    italic,
    link,
    spoiler,
    strikethrough,
    superscript,
)

SPOILER_OPEN = ">!"
SPOILER_CLOSE = "!<"
ELLIPSIS = "…"

# What reddit puts in the markdown of a post that it doesn't have anymore
REMOVED_TEXTS = ("[removed]", "[deleted]")

# The entities that reddit leaves in the markdown of a post (and the zero width space it uses to
# separate the lines of a gallery). Only these: a text that says &copy is not asking for a (c)
_ENTITIES = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&nbsp;": " ",
    "&#x200B;": "",
    "&#x200b;": "",
    "&#8203;": "",
}
_ENTITY_REGEX = re.compile("|".join(re.escape(entity) for entity in _ENTITIES))

# What a backslash makes a literal character (\* is a star that doesn't start italic)
_ESCAPABLE_CHARACTERS = "\\`*_{}[]()#+-.!>~|^&<"
_ESCAPE_TO_PLACEHOLDER = {
    char: chr(0xE000 + index) for index, char in enumerate(_ESCAPABLE_CHARACTERS)
}
_PLACEHOLDER_TO_ESCAPE = {
    placeholder: char for char, placeholder in _ESCAPE_TO_PLACEHOLDER.items()
}
_ESCAPE_REGEX = re.compile("\\\\([" + re.escape(_ESCAPABLE_CHARACTERS) + "])")
_PLACEHOLDER_REGEX = re.compile("[" + "".join(_PLACEHOLDER_TO_ESCAPE) + "]")

_SPOILER_TOKEN_REGEX = re.compile(re.escape(SPOILER_OPEN) + "|" + re.escape(SPOILER_CLOSE))

_HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BULLET_REGEX = re.compile(r"^(\s*)[-*+•]\s+(.*)$")
_NUMBERED_REGEX = re.compile(r"^(\s*)(\d{1,3})[.)]\s+(.*)$")
# A quote is a > that is not the start of a spoiler (>!)
_QUOTE_REGEX = re.compile(r"^\s*>(?!!)\s?(.*)$")
_RULE_REGEX = re.compile(r"^([-*_])(\s*\1){2,}$")
_TABLE_SEPARATOR_REGEX = re.compile(r"^\|?[\s:|-]+\|?$")

# The ways a text is formatted, in the order that decides which one wins when two start together.
# The ones that start first win anyway
_INLINE_PATTERNS = [
    ("media", re.compile(r"!\[(?:gif|img)\]\([^)\n]*\)")),
    ("spoiler", re.compile(re.escape(SPOILER_OPEN) + r"(.+?)" + re.escape(SPOILER_CLOSE), re.S)),
    (
        "link",
        re.compile(r"\[([^\]\n]+)\]\(\s*<?((?:https?://|/)[^\s)>]+)>?(?:\s+\"[^\"]*\")?\s*\)"),
    ),
    ("code", re.compile(r"`([^`\n]+)`")),
    ("bold", re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", re.S)),
    ("strike", re.compile(r"~~(?=\S)(.+?)(?<=\S)~~", re.S)),
    (
        "italic",
        re.compile(
            r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])"
            r"|(?<![\w_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w_])",
            re.S,
        ),
    ),
    ("reddit_name", re.compile(r"(?<![\w/])/?(u|r)/([A-Za-z0-9_-]{2,21})(?![\w-])")),
    ("superscript", re.compile(r"\^\(([^)\n]+)\)|\^(\w+)")),
]


# -------------------------------------------------------------------------------------------------
# Cleaning, cutting and spoilers
# -------------------------------------------------------------------------------------------------


def clean_reddit_text(text: str | None) -> str:
    """
    Clean the text of a reddit post: line endings, entities, the post that is gone
    :param text: The text
    :return: The text, empty if there is nothing to show
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _ENTITY_REGEX.sub(lambda match: _ENTITIES[match.group(0)], text).strip()

    return "" if text in REMOVED_TEXTS else text


def _is_spoiler_open_after(text: str, is_open: bool = False) -> bool:
    """
    Check if a text leaves a spoiler open (a >! that no !< closes), the way reddit's spoilers are
    read: from the first >! to the next !<
    :param text: The text
    :param is_open: If a spoiler was already open when the text starts
    :return: True if a spoiler is open at the end of the text
    """

    for token in _SPOILER_TOKEN_REGEX.findall(text):
        if token == SPOILER_OPEN:
            is_open = True
        elif is_open:
            is_open = False

    return is_open


def _balance_spoilers(blocks: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Make every block close the spoilers that it opens, and open again the ones that a block before
    it left open. Reddit doesn't take as a spoiler one that goes over a blank line (or over a list
    item), and the text of it would be shown if it was left like that: instead it is all hidden
    :param blocks: The blocks (see _parse_blocks)
    :return: The blocks, in which every one has as many openings of a spoiler as closings
    """

    balanced = []
    is_open = False

    for kind, text in blocks:
        if kind == "code":
            balanced.append((kind, text))
            continue

        block_text = (SPOILER_OPEN if is_open else "") + text
        is_open = _is_spoiler_open_after(text, is_open)
        balanced.append((kind, block_text + (SPOILER_CLOSE if is_open else "")))

    return balanced


def cut_text(text: str, max_length: int | None) -> str:
    """
    Cut a text that is too long, at the end of a paragraph or a sentence if there is one near
    :param text: The text
    :param max_length: The most characters the text may have. None for no limit
    :return: The text, followed by an ellipsis if it was cut. The spoiler it leaves open is closed
    """

    if max_length is None or len(text) <= max_length:
        return text

    cut = text[:max_length]
    for separators, minimum in (
        (("\n\n",), 0.5),
        ((". ", "! ", "? ", ".\n"), 0.6),
        ((" ", "\n"), 0.8),
    ):
        end = max(cut.rfind(separator) + 1 for separator in separators)
        if end >= max_length * minimum:
            cut = cut[:end]
            break

    # Not in the middle of a link: [text](https://exa
    last_bracket = cut.rfind("[")
    if last_bracket != -1 and ")" not in cut[last_bracket:]:
        cut = cut[:last_bracket]

    cut = cut.rstrip()
    if _is_spoiler_open_after(cut):
        cut += SPOILER_CLOSE

    return cut + ELLIPSIS


# -------------------------------------------------------------------------------------------------
# Blocks
# -------------------------------------------------------------------------------------------------


def _parse_blocks(text: str) -> list[tuple[str, str]]:
    """
    Split a text in its blocks (paragraphs, headings, list items, quotes and code)
    :param text: The text
    :return: (the kind of the block, its text). For a list item the text has the mark of the item
    """

    blocks: list[tuple[str, str]] = []
    paragraph: list[str] = []
    is_in_code_fence = False
    # The lines of a quote, or of code, that follow each other are the same block, unless there is
    # a blank line between them
    can_join = False

    def flush_paragraph() -> None:
        nonlocal can_join
        if paragraph:
            blocks.append(("text", "\n".join(paragraph)))
            paragraph.clear()
            can_join = False

    def add_joined(kind: str, line: str) -> None:
        nonlocal can_join
        if can_join and blocks and blocks[-1][0] == kind:
            blocks[-1] = (kind, blocks[-1][1] + "\n" + line)
        else:
            blocks.append((kind, line))
        can_join = True

    for raw_line in text.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()

        if is_in_code_fence:
            if stripped.startswith("```"):
                is_in_code_fence = False
            elif stripped:
                add_joined("code", line)
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            is_in_code_fence = True
            blocks.append(("code_start", ""))
            continue

        if not stripped:
            flush_paragraph()
            can_join = False
            continue

        if _RULE_REGEX.match(stripped):
            flush_paragraph()
            continue

        if match := _HEADING_REGEX.match(stripped):
            flush_paragraph()
            blocks.append(("heading", match.group(2)))
        elif match := _BULLET_REGEX.match(line):
            flush_paragraph()
            mark = "◦ " if len(match.group(1)) >= 2 else "• "
            blocks.append(("item", mark + match.group(2)))
        elif match := _NUMBERED_REGEX.match(line):
            flush_paragraph()
            blocks.append(("item", f"{match.group(2)}. {match.group(3)}"))
        elif match := _QUOTE_REGEX.match(line):
            flush_paragraph()
            add_joined("quote", match.group(1))
        elif stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            if not _TABLE_SEPARATOR_REGEX.match(stripped):
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
                blocks.append(("text", " | ".join(cell for cell in cells if cell)))
        else:
            paragraph.append(stripped)

    flush_paragraph()
    return [block for block in blocks if block[0] != "code_start"]


# -------------------------------------------------------------------------------------------------
# Inline formatting
# -------------------------------------------------------------------------------------------------


def _restore_escapes(rich_text: RichText) -> RichText:
    """
    Turn the characters that stood for an escaped one back into it, in all the text of a rich text
    :param rich_text: The rich text
    :return: The rich text
    """

    if isinstance(rich_text, str):
        return _PLACEHOLDER_REGEX.sub(
            lambda match: _PLACEHOLDER_TO_ESCAPE[match.group(0)], rich_text
        )
    if isinstance(rich_text, list):
        return [_restore_escapes(item) for item in rich_text]

    restored = dict(rich_text)
    restored["text"] = _restore_escapes(rich_text["text"])
    return restored


def _normalize(pieces: list[RichText]) -> RichText:
    """
    Join the pieces of a rich text: the strings that follow each other are one, and the lists in a
    list are part of it
    :param pieces: The pieces
    :return: The rich text: a string if it has no formatting
    """

    flat: list[RichText] = []
    for piece in pieces:
        for item in piece if isinstance(piece, list) else [piece]:
            if isinstance(item, str):
                if not item:
                    continue
                if flat and isinstance(flat[-1], str):
                    flat[-1] += item
                    continue
            flat.append(item)

    if not flat:
        return ""

    return flat[0] if len(flat) == 1 else flat


def _get_reddit_url(url: str) -> str:
    """
    Get the full address of a link of reddit's markdown ([text](/r/onepiece))
    :param url: The address
    :return: The address
    """

    return c.REDDIT_BASE_URL + url if url.startswith("/") else url


def _parse_inline(text: str, allow_links: bool = True) -> RichText:
    """
    Turn the formatting of reddit's markdown in a text into rich text
    :param text: The text
    :param allow_links: If links are made. They are not inside the text of a link
    :return: The rich text
    """

    pieces: list[RichText] = []
    position = 0

    while position < len(text):
        found = None
        for name, pattern in _INLINE_PATTERNS:
            if not allow_links and name in ("link", "reddit_name"):
                continue
            match = pattern.search(text, position)
            if match and (found is None or match.start() < found[1].start()):
                found = (name, match)

        if found is None:
            break

        name, match = found
        pieces.append(text[position : match.start()])
        position = match.end()

        match name:
            case "media":
                continue
            case "spoiler":
                pieces.append(spoiler(_parse_inline(match.group(1), allow_links)))
            case "link":
                pieces.append(
                    link(_parse_inline(match.group(1), False), _get_reddit_url(match.group(2)))
                )
            case "code":
                pieces.append(code(match.group(1)))
            case "bold":
                pieces.append(bold(_parse_inline(match.group(2), allow_links)))
            case "strike":
                pieces.append(strikethrough(_parse_inline(match.group(1), allow_links)))
            case "italic":
                inner = match.group(1) if match.group(1) is not None else match.group(2)
                pieces.append(italic(_parse_inline(inner, allow_links)))
            case "reddit_name":
                kind, name_text = match.group(1), match.group(2)
                pieces.append(
                    link(f"{kind}/{name_text}", f"{c.REDDIT_BASE_URL}/{kind}/{name_text}")
                )
            case "superscript":
                inner = match.group(1) if match.group(1) is not None else match.group(2)
                pieces.append(superscript(inner))

    pieces.append(text[position:])
    return _normalize(pieces)


def _get_block_rich_text(kind: str, text: str, hide_everything: bool) -> RichText:
    """
    Get the rich text of a block
    :param kind: The kind of the block
    :param text: The text of the block
    :param hide_everything: If a spoiler hides everything, so the ones in the text are not needed
    :return: The rich text
    """

    if hide_everything:
        # A spoiler inside a spoiler: the text of it is shown, the one around it hides it
        text = re.sub(
            re.escape(SPOILER_OPEN) + "(.+?)" + re.escape(SPOILER_CLOSE), r"\1", text, flags=re.S
        )

    if kind == "code":
        return code(text)

    rich_text = _parse_inline(
        _ESCAPE_REGEX.sub(lambda m: _ESCAPE_TO_PLACEHOLDER[m.group(1)], text)
    )

    if kind == "heading":
        rich_text = bold(rich_text)
    elif kind == "quote":
        rich_text = italic(rich_text)

    return _restore_escapes(rich_text)


def reddit_markdown_to_paragraphs(
    text: str | None, hide_everything: bool = False, max_length: int | None = None
) -> list[RichText]:
    """
    Turn the text of a reddit post into the paragraphs of a rich message
    :param text: The text, in reddit's markdown
    :param hide_everything: If all of it is hidden by a spoiler (the post is marked as a spoiler)
    :param max_length: The most characters of the text to take. None for all of it
    :return: The rich text of every paragraph (a list item or a heading is one too). Empty if
    the post has no text
    """

    text = clean_reddit_text(text)
    if not text:
        return []

    paragraphs: list[RichText] = []
    for kind, block_text in _balance_spoilers(_parse_blocks(cut_text(text, max_length))):
        rich_text = _get_block_rich_text(kind, block_text, hide_everything)
        if rich_text == "" or rich_text == []:
            continue
        paragraphs.append(spoiler(rich_text) if hide_everything else rich_text)

    return paragraphs
