import asyncio
import logging
from datetime import datetime, timedelta

from src.tg_compat import Message
from src.tg_compat.error import TelegramError, RetryAfter
from src.tg_compat.ext import ContextTypes

import resources.Environment as Env
from resources import phrases
from src.model.BaseModel import BaseModel
from src.model.Group import Group
from src.model.GroupChat import GroupChat
from src.model.GroupChatAutoDelete import GroupChatAutoDelete
from src.model.GroupChatEnabledDisabledFeature import GroupChatEnabledDisabledFeature
from src.model.GroupChatEnabledFeaturePin import GroupChatEnabledFeaturePin
from src.model.GroupChatFeaturePinMessage import GroupChatFeaturePinMessage
from src.model.GroupUser import GroupUser
from src.model.Leaderboard import Leaderboard
from src.model.Prediction import Prediction
from src.model.PredictionGroupChatMessage import PredictionGroupChatMessage
from src.model.User import User
from src.model.enums.Feature import Feature
from src.model.pojo.Keyboard import Keyboard
from src.service.message_service import full_message_send, delete_message


def is_main_group(group_chat: GroupChat) -> bool:
    """
    Checks if the update is from the main group_chat
    :param group_chat: The group chat
    :return: True if the message is from the main group_chat, False otherwise
    """

    main_group_id = Env.MAIN_GROUP_ID.get()
    if main_group_id is None:
        return False

    group: Group = group_chat.group
    return int(group.tg_group_id) == int(main_group_id)


def feature_is_enabled(group_chat: GroupChat, feature: Feature) -> bool:
    """
    Checks if a feature is enabled
    :param group_chat: The group chat
    :param feature: The feature
    :return: True if the feature is enabled, False otherwise
    """

    group_chat_enabled_disabled_feature = GroupChatEnabledDisabledFeature.get_or_none(
        (GroupChatEnabledDisabledFeature.group_chat == group_chat)
        & (GroupChatEnabledDisabledFeature.feature == feature)
    )

    return (
        feature.is_enabled_by_default()
        if group_chat_enabled_disabled_feature is None
        else not feature.is_enabled_by_default()
    )


def get_group_or_topic_text(group_chat: GroupChat) -> str:
    """
    Gets the group chat or group_chat text
    :param group_chat: The group chat
    :return: The group chat or group_chat text
    """

    if group_chat.tg_topic_id is not None:
        return phrases.TEXT_TOPIC
    else:
        return phrases.TEXT_GROUP


def get_group_chats_with_feature_enabled(
    feature: Feature,
    filter_by_groups: list[Group] = None,
    excluded_group_chats: list[GroupChat] = None,
) -> list[GroupChat]:
    """
    Gets the group chats with a feature enabled
    :param feature: The feature
    :param filter_by_groups: The groups to filter by
    :param excluded_group_chats: The group chats to exclude from the result
    :return: The list of group chats with the feature enabled
    """

    if filter_by_groups is None:
        filter_by_groups = []

    if len(filter_by_groups) > 0:
        group_filter = GroupChat.group.in_(filter_by_groups)
    else:
        group_filter = True

    if excluded_group_chats is None:
        excluded_group_chats = []

    # Would be better to use some join, couldn't get it to work though
    group_chats_enabled_disabled_feature: list[
        GroupChatEnabledDisabledFeature
    ] = GroupChatEnabledDisabledFeature.select().where(
        GroupChatEnabledDisabledFeature.feature == feature
    )

    if feature.is_enabled_by_default():
        group_chats_with_feature_disabled: list[GroupChat] = [
            gcf.group_chat for gcf in group_chats_enabled_disabled_feature
        ]
    else:  # Find all group_chats that don't have a record
        group_chats_with_feature_disabled: list[GroupChat] = [
            gc
            for gc in GroupChat.select().where(
                (GroupChat.is_active == True)
                & (
                    GroupChat.id.not_in(
                        [gcf.group_chat.id for gcf in group_chats_enabled_disabled_feature]
                    )
                )
            )
        ]

    return (
        GroupChat.select()
        .distinct()
        .join(Group, on=(Group.id == GroupChat.group))
        .where(
            (Group.is_active == True)
            & (GroupChat.is_active == True)
            & group_filter
            & (GroupChat.id.not_in([egc.id for egc in excluded_group_chats]))
            & (GroupChat.id.not_in([c.id for c in group_chats_with_feature_disabled]))
        )
    )


