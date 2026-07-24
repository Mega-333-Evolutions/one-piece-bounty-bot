"""
Drop-in replacements for telegram.Message / telegram.Update / telegram.CallbackQuery
/ telegram.InlineQuery, built from live Telethon events or raw Telethon message
objects. See runtime.py for where these get constructed from actual Telethon
events.
"""

import logging

from telethon.tl.types import (
    PeerUser,
    MessageActionChatAddUser,
    MessageActionChatDeleteUser,
    MessageActionChatJoinedByLink,
    MessageActionChatMigrateTo,
    MessageActionTopicCreate,
)

from ._errors import translate_errors
from ._types import (
    Chat,
    TelegramUser,
    PhotoSize,
    Video,
    Animation,
    Poll,
    PollOption,
    MessageOriginUser,
    MessageOriginChat,
    MessageOriginChannel,
    MessageOriginHidden,
    coerce_peer,
)

logger = logging.getLogger(__name__)


class ForumTopicCreated:
    def __init__(self, name: str):
        self.name = name


class Message:
    """Mirrors telegram.Message (only the attributes/methods this codebase reads)."""

    def __init__(self, **kwargs):
        self.message_id = kwargs.get("message_id")
        self.text = kwargs.get("text")
        self.chat: Chat = kwargs.get("chat")
        self.from_user: TelegramUser = kwargs.get("from_user")
        self.sender_chat: Chat = kwargs.get("sender_chat")
        self.reply_to_message: "Message" = kwargs.get("reply_to_message")
        self.forward_origin = kwargs.get("forward_origin")
        self.sticker = kwargs.get("sticker")
        self.animation: Animation = kwargs.get("animation")
        self.video: Video = kwargs.get("video")
        self.photo = kwargs.get("photo") or []
        self.dice = kwargs.get("dice")
        self.via_bot: TelegramUser = kwargs.get("via_bot")
        self.poll: Poll = kwargs.get("poll")
        self.new_chat_members = kwargs.get("new_chat_members") or ()
        self.left_chat_member: TelegramUser = kwargs.get("left_chat_member")
        self.migrate_to_chat_id = kwargs.get("migrate_to_chat_id")
        self.message_thread_id = kwargs.get("message_thread_id")
        self.is_topic_message = kwargs.get("is_topic_message", False)
        self.author_signature = kwargs.get("author_signature")
        self.forum_topic_created: ForumTopicCreated = kwargs.get("forum_topic_created")

        self._client = kwargs.get("_client")
        self._bot = kwargs.get("_bot")
        self._tl_message = kwargs.get("_tl_message")

    @property
    def id(self):
        """Mirrors telegram.Message.id, PTB's alias for message_id (added for
        naming consistency with Chat.id/User.id/CallbackQuery.id). Several
        screens in this codebase (daily reward, devil fruit trade, RPS/RR
        games) read message.id directly rather than message.message_id."""
        return self.message_id

    def get_bot(self):
        return self._bot

    async def delete(self):
        await translate_errors(
            self._client.delete_messages(self.chat._entity or self.chat.id, [self.message_id])
        )

    async def pin(self, disable_notification: bool = True):
        await translate_errors(
            self._client.pin_message(
                self.chat._entity or self.chat.id,
                self._tl_message or self.message_id,
                notify=not disable_notification,
            )
        )

    async def forward(self, chat_id, disable_notification: bool = False) -> "Message":
        chat_id = coerce_peer(chat_id)
        result = await translate_errors(
            self._client.forward_messages(
                chat_id,
                self._tl_message or self.message_id,
                from_peer=self.chat._entity or self.chat.id,
                silent=disable_notification,
            )
        )
        tl_result = result[0] if isinstance(result, list) else result
        return await Message.from_telethon(tl_result, self._client, self._bot, fetch_reply=False)

    @staticmethod
    async def _build_forward_origin(tl_message, client):
        fwd = getattr(tl_message, "fwd_from", None)
        if fwd is None:
            return None
        from_id = getattr(fwd, "from_id", None)
        if from_id is None:
            name = getattr(fwd, "from_name", None)
            return MessageOriginHidden(sender_user_name=name)
        try:
            if isinstance(from_id, PeerUser):
                entity = await client.get_entity(from_id)
                return MessageOriginUser(sender_user=TelegramUser.from_entity(entity, client))
            else:
                entity = await client.get_entity(from_id)
                chat = await Chat.from_entity(entity, client)
                channel_post = getattr(fwd, "channel_post", None)
                if channel_post:
                    return MessageOriginChannel(
                        chat=chat,
                        message_id=channel_post,
                        author_signature=getattr(fwd, "post_author", None),
                    )
                return MessageOriginChat(sender_chat=chat)
        except Exception:
            logger.warning("Could not resolve forward origin", exc_info=True)
            return None

    @staticmethod
    async def _build_poll(tl_message):
        media = getattr(tl_message, "media", None)
        poll = getattr(media, "poll", None)
        if poll is None:
            return None
        answers = getattr(poll, "answers", None) or []
        option_texts = []
        for a in answers:
            text_obj = getattr(a, "text", None)
            option_texts.append(getattr(text_obj, "text", None) or str(text_obj) if text_obj else "")
        return Poll(
            question=getattr(getattr(poll, "question", None), "text", None) or "",
            options=[PollOption(text=t) for t in option_texts],
            allows_multiple_answers=bool(getattr(poll, "multiple_choice", False)),
        )

    @classmethod
    async def from_telethon(cls, tl_message, client, bot, chat: Chat = None, fetch_reply: bool = True) -> "Message":
        """Build a compat Message from a real (non-service) Telethon message."""
        if tl_message is None:
            return None

        if chat is None:
            tl_chat = await tl_message.get_chat()
            chat = await Chat.from_entity(tl_chat, client, chat_id=tl_message.chat_id)

        from_user = None
        sender_chat = None
        if isinstance(getattr(tl_message, "from_id", None), PeerUser) or (
            tl_message.from_id is None and chat.type == Chat.PRIVATE
        ):
            sender = await tl_message.get_sender()
            from_user = TelegramUser.from_entity(sender, client)
        elif tl_message.from_id is not None:
            sender_entity = await tl_message.get_sender()
            if sender_entity is not None:
                sender_chat = await Chat.from_entity(sender_entity, client)

        via_bot = None
        if getattr(tl_message, "via_bot_id", None):
            try:
                via_bot_entity = await client.get_entity(tl_message.via_bot_id)
                via_bot = TelegramUser.from_entity(via_bot_entity, client)
            except Exception:
                pass

        photo = []
        if getattr(tl_message, "photo", None):
            photo = [PhotoSize(tl_message.photo, client)]

        video = Video(tl_message.video, client) if getattr(tl_message, "video", None) else None
        animation = Animation(tl_message.gif, client) if getattr(tl_message, "gif", None) else None
        sticker = getattr(tl_message, "sticker", None)
        dice = getattr(tl_message, "dice", None)

        reply_to_message = None
        forum_topic_created = None
        if fetch_reply and getattr(tl_message, "reply_to", None) is not None:
            reply_to_msg_id = getattr(tl_message.reply_to, "reply_to_msg_id", None)
            if reply_to_msg_id:
                try:
                    replied = await client.get_messages(chat._entity or chat.id, ids=reply_to_msg_id)
                except Exception:
                    replied = None
                if replied is not None:
                    action = getattr(replied, "action", None)
                    if isinstance(action, MessageActionTopicCreate):
                        forum_topic_created = ForumTopicCreated(name=action.title)
                    reply_to_message = await cls.from_telethon(
                        replied, client, bot, chat=chat, fetch_reply=False
                    )
                    if reply_to_message is not None:
                        reply_to_message.forum_topic_created = forum_topic_created

        forward_origin = await cls._build_forward_origin(tl_message, client)
        poll = await cls._build_poll(tl_message)

        is_topic_message = bool(getattr(getattr(tl_message, "reply_to", None), "forum_topic", False))
        message_thread_id = getattr(getattr(tl_message, "reply_to", None), "reply_to_top_id", None) or (
            getattr(tl_message.reply_to, "reply_to_msg_id", None) if is_topic_message else None
        )

        return cls(
            message_id=tl_message.id,
            text=tl_message.message or None,
            chat=chat,
            from_user=from_user,
            sender_chat=sender_chat,
            reply_to_message=reply_to_message,
            forward_origin=forward_origin,
            sticker=sticker,
            animation=animation,
            video=video,
            photo=photo,
            dice=dice,
            via_bot=via_bot,
            poll=poll,
            message_thread_id=message_thread_id,
            is_topic_message=is_topic_message,
            author_signature=getattr(tl_message, "post_author", None),
            forum_topic_created=forum_topic_created,
            _client=client,
            _bot=bot,
            _tl_message=tl_message,
        )

    @classmethod
    async def from_chat_action(cls, event, client, bot) -> "Message":
        """Build a compat Message from a Telethon ChatAction event (join / leave /
        migrate / topic creation), matching how Bot API folds these into optional
        fields on a single Message object instead of separate update types."""
        tl_message = event.action_message
        tl_chat = await event.get_chat()
        chat = await Chat.from_entity(tl_chat, client, chat_id=event.chat_id)

        from_user = None
        try:
            sender_entity = await event.get_sender()
            from_user = TelegramUser.from_entity(sender_entity, client) if sender_entity else None
        except Exception:
            from_user = None

        new_chat_members = None
        left_chat_member = None
        migrate_to_chat_id = None

        action = getattr(tl_message, "action", None) if tl_message is not None else None

        if isinstance(action, (MessageActionChatAddUser,)):
            members = []
            for uid in action.users:
                if bot is not None and bot.id is not None and uid == bot.id:
                    # The bot's own identity never needs resolving - it's
                    # already known from get_me() at startup (runtime.py).
                    # Looking it up via get_entity() instead is not just
                    # unnecessary but risky here specifically: this chat may
                    # have no prior history with the bot at all (it was
                    # *just* added), and a fresh, first-ever-seen entity in a
                    # ChatAction event is exactly the kind of lookup that can
                    # come back as a "min" user (no usable access_hash) or
                    # fail outright - silently dropping the bot out of
                    # new_chat_members below, which is what made
                    # get_added_or_removed_from_group_event() (in
                    # group_chat_manager.py) unable to tell the bot had just
                    # been added, so it never sent its usual "thanks for
                    # adding me" group setup message.
                    members.append(TelegramUser(id=bot.id, is_bot=True, username=bot.username))
                    continue
                try:
                    entity = await client.get_entity(uid)
                    members.append(TelegramUser.from_entity(entity, client))
                except Exception:
                    pass
            new_chat_members = members
        elif isinstance(action, MessageActionChatJoinedByLink):
            new_chat_members = [from_user] if from_user else []
        elif isinstance(action, MessageActionChatDeleteUser):
            try:
                entity = await client.get_entity(action.user_id)
                left_chat_member = TelegramUser.from_entity(entity, client)
            except Exception:
                pass
        elif isinstance(action, MessageActionChatMigrateTo):
            # Bot-API-style marked id for the new supergroup (matches the
            # "-100<channel_id>" convention Telethon also uses by default).
            migrate_to_chat_id = int(f"-100{action.channel_id}")

        return cls(
            message_id=getattr(tl_message, "id", None),
            chat=chat,
            from_user=from_user,
            new_chat_members=new_chat_members,
            left_chat_member=left_chat_member,
            migrate_to_chat_id=migrate_to_chat_id,
            _client=client,
            _bot=bot,
            _tl_message=tl_message,
        )


