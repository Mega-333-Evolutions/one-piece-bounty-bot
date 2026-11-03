import asyncio
import logging
import time
from pathlib import Path
from typing import Sequence, Optional

from src.tg_compat import Update, PhotoSize, UserProfilePhotos, File, ChatMember, Message
from src.tg_compat import User as TelegramUser, ChatMemberAdministrator
from src.tg_compat.constants import ChatMemberStatus
from src.tg_compat.error import BadRequest, ChatMigrated, RetryAfter, TelegramError, TimedOut
from src.tg_compat.ext import ContextTypes

import constants as c
import resources.Environment as Env
from src.model.Group import Group
from src.model.GroupChat import GroupChat
from src.model.UnmutedUser import UnmutedUser
from src.model.User import User
from src.model.enums.BossType import BossType
from src.model.enums.LeaderboardRank import PIRATE_KING
from src.model.error.CustomException import AnonymousAdminException
from src.service.leaderboard_service import get_current_leaderboard_rank
from src.utils.download_utils import generate_temp_file_path


# Telegram limits how many profile photo lookups a bot may make in a short time, and answers the
# ones over the limit with a "flood wait": a few seconds during which every lookup is refused.
# The wait is for the whole bot, not for one user, so a burst of /status commands (each one looks
# up a photo for its poster) from different players is enough to trigger it. A wait of up to this
# many seconds is waited out - once - before the lookup is tried again; a longer one is not worth
# keeping the command waiting for, so the photo is skipped instead
PROFILE_PHOTO_MAX_FLOOD_WAIT_SECONDS = 5
# Added to every flood wait that is waited out, as Telegram counts it on its own clock
PROFILE_PHOTO_FLOOD_WAIT_MARGIN_SECONDS = 0.5

# time.monotonic() value until which every profile photo lookup is on hold because of a flood
# wait (0 when none is). Shared by the lookups running at the same time, so that the ones starting
# during a flood wait do not hit Telegram again (and get refused again) before it is over
_profile_photo_hold_until: float = 0.0


async def get_user_profile_photo(
    update: Update, telegram_user: TelegramUser = None
) -> str | None:
    """
    Gets the user's profile photo.
    The photo is only a decoration (of the bounty poster), so this never fails because Telegram
    refuses to hand it over: on a flood wait it waits once (if the wait is short) and tries
    again, and if the photo still can't be fetched the result is None, exactly as for a user
    who has no photo, and the poster is made with the default portrait
    :param update: Telegram update
    :param telegram_user: Optional Telegram user to fetch the photo for
    :return: The path of the user's profile photo, None if there is none or it can't be fetched
    """

    global _profile_photo_hold_until

    if telegram_user is None:
        # Anonymous admin, no photo available
        if update.effective_message.sender_chat is not None:
            return None
        telegram_user = update.effective_user

    if telegram_user is None:
        return None

    telegram_user_id = getattr(telegram_user, "id", None)

    for attempt in range(2):
        # A flood wait is on, started by the previous attempt or by another lookup running at the
        # same time: wait it out if it is short, otherwise do without the photo
        wait_seconds = _profile_photo_hold_until - time.monotonic()
        if wait_seconds > PROFILE_PHOTO_MAX_FLOOD_WAIT_SECONDS:
            logging.warning(
                f"Skipping the profile photo of user {telegram_user_id}: Telegram asked to wait"
                f" {wait_seconds:.0f} more seconds before the next lookup"
            )
            return None
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        try:
            return await _download_user_profile_photo(telegram_user)
        except RetryAfter as ra:
            _profile_photo_hold_until = max(
                _profile_photo_hold_until,
                time.monotonic() + float(ra.retry_after) + PROFILE_PHOTO_FLOOD_WAIT_MARGIN_SECONDS,
            )
            logging.warning(
                f"Flood wait of {ra.retry_after} seconds getting the profile photo of user"
                f" {telegram_user_id} (attempt {attempt + 1} of 2)"
            )
        except TelegramError as te:
            # Any other refusal or network failure: the photo is not worth failing the command for
            logging.warning(f"Failed to get the profile photo of user {telegram_user_id}: {te}")
            return None

    # Refused again after waiting once
    return None


