"""
Drop-in replacements for the ``telegram`` types used across the codebase
(``Update``, ``Message``, ``Chat``, ``User``, keyboard classes, media types,
etc). Every one of these is a plain Python object - no Telethon network calls
happen in ``__init__``; async operations (leaving a chat, checking admin
status, downloading a profile photo...) are implemented as async methods that
use the Telethon client stashed on the object at construction time.

This module is intentionally *not* a complete reimplementation of PTB's
``telegram`` package - it implements exactly the surface area exercised by
this codebase (see MIGRATION_NOTES.md for how that surface was audited).
"""

import json
import base64
import logging

from telethon.tl.types import (
    Channel,
    Chat as TLChat,
    User as TLUser,
    ChatParticipantCreator,
    ChatParticipantAdmin,
    ChannelParticipantsAdmins,
)
from telethon.tl.functions.messages import GetFullChatRequest

from .error import BadRequest
from .constants import ChatMemberStatus

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# User
# --------------------------------------------------------------------------


class TelegramUser:
    """Mirrors telegram.User (only the attributes this codebase reads)."""

    def __init__(
        self,
        id: int,
        is_bot: bool = False,
        first_name: str = "",
        last_name: str = None,
        username: str = None,
        _entity=None,
        _client=None,
    ):
        self.id = id
        self.is_bot = is_bot
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self._entity = _entity
        self._client = _client

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name or ""

    @classmethod
    def from_entity(cls, entity, client=None) -> "TelegramUser":
        if entity is None:
            return None
        return cls(
            id=entity.id,
            is_bot=bool(getattr(entity, "bot", False)),
            first_name=getattr(entity, "first_name", None) or "",
            last_name=getattr(entity, "last_name", None),
            username=getattr(entity, "username", None),
            _entity=entity,
            _client=client,
        )

    async def get_profile_photos(self, limit: int = 100) -> "UserProfilePhotos":
        """Mirrors telegram.User.get_profile_photos / Bot.get_user_profile_photos."""
        from ._errors import translate_errors

        photos = await translate_errors(self._client.get_profile_photos(self._entity or self.id, limit=limit))
        # PTB shapes this as a list of "photo groups" (one per profile photo,
        # each itself a list of resolutions); Telethon gives us one Photo per
        # profile picture, so each group has exactly one entry. The owner
        # entity is threaded through to PhotoSize/File so the eventual
        # download goes through download_profile_photo() rather than handing
        # the bare Photo object to download_media() - see PhotoSize.get_file.
        owner = self._entity or self.id
        groups = [[PhotoSize(p, self._client, owner_entity=owner)] for p in photos]
        return UserProfilePhotos(total_count=len(photos), photos=groups)

    def __repr__(self):
        return f"TelegramUser(id={self.id}, username={self.username!r})"


# --------------------------------------------------------------------------
# Media wrappers (PhotoSize / Video / Animation / File)
# --------------------------------------------------------------------------


def _encode_media_ref(kind: str, tl_media, fallback_path: str = None) -> str:
    """
    Encode a Telethon Photo/Document object into an opaque string, mirroring
    the role of a Bot API file_id: a compact, reusable reference that lets us
    resend the same media later without re-uploading it.

    Unlike Bot API file_ids, MTProto file references expire after a while;
    the encoded fallback_path (if given) lets the sending code transparently
    fall back to a fresh upload if the cached reference has expired. See
    MIGRATION_NOTES.md ("Media re-use / file_id caching") for details.
    """
    payload = {
        "k": kind,
        "id": tl_media.id,
        "ah": tl_media.access_hash,
        "fr": base64.b64encode(tl_media.file_reference).decode("ascii"),
        "dc": tl_media.dc_id,
    }
    if fallback_path:
        payload["fp"] = fallback_path
    return "tgcref1:" + base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def is_media_ref(value) -> bool:
    return isinstance(value, str) and value.startswith("tgcref1:")


def decode_media_ref(value: str) -> dict:
    return json.loads(base64.b64decode(value[len("tgcref1:") :]).decode("utf-8"))


