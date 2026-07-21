"""
MarkdownV2 (Telegram Bot API flavor) -> HTML converter.

The original codebase was written against python-telegram-bot and formats all
of its text using Bot API's MarkdownV2 dialect (see ``constants.TG_DEFAULT_PARSE_MODE``
and ``src/utils/string_utils.py``'s ``escape_valid_markdown_chars`` /
``escape_invalid_markdown_chars`` helpers).

Earlier versions of this compat layer parsed MarkdownV2 directly into raw
``telethon.tl.types.MessageEntity*`` objects and passed them via
``formatting_entities=``, bypassing Telethon's own parser entirely. That
approach turned out to be too fragile in practice (specific formatting -
plain hyperlinks in particular - silently failed to render, without a
reproducible root cause found through static analysis alone). This module
instead converts Bot-API-flavored MarkdownV2 into the HTML dialect Telethon's
own, battle-tested ``parse_mode='html'`` understands
(``telethon/extensions/html.py``), and lets Telethon do the actual parsing,
entity construction, and (for mentions) access-hash resolution - the same
code path used by every other Telethon-based bot, rather than a hand-rolled
one specific to this project.

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
    [text](tg://user?id=12345)      -> inline mention of a user by id
    >quoted line                    -> blockquote (consecutive '>' lines)
    >quoted line ending in ||       -> expandable/collapsible blockquote
                                        (this codebase's own convention, see
                                        resources/phrases_en.py's
                                        surround_with_expandable_quote)

Any character preceded by ``\\`` is treated as a literal character.
Nesting is supported by recursively converting the inner text of each
construct - since the output is HTML, nesting falls out naturally from
properly nested tags rather than needing manual offset/length bookkeeping.
"""

import html as _html


def _escape(text: str) -> str:
    """HTML-escape literal text so it can't be misread as markup by
    Telethon's HTML parser. Does not escape quotes, since this text never
    ends up inside an HTML attribute."""
    return _html.escape(text, quote=False)