async def _download_user_profile_photo(telegram_user: TelegramUser) -> str | None:
    """
    Downloads the last profile photo that the user has set
    :param telegram_user: The Telegram user to download the photo of
    :return: The path of the downloaded photo, None if the user has none
    :raises TelegramError: If Telegram refuses the lookup or the download, RetryAfter included
    """

    # Get user's last photo
    photo_path: Optional[Path] = None
    try:
        # More verbose to get IDE hints
        user_profile_photos: UserProfilePhotos = await telegram_user.get_profile_photos(
            limit=1
        )
        last_set_photos: Sequence[PhotoSize] = user_profile_photos.photos[0]
        last_set_photo: PhotoSize = last_set_photos[-1]
        file: File = await last_set_photo.get_file()
        try:
            photo_path: Path = await file.download_to_drive(
                generate_temp_file_path(c.TG_PROFILE_PHOTO_EXTENSION)
            )
        except TimedOut:
            # One retry for a transient network hiccup - if it still fails, proceed without a
            # photo rather than letting the whole command (e.g. the bounty poster) fail silently
            try:
                photo_path: Path = await file.download_to_drive(
                    generate_temp_file_path(c.TG_PROFILE_PHOTO_EXTENSION)
                )
            except TimedOut as te:
                logging.warning(f"Failed to download profile photo after retrying: {te}")
    except (AttributeError, IndexError):
        pass

    return photo_path


def get_boss_type(user: User, group_chat: GroupChat = None) -> BossType | None:
    """
    Get the boss type of the user
    :param user: The user
    :param group_chat: The group chat
    :return: The boss type
    """

    if user.is_admin:
        return BossType.ADMIN

    if user.is_legendary_pirate():
        return BossType.LEGENDARY_PIRATE

    if get_current_leaderboard_rank(user, group_chat) == PIRATE_KING:
        return BossType.PIRATE_KING

    if user.is_warlord():
        return BossType.WARLORD

    if group_chat is not None:
        # Check for Pirate King in global leaderboard
        if get_current_leaderboard_rank(user) == PIRATE_KING:
            return BossType.PIRATE_KING

    return None


def user_has_combat_loss_immunity(user: User) -> bool:
    """
    Returns True if the user is immune from combat-related losses (fights and plunders).
    Only Admirals (the Admin rank) are. Legendary Pirates used to be and no longer are
    :param user: The user
    :return: True if the user is immune from combat-related losses
    """

    return bool(user.is_admin)


def user_is_boss(user: User, group_chat: GroupChat = None) -> bool:
    """
    Returns True if the user is a boss
    :param user: The user
    :param group_chat: The group chat
    :return: True if the user is a boss
    """

    return get_boss_type(user, group_chat) is not None


def user_is_muted(user: User, group_chat: GroupChat) -> bool:
    """
    Returns True if the user is muted
    :param user: The user
    :param group_chat: The group chat
    :return: True if the user is muted
    """

    if group_chat is None:
        return False

    if user_is_boss(user):
        return False

    if not group_chat.is_muted:
        return False

    return (
        UnmutedUser.get_or_none(UnmutedUser.user == user, UnmutedUser.group_chat == group_chat)
        is None
    )


async def get_chat_member(
    user: User,
    group_chat: GroupChat,
    update: Update = None,
    context: ContextTypes.DEFAULT_TYPE = None,
    tg_group_id: str = None,
) -> ChatMember | None:
    """
    Returns the chat member of the user
    :param user: The user
    :param group_chat: The group chat
    :param update: The update
    :param context: The context
    :param tg_group_id: The chat id
    :return: The chat member
    """

    if update is None and group_chat is None and tg_group_id is None:
        raise ValueError("update or group_chat or tg_group_id must be specified")

    if group_chat is not None and context is None:
        raise ValueError("context must be specified if group_chat is specified")

    from src.tg_compat.error import Forbidden

    try:
        if update is not None:
            return await update.effective_chat.get_member(int(user.tg_user_id))
        elif group_chat is not None:  # To avoid IDE warning
            group: Group = group_chat.group
            return await context.bot.get_chat_member(group.tg_group_id, str(user.tg_user_id))
        elif tg_group_id is not None:
            return await context.bot.get_chat_member(tg_group_id, str(user.tg_user_id))
        else:
            raise ValueError("update or group_chat must be specified")
    except ChatMigrated as e:
        # Group was upgraded to a Supergroup. Save the new ID and retry.
        if group_chat is not None:
            group: Group = group_chat.group
            group.tg_group_id = e.new_chat_id
            group.save()
            
        if context is not None:
            return await context.bot.get_chat_member(e.new_chat_id, str(user.tg_user_id))
        elif update is not None:
            return await update.get_bot().get_chat_member(e.new_chat_id, str(user.tg_user_id))
        return None
    except (Forbidden, BadRequest):  # Bot kicked from the group chat or user not found
        return None
    except TimedOut:  # Telegram API timeout - treat as non-admin, don't crash handler
        return None