class PhotoSize:
    """Mirrors telegram.PhotoSize. Wraps a Telethon Photo object."""

    def __init__(self, tl_photo, client=None, fallback_path: str = None, owner_entity=None):
        self._tl_photo = tl_photo
        self._client = client
        self._fallback_path = fallback_path
        self._owner_entity = owner_entity
        self.file_size = getattr(tl_photo, "size", None)

    @property
    def file_id(self) -> str:
        return _encode_media_ref("photo", self._tl_photo, self._fallback_path)

    async def get_file(self) -> "File":
        return File(self._tl_photo, self._client, owner_entity=self._owner_entity)

    def __len__(self):
        # Defensive: some call sites do `len(message.video)`-style truthiness
        # checks assuming a collection; a real media object is always "there".
        return 1


class Video:
    """Mirrors telegram.Video. Wraps a Telethon Document (video) object."""

    def __init__(self, tl_document, client=None, fallback_path: str = None):
        self._tl_document = tl_document
        self._client = client
        self._fallback_path = fallback_path
        self.file_size = getattr(tl_document, "size", None)

    @property
    def file_id(self) -> str:
        return _encode_media_ref("video", self._tl_document, self._fallback_path)

    async def get_file(self) -> "File":
        return File(self._tl_document, self._client)

    def __len__(self):
        return 1


class Animation:
    """Mirrors telegram.Animation. Wraps a Telethon Document (gif) object."""

    def __init__(self, tl_document, client=None, fallback_path: str = None):
        self._tl_document = tl_document
        self._client = client
        self._fallback_path = fallback_path
        self.file_size = getattr(tl_document, "size", None)

    @property
    def file_id(self) -> str:
        return _encode_media_ref("animation", self._tl_document, self._fallback_path)

    async def get_file(self) -> "File":
        return File(self._tl_document, self._client)

    def __len__(self):
        return 1


class File:
    """Mirrors telegram.File."""

    def __init__(self, tl_media, client=None, owner_entity=None):
        self._tl_media = tl_media
        self._client = client
        # Set only when this File wraps a *profile* photo - see
        # download_to_drive() below for why that changes how we download it.
        self._owner_entity = owner_entity

    async def download_to_drive(self, custom_path=None):
        from ._errors import translate_errors

        if self._owner_entity is not None:
            # Handing a bare Photo object (as returned by get_profile_photos)
            # straight to download_media() is a known Telethon footgun: it
            # can silently download a tiny/placeholder thumbnail instead of
            # the full-size photo instead of raising an error (see
            # https://github.com/LonamiWebs/Telethon/issues/1519), which is
            # what was causing "cannot identify image file" downstream in
            # bounty poster generation. download_profile_photo() is the
            # purpose-built, confirmed-working method for this instead.
            return await translate_errors(
                self._client.download_profile_photo(
                    self._owner_entity, file=custom_path, download_big=True
                )
            )

        return await translate_errors(self._client.download_media(self._tl_media, file=custom_path))


class UserProfilePhotos:
    """Mirrors telegram.UserProfilePhotos."""

    def __init__(self, total_count: int, photos):
        self.total_count = total_count
        self.photos = photos


# --------------------------------------------------------------------------
# Chat member status
# --------------------------------------------------------------------------


class ChatMember:
    """Mirrors telegram.ChatMember (base)."""

    def __init__(self, user: TelegramUser, status: str, custom_title: str = None):
        self.user = user
        self.status = status
        self.custom_title = custom_title


class ChatMemberAdministrator(ChatMember):
    """Mirrors telegram.ChatMemberAdministrator."""

    def __init__(self, user: TelegramUser, custom_title: str = None):
        super().__init__(user=user, status=ChatMemberStatus.ADMINISTRATOR, custom_title=custom_title)


async def _get_chat_member(client, chat_entity, user_id) -> ChatMember:
    """Resolve a single chat member's status. Never raises for "not currently
    a member" - both LEFT and BANNED collapse to LEFT, matching how this
    codebase's user_is_chat_member() treats them identically anyway."""
    from ._errors import translate_errors

    user_entity = await translate_errors(client.get_entity(user_id))
    user = TelegramUser.from_entity(user_entity, client)

    try:
        perms = await translate_errors(client.get_permissions(chat_entity, user_id))
    except BadRequest:
        return ChatMember(user=user, status=ChatMemberStatus.LEFT)

    if getattr(perms, "is_creator", False):
        status = ChatMemberStatus.OWNER
    elif getattr(perms, "is_admin", False):
        status = ChatMemberStatus.ADMINISTRATOR
    else:
        status = ChatMemberStatus.MEMBER
    return ChatMember(user=user, status=status)