async def broadcast_to_chats_with_feature_enabled_dispatch(
    context: ContextTypes.DEFAULT_TYPE,
    feature: Feature,
    text: str,
    inline_keyboard: list[list[Keyboard]] = None,
    excluded_group_chats: list[GroupChat] = None,
    external_item: BaseModel = None,
    filter_by_groups: list[Group] = None,
) -> None:
    """
    Broadcasts a message to all the chats with a feature enabled
    :param context: The context
    :param feature: The feature
    :param text: The message
    :param inline_keyboard: The outbound keyboard
    :param excluded_group_chats: The chats to exclude from the broadcast
    :param external_item: The external item to save the group chat message
    :param filter_by_groups: The groups to filter by
    """

    context.application.create_task(
        broadcast_to_chats_with_feature_enabled(
            context,
            feature,
            text,
            inline_keyboard=inline_keyboard,
            excluded_group_chats=excluded_group_chats,
            external_item=external_item,
            filter_by_groups=filter_by_groups,
        )
    )


async def broadcast_to_chats_with_feature_enabled(
    context: ContextTypes.DEFAULT_TYPE,
    feature: Feature,
    text: str,
    inline_keyboard: list[list[Keyboard]] = None,
    excluded_group_chats: list[GroupChat] = None,
    external_item: BaseModel = None,
    filter_by_groups: list[Group] = None,
) -> None:
    """
    Broadcasts a message to all the chats with a feature enabled
    :param context: The context
    :param feature: The feature
    :param text: The message
    :param inline_keyboard: The outbound keyboard
    :param excluded_group_chats: The chats to exclude from the broadcast
    :param external_item: The external item to save the group chat message
    :param filter_by_groups: The groups to filter by
    """

    if feature in [Feature.PREDICTION, Feature.LEADERBOARD] and external_item is None:
        raise ValueError(
            "External item cannot be None if the feature is " + feature.get_description()
        )

    if filter_by_groups is None:
        filter_by_groups = []

    group_chats: list[GroupChat] = get_group_chats_with_feature_enabled(
        feature, excluded_group_chats=excluded_group_chats, filter_by_groups=filter_by_groups
    )
    feature_is_pinnable = feature.is_pinnable()

    # Unpin all previous messages of this feature
    if feature_is_pinnable:
        # Get all messages to unpin to avoid unpinning messages that are just pinned due to async
        # call
        messages_to_unpin: list[GroupChatFeaturePinMessage] = list(
            GroupChatFeaturePinMessage.select().where(
                GroupChatFeaturePinMessage.feature == feature
            )
        )
        await unpin_feature_messages_dispatch(context, messages_to_unpin)

    for group_chat in group_chats:
        group_chat: GroupChat = group_chat
        try:
            message: Message = await full_message_send(
                context, text, keyboard=inline_keyboard, group_chat=group_chat
            )

            if feature is Feature.PREDICTION:  # Save Prediction Group Chat Message
                prediction_group_chat_message: PredictionGroupChatMessage = (
                    PredictionGroupChatMessage()
                )
                external_item: Prediction = external_item
                prediction_group_chat_message.prediction = external_item
                prediction_group_chat_message.group_chat = group_chat
                prediction_group_chat_message.message_id = message.message_id
                prediction_group_chat_message.save()
            elif feature is Feature.LEADERBOARD:  # Save Leaderboard message id
                external_item: Leaderboard = external_item
                external_item.message_id = message.message_id
                external_item.save()
        except TelegramError as te:
            logging.warning(
                f"Failed to send {feature.get_description()} message to group chat "
                f"{group_chat.id}: {te}"
            )
            save_group_chat_error(group_chat, str(te))
            continue

        if not feature_is_pinnable:
            continue

        has_pin_record = (
            GroupChatEnabledFeaturePin.get_or_none(
                (GroupChatEnabledFeaturePin.group_chat == group_chat)
                & (GroupChatEnabledFeaturePin.feature == feature)
            )
            is not None
        )
        should_pin = (
            not feature.is_pinned_by_default() if has_pin_record else feature.is_pinned_by_default()
        )

        if not should_pin:
            continue

        # The send above already counts against Telegram's flood limits, so pinning right after
        # it is what most commonly trips RetryAfter when broadcasting to many groups in a row.
        # Retry once after waiting it out instead of silently giving up on pinning this message.
        for attempt in range(2):
            try:
                await message.pin(disable_notification=True)
                pin_message: GroupChatFeaturePinMessage = GroupChatFeaturePinMessage()
                pin_message.group_chat = group_chat
                pin_message.feature = feature
                pin_message.message_id = message.message_id
                pin_message.save()
                break
            except RetryAfter as ra:
                if attempt == 0:
                    logging.warning(
                        f"Rate limited while pinning {feature.get_description()} message in "
                        f"group chat {group_chat.id}, retrying in {ra.retry_after}s"
                    )
                    await asyncio.sleep(ra.retry_after)
                    continue
                logging.warning(
                    f"Failed to pin {feature.get_description()} message in group chat "
                    f"{group_chat.id} after retrying: {ra}"
                )
                save_group_chat_error(group_chat, str(ra))
            except TelegramError as te:
                logging.warning(
                    f"Failed to pin {feature.get_description()} message in group chat "
                    f"{group_chat.id}: {te}"
                )
                save_group_chat_error(group_chat, str(te))
                break


