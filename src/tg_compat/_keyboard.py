"""
Drop-in replacements for telegram's plain data-container classes: inline
keyboard buttons/markup, input media (used when editing message media), and
inline query result types. None of these talk to Telethon directly - they're
consumed by src/tg_compat/_bot.py, which translates them into Telethon's
``Button`` / ``send_file`` / inline-query-result-builder calls.
"""

import logging

logger = logging.getLogger(__name__)


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
        # api_kwargs={"style": ...} from src/utils/button_style_utils.py -
        # Bot API 9.4 (Feb 2026) added a real `style` field for colored
        # buttons (bg_primary/bg_danger/bg_success). See
        # convert_markup_to_buttons() below for how this gets applied.
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


def _with_style(tl_button, style: str):
    """
    Attach a Bot API 9.4 button color (bg_primary/bg_danger/bg_success) to an
    already-constructed Telethon button object.

    Telethon's Button.* helpers may not (yet) expose `style` as a keyword, so
    this reconstructs the same TL object with the same fields plus `style`
    rather than relying on a helper parameter that might not exist. If the
    installed Telethon version's generated schema doesn't have this field
    yet, construction raises TypeError and the original, unstyled button is
    used instead - colors are a visual nicety, never worth failing a send
    over.
    """
    if not style:
        return tl_button

    flag_by_style = {"success": "bg_success", "danger": "bg_danger", "primary": "bg_primary"}
    flag = flag_by_style.get(style)
    if flag is None:
        return tl_button

    try:
        from telethon.tl.types import KeyboardButtonStyle

        style_obj = KeyboardButtonStyle(**{flag: True})
        field_names = [k for k in vars(tl_button).keys() if not k.startswith("_")]
        kwargs = {k: getattr(tl_button, k) for k in field_names}
        kwargs["style"] = style_obj
        return type(tl_button)(**kwargs)
    except Exception:
        logger.warning(
            f"tg_compat: this Telethon version doesn't support colored buttons "
            f"(Bot API 9.4) yet; sending {tl_button!r} without a style"
        )
        return tl_button


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
                tl_button = Button.url(btn.text, btn.url)
            elif btn.switch_inline_query is not None:
                tl_button = Button.switch_inline(btn.text, btn.switch_inline_query)
            elif btn.switch_inline_query_current_chat is not None:
                tl_button = Button.switch_inline(btn.text, btn.switch_inline_query_current_chat, same_peer=True)
            else:
                data = btn.callback_data
                if isinstance(data, str):
                    data = data.encode("utf-8")
                tl_button = Button.inline(btn.text, data=data)
            style = (btn.extra or {}).get("style")
            new_row.append(_with_style(tl_button, style))
        rows.append(new_row)
    return rows