async def _get_chat_administrators(client, chat_entity):
    """Returns a list of ChatMemberAdministrator for the given chat. For
    basic (non-super) groups, falls back to inspecting the full chat's
    participant list since ChannelParticipantsAdmins only applies to
    channels/supergroups."""
    from ._errors import translate_errors

    entity = chat_entity
    if not isinstance(entity, (Channel, TLChat, TLUser)):
        entity = await translate_errors(client.get_entity(chat_entity))

    result = []
    if isinstance(entity, Channel):
        admins = await translate_errors(
            client.get_participants(entity, filter=ChannelParticipantsAdmins())
        )
        for u in admins:
            raw = getattr(u, "participant", None)
            custom_title = getattr(raw, "rank", None) if raw is not None else None
            result.append(
                ChatMemberAdministrator(user=TelegramUser.from_entity(u, client), custom_title=custom_title)
            )
        return result

    # Basic group
    full = await translate_errors(client(GetFullChatRequest(chat_id=entity.id)))
    admin_ids = set()
    for p in getattr(full.full_chat.participants, "participants", []):
        if isinstance(p, (ChatParticipantCreator, ChatParticipantAdmin)):
            admin_ids.add(p.user_id)
    users_by_id = {u.id: u for u in full.users}
    for uid in admin_ids:
        u = users_by_id.get(uid)
        if u is not None:
            result.append(ChatMemberAdministrator(user=TelegramUser.from_entity(u, client)))
    return result


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------


class Chat:
    """Mirrors telegram.Chat."""

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"

    def __init__(
        self,
        id: int,
        type: str,
        title: str = None,
        username: str = None,
        is_forum: bool = False,
        _entity=None,
        _client=None,
    ):
        self.id = id
        self.type = type
        self.title = title
        self.username = username
        self.is_forum = is_forum
        self._entity = _entity
        self._client = _client

    @classmethod
    async def from_entity(cls, entity, client, chat_id: int = None) -> "Chat":
        if isinstance(entity, TLUser):
            chat_type = cls.PRIVATE
            title = None
            is_forum = False
        elif isinstance(entity, Channel):
            chat_type = cls.SUPERGROUP if entity.megagroup else cls.CHANNEL
            title = entity.title
            is_forum = bool(getattr(entity, "forum", False))
        elif isinstance(entity, TLChat):
            chat_type = cls.GROUP
            title = entity.title
            is_forum = False
        else:
            chat_type = cls.PRIVATE
            title = None
            is_forum = False

        from telethon import utils

        resolved_id = chat_id if chat_id is not None else utils.get_peer_id(entity)
        return cls(
            id=resolved_id,
            type=chat_type,
            title=title,
            username=getattr(entity, "username", None),
            is_forum=is_forum,
            _entity=entity,
            _client=client,
        )

    async def leave(self):
        from ._errors import translate_errors

        await translate_errors(self._client.delete_dialog(self._entity or self.id))

    async def get_member(self, user_id: int) -> ChatMember:
        return await _get_chat_member(self._client, self._entity or self.id, user_id)

    async def get_administrators(self):
        return await _get_chat_administrators(self._client, self._entity or self.id)

    def __repr__(self):
        return f"Chat(id={self.id}, type={self.type!r})"


# --------------------------------------------------------------------------
# Forward origin
# --------------------------------------------------------------------------


class MessageOriginUser:
    def __init__(self, sender_user: TelegramUser):
        self.sender_user = sender_user


class MessageOriginChat:
    def __init__(self, sender_chat: Chat):
        self.sender_chat = sender_chat


class MessageOriginChannel:
    def __init__(self, chat: Chat, message_id: int = None, author_signature: str = None):
        self.chat = chat
        self.message_id = message_id
        self.author_signature = author_signature


class MessageOriginHidden:
    def __init__(self, sender_user_name: str = None):
        self.sender_user_name = sender_user_name


# --------------------------------------------------------------------------
# Poll
# --------------------------------------------------------------------------


class PollOption:
    def __init__(self, text: str, voter_count: int = 0):
        self.text = text
        self.voter_count = voter_count


class Poll:
    def __init__(self, question: str, options, allows_multiple_answers: bool = False):
        self.question = question
        self.options = options
        self.allows_multiple_answers = allows_multiple_answers
