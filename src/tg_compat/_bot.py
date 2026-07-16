"""
Drop-in replacement for telegram.Bot - this is the object stashed on
context.bot (and returned by Update.get_bot() / Message.get_bot()) throughout
the codebase. Every method here mirrors the exact keyword signature the
original code calls it with (see MIGRATION_NOTES.md for the audit of every
call site), backed entirely by a Telethon TelegramClient.
"""

import logging
import base64
from io import BytesIO

from telethon.tl.types import (
    DocumentAttributeAnimated,
    InputPhoto,
    InputDocument,
    MessageEntityMentionName,
    InputMessageEntityMentionName,
)

from ._errors import translate_errors
from ._markdown import parse_markdown_v2
from ._keyboard import convert_markup_to_buttons
from ._types import (
    is_media_ref,
    decode_media_ref,
    _get_chat_member,
)
from ._message import Message, answer_callback_query as _answer_callback_query

logger = logging.getLogger(__name__)


def _reconstruct_media_reference(decoded: dict):
    file_reference = base64.b64decode(decoded["fr"])
    if decoded["k"] == "photo":
        return InputPhoto(id=decoded["id"], access_hash=decoded["ah"], file_reference=file_reference)
    return InputDocument(id=decoded["id"], access_hash=decoded["ah"], file_reference=file_reference)