def _normalize_url(url: str) -> str:
    """
    A link whose url has no recognized scheme (e.g. a misconfigured env var
    storing "t.me/xxx" instead of "https://t.me/xxx") risks being silently
    rejected by Telegram's servers - the rest of the message still sends,
    but that one link renders as plain text with no visible error anywhere.
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


def _atomic_span_end(s: str, i: int):
    """
    If a self-contained, opaque construct starts at s[i] - a ```pre``` block,
    a `code` span, or a [text](url) link - return the index right after it
    ends. Otherwise return None, meaning s[i] is just an ordinary character.

    Mirrors the matching branches of _to_html() closely enough to identify
    the same spans, but only measures their extent rather than converting
    them - conversion still happens in the normal course of _to_html() once
    whatever *outer* delimiter search called this has been resolved.
    """
    if s[i : i + 3] == "```":
        end = s.find("```", i + 3)
        return end + 3 if end != -1 else None
    if s[i] == "`":
        end = s.find("`", i + 1)
        return end + 1 if end != -1 else None
    if s[i] == "[":
        close_bracket = _find_unescaped(s, i + 1, "]")
        if close_bracket != -1 and s[close_bracket + 1 : close_bracket + 2] == "(":
            close_paren = _find_unescaped(s, close_bracket + 2, ")")
            if close_paren != -1:
                return close_paren + 1
        return None
    return None


def _find_closing_delim(s: str, start: int, delim: str) -> int:
    """
    Like _find_unescaped, but treats [text](url), `code`, and ```pre```
    spans as opaque - a markdown-special character living inside one of
    those (almost always inside a URL) is never a candidate closing
    delimiter for whatever *outer* span is being closed here, matching how
    a real MarkdownV2 parser treats them.

    Without this, a raw, unescaped underscore inside a URL nested in (for
    example) an italic span reads, to a plain left-to-right scan, exactly
    like that span's own closing "_" - so this codebase's
    "_Posted by [u/{}]({author_url}) on [r/{}]({sub_url})_" pattern
    (reddit_service.py) broke on any Reddit username containing an
    underscore: the italic span closed early, mid-way through the
    username's URL, which truncated the link before its own closing ")" -
    so the link-parsing branch in _to_html() never found one and the whole
    thing fell back to literal, broken-looking [brackets](and parens) in
    the sent message, with the swallowed "_" visibly missing from the
    leaked URL text (Telegram then auto-linkified that leaked plain-text
    URL on its own, which is what made it look like *some* kind of working
    link despite being neither the intended link nor the intended text).
    """
    i = start
    n = len(s)
    dlen = len(delim)
    while i < n:
        if s[i] == "\\":
            i += 2
            continue
        if s[i : i + dlen] == delim:
            return i
        skip_to = _atomic_span_end(s, i)
        if skip_to is not None:
            i = skip_to
            continue
        i += 1
    return -1


def _unescape(text: str) -> str:
    """
    Undo MarkdownV2 backslash-escaping ("\\X" -> "X"), for the few substrings
    that are taken as a raw slice instead of being run back through
    _to_html() - a link's URL, and the contents of `code`/```pre``` blocks.

    Real Bot API MarkdownV2 (what PTB sends to Telegram's own server-side
    parser) unescapes "\\X" to "X" uniformly, wherever it appears in a
    message - including inside a link's URL and inside code/pre text. But
    this codebase's escape_invalid_markdown_chars/escape_valid_markdown_chars
    helpers (src/service/message_service.py) run over whole, already-built
    messages - deeplinks and all - without excluding text that happens to
    sit inside a [text](url), `code`, or ```pre``` construct. So a URL like
    "https://t.me/x" commonly arrives here as "https://t\\.me/x" (the "."
    got escaped along with the rest of the message), and a deeplink's base64
    payload commonly picks up an escaped "\\=" from its padding.

    Without this, those literal backslashes were passed straight through:
    into the href attribute (producing a URL Telegram silently refuses to
    treat as clickable - the message still sends, the link just isn't a
    link) for links, and visibly in the rendered text for code/pre. Bold,
    italic, blockquotes etc. were never affected, since those recurse through
    _to_html() (which already unescapes via the `ch == "\\"` branch below) -
    only these raw-slice cases skipped that step.
    """
    if "\\" not in text:
        return text
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\\" and i + 1 < n:
            out.append(text[i + 1])
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _to_html(source: str) -> str:
    """Recursively convert a MarkdownV2-formatted string into HTML."""
    i = 0
    n = len(source)
    out = []

    def consume_wrapped(delim, tag, closing=None, attrs=""):
        """
        Parse `delim ... (closing or delim)`, recursing into the inner text
        and wrapping the result in `<tag attrs>...</tag>`. Returns True if a
        full match was consumed (i pointer already advanced), False if there
        was no valid closing delimiter (caller should emit the opening
        character literally and advance by one).
        """
        nonlocal i
        closing = closing or delim
        end = _find_closing_delim(source, i + len(delim), closing)
        if end == -1:
            return False
        inner = source[i + len(delim) : end]
        out.append(f"<{tag}{attrs}>")
        out.append(_to_html(inner))
        out.append(f"</{tag}>")
        i = end + len(closing)
        return True

    while i < n:
        ch = source[i]

        # Escaped character -> literal (still needs HTML-escaping, e.g. \< )
        if ch == "\\" and i + 1 < n:
            out.append(_escape(source[i + 1]))
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
            # in '||' as the "make this collapsible" marker.
            expandable = False
            if quote_lines and quote_lines[-1].endswith("||"):
                quote_lines[-1] = quote_lines[-1][:-2]
                expandable = True

            inner_source = "\n".join(quote_lines)
            attrs = " expandable" if expandable else ""
            out.append(f"<blockquote{attrs}>")
            out.append(_to_html(inner_source))
            out.append("</blockquote>")
            i = j
            continue

        # Pre-formatted block ```lang\n...``` or ```...```
        if source[i : i + 3] == "```":
            end = source.find("```", i + 3)
            if end == -1:
                out.append(_escape(ch))
                i += 1
                continue
            block = source[i + 3 : end]
            lang = ""
            if "\n" in block:
                first_line, rest = block.split("\n", 1)
                if first_line and not any(c.isspace() for c in first_line):
                    lang = first_line
                    block = rest
            if lang:
                out.append(f'<pre><code class="language-{_escape(lang)}">')
                out.append(_escape(_unescape(block)))
                out.append("</code></pre>")
            else:
                out.append("<pre>")
                out.append(_escape(_unescape(block)))
                out.append("</pre>")
            i = end + 3
            continue

        # Inline code `...` (contents are literal - no nested formatting/escaping
        # of markdown syntax, only HTML-escaping so the raw text displays as-is)
        if ch == "`":
            end = source.find("`", i + 1)
            if end == -1:
                out.append(_escape(ch))
                i += 1
                continue
            code_text = source[i + 1 : end]
            out.append("<code>")
            out.append(_escape(_unescape(code_text)))
            out.append("</code>")
            i = end + 1
            continue

        # Links / text mentions [text](url)
        if ch == "[":
            close_bracket = _find_unescaped(source, i + 1, "]")
            if close_bracket != -1 and source[close_bracket + 1 : close_bracket + 2] == "(":
                # Bot API's spec requires ')' and '\' inside the (...) part to be
                # escaped, so the closing paren must be found the same escape-aware
                # way as the closing ']' above - a plain .find(")") would stop early
                # on an escaped "\)" inside the URL.
                close_paren = _find_unescaped(source, close_bracket + 2, ")")
                if close_paren != -1:
                    link_text = source[i + 1 : close_bracket]
                    # Unescape first: the raw slice still carries whatever
                    # backslashes message_service.py's escape_invalid_markdown_chars
                    # added when it swept the *whole* message (e.g. "t.me" ->
                    # "t\.me", a deeplink's base64 padding -> "\="). Real Bot API
                    # MarkdownV2 unescapes these before treating the result as a URL,
                    # so this compat layer has to as well - otherwise the href ends
                    # up with a literal backslash in it and Telegram won't render it
                    # as a clickable link.
                    url = _normalize_url(_unescape(source[close_bracket + 2 : close_paren]))
                    out.append(f'<a href="{_html.escape(url, quote=True)}">')
                    out.append(_to_html(link_text))
                    out.append("</a>")
                    i = close_paren + 1
                    continue
            out.append(_escape(ch))
            i += 1
            continue

        # Spoiler ||...||
        if source[i : i + 2] == "||":
            if consume_wrapped("||", "tg-spoiler", closing="||"):
                continue
            out.append(_escape(ch))
            i += 1
            continue

        # Underline __...__  (must be checked before single-underscore italic)
        if source[i : i + 2] == "__":
            if consume_wrapped("__", "u", closing="__"):
                continue
            out.append(_escape(ch))
            i += 1
            continue

        # Bold *...*
        if ch == "*":
            if consume_wrapped("*", "b"):
                continue
            out.append(_escape(ch))
            i += 1
            continue

        # Strikethrough ~...~
        if ch == "~":
            if consume_wrapped("~", "s"):
                continue
            out.append(_escape(ch))
            i += 1
            continue

        # Italic _..._
        if ch == "_":
            if consume_wrapped("_", "i"):
                continue
            out.append(_escape(ch))
            i += 1
            continue

        out.append(_escape(ch))
        i += 1

    return "".join(out)


def markdown_v2_to_html(source):
    """
    Convert a MarkdownV2 (Bot API flavor) formatted string into HTML
    suitable for Telethon's parse_mode='html'.

    :param source: MarkdownV2 formatted text, or None
    :return: HTML string, or None if source is None
    """
    if source is None:
        return None
    return _to_html(source)