async def unpin_feature_messages_dispatch(
    context: ContextTypes.DEFAULT_TYPE, messages_to_unpin: list[GroupChatFeaturePinMessage]
) -> None:
    """
    Unpins the feature messages
    :param context: The context
    :param messages_to_unpin: The messages to unpin
    """

    context.application.create_task(unpin_feature_messages(context, messages_to_unpin))


async def unpin_feature_messages(
    context: ContextTypes.DEFAULT_TYPE, messages_to_unpin: list[GroupChatFeaturePinMessage]
) -> None:
    """
    Unpins the feature messages
    :param context: The context
    :param messages_to_unpin: The messages to unpin
    """

    for pin_message in messages_to_unpin:
        group_chat: GroupChat = pin_message.group_chat
        group: Group = group_chat.group
        try:
            await context.bot.unpin_chat_message(group.tg_group_id, pin_message.message_id)
        except TelegramError as te:
            save_group_chat_error(group_chat, str(te))

        pin_message.delete_instance()


def deactivate_inactive_group_chats() -> None:
    """
    Deactivates the inactive groups and group chats
    """

    inactive_days = Env.INACTIVE_GROUP_DAYS.get_int()

    (
        Group.update(is_active=False)
        .where(Group.last_message_date < datetime.now() - timedelta(days=inactive_days))
        .execute()
    )

    (
        GroupChat.update(is_active=False)
        .where(GroupChat.last_message_date < datetime.now() - timedelta(days=inactive_days))
        .execute()
    )

    # Deactivate inactive group users
    deactivate_inactive_group_users()


def deactivate_inactive_group_users() -> None:
    """
    Deactivates the inactive group users
    """

    inactive_days = Env.INACTIVE_GROUP_USER_DAYS.get_int()

    (
        GroupUser.update(is_active=False)
        .where(GroupUser.last_message_date < datetime.now() - timedelta(days=inactive_days))
        .execute()
    )

    (
        User.update(is_active=False)
        .where(User.last_message_date < datetime.now() - timedelta(days=inactive_days))
        .execute()
    )


def save_group_chat_error(group_chat: GroupChat, error: str) -> None:
    """
    Saves the error for the group chat
    :param group_chat: The group chat
    :param error: The error
    """

    group_chat.last_error_date = datetime.now()
    group_chat.last_error_message = error
    group_chat.save()

    group: Group = group_chat.group
    group.last_error_date = datetime.now()
    group.last_error_message = error
    group.save()


async def auto_delete(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Auto delete messages
    :param context: The context
    """

    # Get maximum 20 messages to auto delete
    auto_deletes: list[GroupChatAutoDelete] = (
        GroupChatAutoDelete.select()
        .where(GroupChatAutoDelete.delete_date < datetime.now())
        .limit(20)
    )

    for auto_delete_item in auto_deletes:
        context.application.create_task(auto_delete_process(context, auto_delete_item))


async def auto_delete_process(
    context: ContextTypes.DEFAULT_TYPE, auto_delete_item: GroupChatAutoDelete
) -> None:
    """
    Auto delete process
    :param context: The context
    :param auto_delete_item: The message
    """

    group_chat: GroupChat = auto_delete_item.group_chat

    if _is_message_for_active_challenge(group_chat, auto_delete_item.message_id):
        # Don't delete a challenge message while players are still in the 30-second
        # accept/reject cooldown or actively playing it - defer and check again on the next
        # auto delete run (run_minute_tasks -> auto_delete(), roughly once a minute) instead
        auto_delete_item.delete_date = datetime.now() + timedelta(minutes=1)
        auto_delete_item.save()
        return

    try:
        await delete_message(
            context=context,
            group_chat=group_chat,
            message_id=auto_delete_item.message_id,
            is_auto_delete=True,
        )
    except TelegramError as te:
        save_group_chat_error(group_chat, str(te))

    auto_delete_item.delete_instance()


def _is_message_for_active_challenge(group_chat: GroupChat, message_id: int) -> bool:
    """
    Check if a message is the group invite for a challenge that shouldn't be auto-deleted yet:
    still waiting to be accepted/rejected (or its 30-second confirmation window to expire), or
    still being actively played.

    An open/global challenge (no specific opponent, "Challenge anyone") is the one exception:
    once the challenger uses "Start immediately as global", the game moves to being played in
    private chat, so this group message is safe to delete right away without waiting for that
    game to finish - global_challenger_start_date is only ever set by that action, so its
    presence is used as the signal here
    :param group_chat: The group chat the message is in
    :param message_id: The message id
    :return: True if the message should NOT be auto-deleted yet
    """

    from src.model.Game import Game

    game: Game | None = Game.get_or_none(
        (Game.group_chat == group_chat) & (Game.message_id == message_id)
    )

    if game is None:
        return False

    if game.is_finished():
        return False

    if game.global_challenger_start_date is not None:
        return False

    return True
