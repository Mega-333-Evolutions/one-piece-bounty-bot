"""
Drop-in replacements for telegram's plain data-container classes: inline
keyboard buttons/markup, input media (used when editing message media), and
inline query result types. None of these talk to Telethon directly - they're
consumed by src/tg_compat/_bot.py, which translates them into Telethon's
``Button`` / ``send_file`` / inline-query-result-builder calls.
"""


class InlineKeyboardButton:
    """Mirrors telegram.InlineKeyboardButton."""

    def __init__(
        self,
        text: str,
        callback_data=None,
        url: str = None,
        switch_inline_query: str = None,
        switch_inline_query_current_chat: str = None,
        **kwargs,
    ):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        # Anything else (e.g. the api_kwargs={"style": ...} cosmetic tagging
        # used by src/utils/button_style_utils.py) is accepted and ignored:
        # Telegram's Bot API has no per-button colour/style field to send it
        # to in the first place, so this was already inert.
        self.extra = kwargs


class InlineKeyboardMarkup:
    """Mirrors telegram.InlineKeyboardMarkup."""

    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard


class InputMedia:
    """Mirrors telegram.InputMedia (base)."""

    def __init__(self, media, caption: str = None, parse_mode: str = None):
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode


class InputMediaPhoto(InputMedia):
    type = "photo"


class InputMediaVideo(InputMedia):
    type = "video"


class InputMediaAnimation(InputMedia):
    type = "animation"


class InputTextMessageContent:
    """Mirrors telegram.InputTextMessageContent."""

    def __init__(self, message_text: str, parse_mode: str = None, disable_web_page_preview: bool = None):
        self.message_text = message_text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview


class InlineQueryResult:
    """Mirrors telegram.InlineQueryResult (base)."""

    def __init__(self, id: str):
        self.id = id


class InlineQueryResultArticle(InlineQueryResult):
    """Mirrors telegram.InlineQueryResultArticle."""

    def __init__(
        self,
        id: str,
        title: str,
        input_message_content: InputTextMessageContent,
        description: str = None,
        reply_markup: InlineKeyboardMarkup = None,
        thumbnail_url: str = None,
    ):
        super().__init__(id)
        self.title = title
        self.input_message_content = input_message_content
        self.description = description
        self.reply_markup = reply_markup
        self.thumbnail_url = thumbnail_url


def convert_markup_to_buttons(reply_markup: InlineKeyboardMarkup):
    """Converts a compat InlineKeyboardMarkup into Telethon's `Button` rows."""
    if reply_markup is None:
        return None
    from telethon import Button

    rows = []
    for row in reply_markup.inline_keyboard:
        new_row = []
        for btn in row:
            if btn.url:
                new_row.append(Button.url(btn.text, btn.url))
            elif btn.switch_inline_query is not None:
                new_row.append(Button.switch_inline(btn.text, btn.switch_inline_query))
            elif btn.switch_inline_query_current_chat is not None:
                new_row.append(
                    Button.switch_inline(btn.text, btn.switch_inline_query_current_chat, same_peer=True)
                )
            else:
                data = btn.callback_data
                if isinstance(data, str):
                    data = data.encode("utf-8")
                new_row.append(Button.inline(btn.text, data=data))
        rows.append(new_row)
    return rows