class Bot:
    """Mirrors telegram.Bot."""

    def __init__(self, client, bot_user_id: int = None, bot_username: str = None):
        self._client = client
        self.id = bot_user_id
        self.username = bot_username

    # -- text preparation -------------------------------------------------

    async def _prepare_text(self, text, parse_mode):
        if text is None:
            return None, None
        if parse_mode == "MarkdownV2":
            plain, entities = parse_markdown_v2(text)
        else:
            plain, entities = text, []
        if not entities:
            return plain, None
        resolved = []
        for e in entities:
            if isinstance(e, MessageEntityMentionName):
                try:
                    input_user = await self._client.get_input_entity(e.user_id)
                    resolved.append(
                        InputMessageEntityMentionName(offset=e.offset, length=e.length, user_id=input_user)
                    )
                except Exception:
                    logger.warning(
                        f"tg_compat: could not resolve mention entity for user {e.user_id}; "
                        f"sending mention as plain text instead"
                    )
            else:
                resolved.append(e)
        return plain, (resolved or None)

    def _resolve_media_input(self, media_value, default_extension: str = None):
        """bytes -> upload fresh; cached "tgcref1:" reference -> reuse without
        re-uploading; anything else (path/URL) -> pass through as-is."""
        if isinstance(media_value, (bytes, bytearray)):
            bio = BytesIO(media_value)
            # Telethon decides photo-vs-document (and picks a mime type) from
            # the file's *name extension*, not its content - see
            # telethon.utils.is_image(), which literally just checks the
            # extension. A bare BytesIO has no .name, so without this it
            # silently uploads as a generic "unnamed" document instead of a
            # photo/video/animation.
            bio.name = f"upload{default_extension or ''}"
            return bio
        if is_media_ref(media_value):
            return _reconstruct_media_reference(decode_media_ref(media_value))
        return media_value

    @staticmethod
    def _reply_target(reply_to_message_id, message_thread_id):
        return reply_to_message_id if reply_to_message_id is not None else message_thread_id

    # -- messages -----------------------------------------------------------

    async def send_message(
        self,
        chat_id,
        text,
        reply_markup=None,
        disable_web_page_preview=None,
        parse_mode="MarkdownV2",
        disable_notification=None,
        reply_to_message_id=None,
        allow_sending_without_reply=None,
        protect_content=None,
        message_thread_id=None,
        **_ignored,
    ) -> Message:
        plain, entities = await self._prepare_text(text, parse_mode)
        tl_message = await translate_errors(
            self._client.send_message(
                chat_id,
                plain,
                formatting_entities=entities,
                parse_mode=None,
                link_preview=(not disable_web_page_preview) if disable_web_page_preview is not None else True,
                silent=bool(disable_notification),
                reply_to=self._reply_target(reply_to_message_id, message_thread_id),
                buttons=convert_markup_to_buttons(reply_markup),
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def edit_message_text(
        self,
        text,
        chat_id=None,
        message_id=None,
        reply_markup=None,
        parse_mode="MarkdownV2",
        disable_web_page_preview=None,
        **_ignored,
    ) -> Message:
        plain, entities = await self._prepare_text(text, parse_mode)
        tl_message = await translate_errors(
            self._client.edit_message(
                chat_id,
                message_id,
                plain,
                formatting_entities=entities,
                parse_mode=None,
                link_preview=(not disable_web_page_preview) if disable_web_page_preview is not None else True,
                buttons=convert_markup_to_buttons(reply_markup),
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def edit_message_reply_markup(self, chat_id=None, message_id=None, reply_markup=None, **_ignored) -> Message:
        tl_message = await translate_errors(
            self._client.edit_message(chat_id, message_id, buttons=convert_markup_to_buttons(reply_markup))
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def edit_message_caption(
        self, chat_id=None, message_id=None, caption=None, parse_mode="MarkdownV2", reply_markup=None, **_ignored
    ) -> Message:
        plain, entities = await self._prepare_text(caption, parse_mode)
        tl_message = await translate_errors(
            self._client.edit_message(
                chat_id,
                message_id,
                plain,
                formatting_entities=entities,
                parse_mode=None,
                buttons=convert_markup_to_buttons(reply_markup),
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def edit_message_media(self, chat_id=None, message_id=None, media=None, reply_markup=None, **_ignored) -> Message:
        plain, entities = await self._prepare_text(media.caption, media.parse_mode) if media else (None, None)
        ext_by_type = {"photo": ".jpg", "video": ".mp4", "animation": ".mp4"}
        default_extension = ext_by_type.get(getattr(media, "type", None), ".jpg")
        file_input = self._resolve_media_input(media.media, default_extension=default_extension) if media else None
        tl_message = await translate_errors(
            self._client.edit_message(
                chat_id,
                message_id,
                plain,
                file=file_input,
                formatting_entities=entities,
                parse_mode=None,
                buttons=convert_markup_to_buttons(reply_markup),
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def delete_message(self, chat_id, message_id) -> bool:
        await translate_errors(self._client.delete_messages(chat_id, [message_id]))
        return True

    async def copy_message(
        self, chat_id, from_chat_id, message_id, message_thread_id=None, disable_notification=None, **_ignored
    ) -> Message:
        src = await translate_errors(self._client.get_messages(from_chat_id, ids=message_id))
        if src is None:
            from .error import BadRequest

            raise BadRequest("Message to copy not found")
        reply_to = message_thread_id
        if getattr(src, "media", None):
            tl_message = await translate_errors(
                self._client.send_file(
                    chat_id,
                    file=src.media,
                    caption=src.message or None,
                    formatting_entities=list(src.entities) if src.entities else None,
                    parse_mode=None,
                    silent=bool(disable_notification),
                    reply_to=reply_to,
                )
            )
        else:
            tl_message = await translate_errors(
                self._client.send_message(
                    chat_id,
                    src.message or "",
                    formatting_entities=list(src.entities) if src.entities else None,
                    parse_mode=None,
                    silent=bool(disable_notification),
                    reply_to=reply_to,
                )
            )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def pin_chat_message(self, chat_id, message_id, disable_notification=None, **_ignored):
        await translate_errors(
            self._client.pin_message(chat_id, message_id, notify=not disable_notification)
        )
        return True

    async def unpin_chat_message(self, chat_id, message_id=None, **_ignored):
        await translate_errors(self._client.unpin_message(chat_id, message_id))
        return True

    # -- media --------------------------------------------------------------

    async def send_photo(
        self,
        chat_id,
        photo,
        caption=None,
        reply_markup=None,
        parse_mode="MarkdownV2",
        disable_notification=None,
        reply_to_message_id=None,
        allow_sending_without_reply=None,
        protect_content=None,
        message_thread_id=None,
        **_ignored,
    ) -> Message:
        plain, entities = await self._prepare_text(caption, parse_mode)
        tl_message = await translate_errors(
            self._client.send_file(
                chat_id,
                file=self._resolve_media_input(photo, default_extension=".jpg"),
                caption=plain,
                formatting_entities=entities,
                parse_mode=None,
                buttons=convert_markup_to_buttons(reply_markup),
                silent=bool(disable_notification),
                reply_to=self._reply_target(reply_to_message_id, message_thread_id),
                force_document=False,
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def send_video(
        self,
        chat_id,
        video,
        caption=None,
        reply_markup=None,
        parse_mode="MarkdownV2",
        disable_notification=None,
        reply_to_message_id=None,
        allow_sending_without_reply=None,
        protect_content=None,
        message_thread_id=None,
        **_ignored,
    ) -> Message:
        plain, entities = await self._prepare_text(caption, parse_mode)
        tl_message = await translate_errors(
            self._client.send_file(
                chat_id,
                file=self._resolve_media_input(video, default_extension=".mp4"),
                caption=plain,
                formatting_entities=entities,
                parse_mode=None,
                buttons=convert_markup_to_buttons(reply_markup),
                silent=bool(disable_notification),
                reply_to=self._reply_target(reply_to_message_id, message_thread_id),
                force_document=False,
                supports_streaming=True,
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    async def send_animation(
        self,
        chat_id,
        animation,
        caption=None,
        reply_markup=None,
        parse_mode="MarkdownV2",
        disable_notification=None,
        reply_to_message_id=None,
        allow_sending_without_reply=None,
        protect_content=None,
        message_thread_id=None,
        **_ignored,
    ) -> Message:
        plain, entities = await self._prepare_text(caption, parse_mode)
        is_fresh_upload = isinstance(animation, (bytes, bytearray))
        tl_message = await translate_errors(
            self._client.send_file(
                chat_id,
                file=self._resolve_media_input(animation, default_extension=".mp4"),
                caption=plain,
                formatting_entities=entities,
                parse_mode=None,
                buttons=convert_markup_to_buttons(reply_markup),
                silent=bool(disable_notification),
                reply_to=self._reply_target(reply_to_message_id, message_thread_id),
                force_document=False,
                attributes=[DocumentAttributeAnimated()] if is_fresh_upload else None,
            )
        )
        return await Message.from_telethon(tl_message, self._client, self, fetch_reply=False)

    # -- callback queries -----------------------------------------------------

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=None, **_ignored) -> bool:
        await _answer_callback_query(self._client, callback_query_id, text=text, show_alert=bool(show_alert))
        return True

    # -- chat / members -------------------------------------------------------

    async def get_chat_member(self, chat_id, user_id):
        return await _get_chat_member(self._client, chat_id, int(user_id))