async def user_is_chat_member(
    user: User,
    update: Update = None,
    context: ContextTypes.DEFAULT_TYPE = None,
    group_chat: GroupChat = None,
    tg_group_id: str = None,
) -> bool:
    """
    Returns True if the user is a member of the chat
    :param user: The user
    :param update: The update
    :param context: The context
    :param group_chat: The group chat
    :param tg_group_id: The chat id
    :return: True if the user is a member of the chat
    """

    chat_member: ChatMember = await get_chat_member(user, group_chat, update, context, tg_group_id)
    return chat_member is not None and chat_member.status not in [
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
    ]


async def user_is_chat_admin(
    user: User,
    update: Update = None,
    context: ContextTypes.DEFAULT_TYPE = None,
    group_chat: GroupChat = None,
    tg_group_id: str = None,
) -> bool:
    """
    Returns True if the user is an admin of the chat
    :param user: The user
    :param update: The update
    :param context: The context
    :param group_chat: The group chat
    :param tg_group_id: The chat id
    :return: True if the user is an admin of the chat
    """

    chat_member: ChatMember = await get_chat_member(user, group_chat, update, context, tg_group_id)
    return chat_member is not None and chat_member.status in [
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    ]


async def get_effective_tg_user_id(
    effective_user: TelegramUser, effective_message: Message
) -> str:
    """
    Get the effective Telegram user ID, even if anonymous admin
    :param effective_user: The effective user
    :param effective_message: The effective message
    :return: The effective Telegram user ID
    """

    if effective_message is None:  # Encountered in item sharing from keyboard
        return str(effective_user.id)

    if effective_message.sender_chat is None:
        return str(effective_user.id)

    # Anonymous admin
    # Get all chat admins
    # noinspection PyTypeChecker
    chat_admins: list[ChatMemberAdministrator] = await effective_message.chat.get_administrators()

    if len(chat_admins) == 0:
        raise AnonymousAdminException()

    # Just 1 admin, must be the one that sent the message
    if len(chat_admins) == 1:
        return str(chat_admins[0].user.id)

    # Message without author signature, no way to determine user
    if effective_message.author_signature is None:
        raise AnonymousAdminException()

    # Get the admin with the same title as the author signature, if unique
    admins_with_same_title = [
        a for a in chat_admins if a.custom_title == effective_message.author_signature
    ]

    # No Admin with title, should never happen
    if len(admins_with_same_title) == 0:
        raise ValueError(f"Admin with title {effective_message.author_signature} not found")

    # More than one Admin with same title, no way to determine user
    if len(admins_with_same_title) > 1:
        raise AnonymousAdminException()

    return str(admins_with_same_title[0].user.id)


def sync_admin_users() -> None:
    """
    Syncs each user's Admin (Veteran) status with the ADMIN_USER_IDS env var.
    Telegram user ids listed there (space separated) are granted Admin status; any user
    currently marked as Admin whose id is no longer listed has it revoked. To appoint someone,
    add their Telegram user id to the env var. To revoke, remove it
    :return: None
    """

    admin_user_ids: set[str] = set()
    for raw_id in Env.ADMIN_USER_IDS.get().split():
        try:
            admin_user_ids.add(str(int(raw_id)))
        except ValueError:
            logging.warning(f"Invalid Telegram user id in ADMIN_USER_IDS env var: {raw_id}")

    # Grant Admin status to newly listed users
    if len(admin_user_ids) > 0:
        User.update(is_admin=True).where(
            (User.tg_user_id.in_(admin_user_ids)) & (User.is_admin == False)
        ).execute()

    # Revoke Admin status from users no longer listed
    if len(admin_user_ids) > 0:
        User.update(is_admin=False).where(
            (User.is_admin == True) & (User.tg_user_id.not_in(admin_user_ids))
        ).execute()
    else:
        # No ids listed, revoke Admin status from everyone
        User.update(is_admin=False).where(User.is_admin == True).execute()
