"""
Minimal MarkdownV2 (Telegram Bot API flavor) parser.

The original codebase was written against python-telegram-bot and formats all
of its text using Bot API's MarkdownV2 dialect (see ``constants.TG_DEFAULT_PARSE_MODE``
and ``src/utils/string_utils.py``'s ``escape_valid_markdown_chars`` /
``escape_invalid_markdown_chars`` helpers). Telethon ships its own markdown
dialect (``telethon.extensions.markdown``) which uses different escaping
rules, so feeding Bot-API-escaped text into Telethon's own parser would leave
stray backslashes visible to end users.

This module parses the Bot API MarkdownV2 grammar directly into
``(plain_text, [MessageEntity, ...])`` so it can be handed to Telethon's
``formatting_entities`` parameter, bypassing Telethon's own markdown parsing
entirely and preserving the exact rendering the original bot produced.

Supported syntax (https://core.telegram.org/bots/api#markdownv2-style):
    *bold*
    _italic_
    __underline__
    ~strikethrough~
    ||spoiler||
    `inline code`
    ```lang
    pre block
    ```
    [text](http://example.com)      -> text link
    [text](tg://user?id=12345)      -> text mention (by user id)

Any character preceded by ``\\`` is treated as a literal character.
Nesting is supported by recursively parsing the inner text of an entity.
"""

from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntitySpoiler,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
    MessageEntityMentionName,
    MessageEntityBlockquote,
)


def utf16_len(s: str) -> int:
    """Length of a string in UTF-16 code units, which is how Telegram counts
    entity offsets/lengths (surrogate-pair characters count as 2)."""
    if not s:
        return 0
    return len(s.encode("utf-16-le")) // 2


def _normalize_url(url: str) -> str:
    """
    A MessageEntityTextUrl whose url has no recognized scheme (e.g. a
    misconfigured env var storing "t.me/xxx" instead of "https://t.me/xxx")
    risks being silently rejected by Telegram's servers - the rest of the
    message still sends, but that one link renders as plain text with no
    visible error anywhere, which is a hard failure mode to track down.
    tg://... links (used for user mentions, already a recognized scheme) are
    left untouched; anything else with no "scheme://" prefix gets "https://"
    prepended, matching how a browser address bar treats a bare domain.
    """
    if "://" in url or url.startswith("tg:"):
        return url
    return "https://" + url


def _find_unescaped(s: str, start: int, token: str) -> int:
    """Find the first unescaped occurrence of `token` at/after `start`."""
    i = start
    n = len(s)
    tok_len = len(token)
    while i < n:
        if s[i] == "\\":
            i += 2
            continue
        if s[i : i + tok_len] == token:
            return i
        i += 1
    return -1


