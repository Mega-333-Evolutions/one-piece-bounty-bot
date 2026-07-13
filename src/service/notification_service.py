import logging
import traceback

from src.tg_compat import Update, Message
from src.tg_compat.error import Forbidden, BadRequest, TimedOut
from src.tg_compat.ext import ContextTypes

import resources.Environment as Env
import resources.phrases as phrases
from src.model.DisabledNotification import DisabledNotification
from src.model.User import User
from src.model.enums.Notification import Notification
from src.model.enums.Screen import Screen
from src.model.pojo.Keyboard import Keyboard
from src.service.message_service import full_message_send
from src.service.language_service import set_current_language


async def send_notification(
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    notification: Notification,
    should_forward_message: bool = False,
    update: Update = None,
) -> None:
    """
    Sends a notification to the user, fire and forget
    :param context: The context object
    :param user: User
    :param notification: Notification
    :param should_forward_message: If the message of the update should be forwarded
    :param update: The update object
    :return: None
    """

    if user is None:
        logging.error("Trying to send a notification to a None user")
        logging.error(traceback.format_stack())
        return

    if (
        should_forward_message
    ):  # Sync since it's for deleted messages, else no message is forwarded before the deletion
        await send_notification_execute(
            context, user, notification, should_forward_message, update
        )
    else:
        context.application.create_task(
            send_notification_execute(context, user, notification, should_forward_message, update)
        )


async def send_notification_execute(
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    notification: Notification,
    should_forward_message: bool = False,
    update: Update = None,
) -> None:
    """
    Sends a notification to the user
    :param context: The context object
    :param user: User
    :param notification: Notification
    :param should_forward_message: If the message of the update should be forwarded
    :param update: The update object
    :return: None
    """

    from src.chat.private.screens.screen_settings_notifications_type import (
        NotificationTypeReservedKeys,
    )

    set_current_language(user.get_language())

    if should_forward_message and update is None:
        raise ValueError("If should_forward_message is not None, update must be not None")

    # Notification not enabled
    if not is_enabled(user, notification):
        return

    # Not in authorized users
    if (
        Env.LIMIT_TO_AUTHORIZED_USERS.get_bool()
        and user.tg_user_id not in Env.AUTHORIZED_USERS.get_list()
    ):
        return

    # Not in authorized groups
    if Env.LIMIT_TO_AUTHORIZED_GROUPS.get_bool() and not await user.in_authorized_groups(context):
        return

    # Create Keyboard for notification management
    inline_keyboard: list[list[Keyboard]] = []
    previous_screens = [
        Screen.PVT_START,
        Screen.PVT_SETTINGS,
        Screen.PVT_SETTINGS_NOTIFICATIONS,
        Screen.PVT_SETTINGS_NOTIFICATIONS_TYPE,
    ]
    button_info = {
        NotificationTypeReservedKeys.CATEGORY: notification.category,
        NotificationTypeReservedKeys.TYPE: notification.type,
    }

    inline_keyboard += notification.get_keyboard()
    inline_keyboard.append(
        [
            Keyboard(
                phrases.PVT_KEY_MANAGE_NOTIFICATION_SETTINGS,
                info=button_info,
                screen=Screen.PVT_SETTINGS_NOTIFICATIONS_TYPE_EDIT,
                previous_screen_list=previous_screens,
            )
        ]
    )

    try:
        quote_message_id = None
        if should_forward_message:
            try:
                if update is not None and getattr(update, "message", None) is not None:
                    message: Message = await update.message.forward(
                        user.tg_user_id, disable_notification=True
                    )
                    quote_message_id = message.message_id
            
            # --- CRITICAL FIX: Catching Forbidden during forward ---
            except Forbidden: 
                logging.warning(f"Could not forward message to {user.tg_user_id}: User has not started bot in DM or blocked it.")
            # --------------------------------------------------------
            
            except BadRequest as e:
                logging.warning(f"Could not forward message: {e}")
            except Exception:
                logging.error("Unexpected error while forwarding message", exc_info=True)

        await full_message_send(
            context,
            notification.build(),
            chat_id=user.tg_user_id,
            keyboard=inline_keyboard,
            disable_notification=notification.disable_notification,
            reply_to_message_id=quote_message_id,
            disable_web_page_preview=notification.disable_web_page_preview,
            add_delete_button=True,
            should_auto_delete=False,
            authorized_users=[user],
        )
    except Forbidden:  # User has blocked the bot or hasn't started it
        pass
    except TimedOut:  # Transient network timeout - notification will be missed but bot stays alive
        logging.warning(f"Timed out sending notification to user {user.id}")
    except BadRequest as e: # Trying to send a DM to another bot
        if "bot_to_bot" in str(e).lower():
            pass
        else:
            raise e


def is_enabled(user: User, notification: Notification) -> bool:
    """
    Checks if a notification is enabled for a user
    :param user: The user
    :param notification: Notification
    :return: True if the notification is enabled
    """

    return (
        DisabledNotification.get_or_none(
            DisabledNotification.user == user, DisabledNotification.type == notification.type
        )
        is None
    )