async def answer_callback_query(client, callback_query_id, text: str = None, show_alert: bool = False, cache_time: int = 0):
    """Shared implementation for answering a callback query by id, used by
    both CallbackQuery.answer() and Bot.answer_callback_query()."""
    from telethon.tl.functions.messages import SetBotCallbackAnswerRequest

    return await translate_errors(
        client(
            SetBotCallbackAnswerRequest(
                query_id=int(callback_query_id),
                cache_time=cache_time,
                alert=show_alert,
                message=text,
            )
        )
    )


class CallbackQuery:
    """Mirrors telegram.CallbackQuery."""

    def __init__(self, id: str, data: str, message: Message, from_user: TelegramUser, _client=None):
        self.id = id
        self.data = data
        self.message = message
        self.from_user = from_user
        self._client = _client

    async def answer(self, text: str = None, show_alert: bool = False):
        await answer_callback_query(self._client, self.id, text=text, show_alert=show_alert)


class InlineQuery:
    """Mirrors telegram.InlineQuery."""

    def __init__(self, id: str, query: str, from_user: TelegramUser, _event=None):
        self.id = id
        self.query = query
        self.from_user = from_user
        self._event = _event

    async def answer(self, results, **kwargs):
        from ._inline import build_and_answer_inline_query

        await build_and_answer_inline_query(self._event, results, **kwargs)


class Update:
    """Mirrors telegram.Update - a thin container the rest of the codebase reads
    .effective_user / .effective_chat / .effective_message / .message /
    .callback_query / .inline_query from."""

    def __init__(
        self,
        message: Message = None,
        callback_query: CallbackQuery = None,
        inline_query: InlineQuery = None,
        _bot=None,
    ):
        self.message = message
        self.callback_query = callback_query
        self.inline_query = inline_query
        self._bot = _bot

    @property
    def effective_message(self) -> Message:
        if self.message is not None:
            return self.message
        if self.callback_query is not None:
            return self.callback_query.message
        return None

    @property
    def effective_chat(self) -> Chat:
        msg = self.effective_message
        return msg.chat if msg is not None else None

    @property
    def effective_user(self) -> TelegramUser:
        if self.callback_query is not None:
            return self.callback_query.from_user
        if self.inline_query is not None:
            return self.inline_query.from_user
        if self.message is not None:
            return self.message.from_user
        return None

    def get_bot(self):
        return self._bot