def parse_markdown_v2(source):
    """
    Parse a MarkdownV2-formatted string into (plain_text, entities).

    :param source: MarkdownV2 formatted text, or None
    :return: tuple of (plain text with markup stripped, list of raw
             telethon.tl.types.MessageEntity* objects with UTF-16 offsets).
             MessageEntityMentionName entities carry a plain int `user_id`;
             the caller is responsible for resolving that into an
             InputMessageEntityMentionName (which needs an InputUser) before
             sending, since resolution requires an async client call.
    """
    if source is None:
        return None, []

    i = 0
    n = len(source)
    out = []
    entities = []

    def cur_offset():
        return utf16_len("".join(out))

    def consume_wrapped(delim, entity_builder, closing=None):
        """
        Parse `delim ... (closing or delim)`, recursing into the inner text.
        Returns True if a full match was consumed (i pointer already advanced),
        False if there was no valid closing delimiter (caller should emit the
        opening character literally and advance by one).
        """
        nonlocal i
        closing = closing or delim
        end = _find_unescaped(source, i + len(delim), closing)
        if end == -1:
            return False
        inner = source[i + len(delim) : end]
        start_off = cur_offset()
        inner_plain, inner_entities = parse_markdown_v2(inner)
        for ch in inner_plain:
            out.append(ch)
        length = cur_offset() - start_off
        for e in inner_entities:
            e.offset += start_off
            entities.append(e)
        built = entity_builder(start_off, length)
        if built is not None:
            entities.append(built)
        i = end + len(closing)
        return True

    while i < n:
        ch = source[i]

        # Escaped character -> literal
        if ch == "\\" and i + 1 < n:
            out.append(source[i + 1])
            i += 2
            continue

        # Blockquote: consecutive lines starting with '>' at the start of a line
        if ch == ">" and (i == 0 or source[i - 1] == "\n"):
            quote_lines = []
            j = i
            while j < n and source[j] == ">":
                j += 1
                line_end = source.find("\n", j)
                if line_end == -1:
                    quote_lines.append(source[j:])
                    j = n
                    break
                quote_lines.append(source[j:line_end])
                if line_end + 1 < n and source[line_end + 1] == ">":
                    j = line_end + 1
                else:
                    j = line_end
                    break

            # This codebase's own convention for an expandable/collapsed
            # quote (see resources/phrases_en.py's surround_with_expandable_quote):
            # every line prefixed with '>', with the visible content ending
            # in '||' as the "make this collapsible" marker. Strip that
            # marker before treating the rest as plain quote content.
            collapsed = False
            if quote_lines and quote_lines[-1].endswith("||"):
                quote_lines[-1] = quote_lines[-1][:-2]
                collapsed = True

            inner_source = "\n".join(quote_lines)
            start_off = cur_offset()
            inner_plain, inner_entities = parse_markdown_v2(inner_source)
            for c in inner_plain:
                out.append(c)
            length = cur_offset() - start_off
            for e in inner_entities:
                e.offset += start_off
                entities.append(e)
            entities.append(MessageEntityBlockquote(offset=start_off, length=length, collapsed=collapsed))
            i = j
            continue

        # Pre-formatted block ```lang\n...``` or ```...```
        if source[i : i + 3] == "```":
            end = source.find("```", i + 3)
            if end == -1:
                out.append(ch)
                i += 1
                continue
            block = source[i + 3 : end]
            lang = ""
            if "\n" in block:
                first_line, rest = block.split("\n", 1)
                if first_line and not any(c.isspace() for c in first_line):
                    lang = first_line
                    block = rest
            start_off = cur_offset()
            for c in block:
                out.append(c)
            length = cur_offset() - start_off
            entities.append(MessageEntityPre(offset=start_off, length=length, language=lang))
            i = end + 3
            continue

        # Inline code `...`
        if ch == "`":
            end = source.find("`", i + 1)
            if end == -1:
                out.append(ch)
                i += 1
                continue
            code_text = source[i + 1 : end]
            start_off = cur_offset()
            for c in code_text:
                out.append(c)
            length = cur_offset() - start_off
            entities.append(MessageEntityCode(offset=start_off, length=length))
            i = end + 1
            continue

        # Links / text mentions [text](url)
        if ch == "[":
            close_bracket = _find_unescaped(source, i + 1, "]")
            if close_bracket != -1 and source[close_bracket + 1 : close_bracket + 2] == "(":
                close_paren = source.find(")", close_bracket + 2)
                if close_paren != -1:
                    link_text = source[i + 1 : close_bracket]
                    url = _normalize_url(source[close_bracket + 2 : close_paren])
                    start_off = cur_offset()
                    inner_plain, inner_entities = parse_markdown_v2(link_text)
                    for c in inner_plain:
                        out.append(c)
                    length = cur_offset() - start_off
                    for e in inner_entities:
                        e.offset += start_off
                        entities.append(e)
                    if url.startswith("tg://user?id="):
                        try:
                            user_id = int(url[len("tg://user?id=") :].split("&")[0])
                            entities.append(
                                MessageEntityMentionName(
                                    offset=start_off, length=length, user_id=user_id
                                )
                            )
                        except ValueError:
                            entities.append(
                                MessageEntityTextUrl(offset=start_off, length=length, url=url)
                            )
                    else:
                        entities.append(
                            MessageEntityTextUrl(offset=start_off, length=length, url=url)
                        )
                    i = close_paren + 1
                    continue
            out.append(ch)
            i += 1
            continue

        # Spoiler ||...||
        if source[i : i + 2] == "||":
            if consume_wrapped(
                "||",
                lambda off, length: MessageEntitySpoiler(offset=off, length=length),
                closing="||",
            ):
                continue
            out.append(ch)
            i += 1
            continue

        # Underline __...__  (must be checked before single-underscore italic)
        if source[i : i + 2] == "__":
            if consume_wrapped(
                "__",
                lambda off, length: MessageEntityUnderline(offset=off, length=length),
                closing="__",
            ):
                continue
            out.append(ch)
            i += 1
            continue

        # Bold *...*
        if ch == "*":
            if consume_wrapped("*", lambda off, length: MessageEntityBold(offset=off, length=length)):
                continue
            out.append(ch)
            i += 1
            continue

        # Strikethrough ~...~
        if ch == "~":
            if consume_wrapped(
                "~", lambda off, length: MessageEntityStrike(offset=off, length=length)
            ):
                continue
            out.append(ch)
            i += 1
            continue

        # Italic _..._
        if ch == "_":
            if consume_wrapped(
                "_", lambda off, length: MessageEntityItalic(offset=off, length=length)
            ):
                continue
            out.append(ch)
            i += 1
            continue

        out.append(ch)
        i += 1

    # Entities get appended to this list in the order the parser resolves
    # them, not necessarily in text order - a link nested inside a
    # blockquote is appended before the blockquote's own entity (since the
    # blockquote's own entity is only known/appended once its full extent,
    # including everything nested inside it, has been parsed), even though
    # the blockquote's offset is numerically earlier. Sort by offset before
    # returning so callers always get a well-ordered list, matching what a
    # server-side entity consumer expects.
    entities.sort(key=lambda e: e.offset)
    return "".join(out), entities
