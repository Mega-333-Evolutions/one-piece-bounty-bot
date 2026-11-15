from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

import resources.Environment as Env
import resources.phrases as phrases
from src.model.GroupChat import GroupChat
from src.model.enums.BotAdminRight import BotAdminRight
from src.model.enums.ButtonStyle import ButtonStyle
from src.model.enums.Emoji import Emoji
from src.model.enums.ReservedKeyboardKeys import ReservedKeyboardKeys
from src.model.pojo.Keyboard import Keyboard
from src.service.date_service import convert_minutes_to_duration
from src.service.group_service import get_bot_delete_right
from src.service.list_service import get_options_keyboard
from src.service.message_service import full_message_send


async def manage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    inbound_keyboard: Keyboard,
    group_chat: GroupChat,
) -> None:
    """
    Manage the auto delete screen
    :param update: The update object
    :param context: The context object
    :param inbound_keyboard: The inbound keyboard
    :param group_chat: The group chat
    :return: None
    """

    if ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY in inbound_keyboard.info:
        duration = inbound_keyboard.get(ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY)
        group_chat.auto_delete_duration = duration
        group_chat.save()

        # Auto delete is turned on whatever the Bot is allowed to do: without the permission to
        # delete messages it deletes only its own messages, not the ones that triggered them, and
        # the user is told so in a popup. The popup is not shown if the Bot has the permission
        # (or Telegram could not tell), nor when auto delete is turned off
        if duration is not None:
            delete_right = await get_bot_delete_right(context, group_chat)
            if delete_right.is_missing():
                await full_message_send(
                    context,
                    get_delete_not_available_text(delete_right),
                    update=update,
                    answer_callback=True,
                    show_alert=True,
                )

    current_value = group_chat.auto_delete_duration
    # Create numeric keyboard with all possible values. The selected one is green, the others
    # have no colour
    numeric_keyboard: list[list[Keyboard]] = get_options_keyboard(
        inbound_info=inbound_keyboard.info,
        values=Env.AUTO_DELETE_DURATION_VALUES.get_list(),
        current_selected=current_value,
        current_selected_style=ButtonStyle.SUCCESS,
    )

    # Add "Never" option as first option
    numeric_keyboard.insert(
        0,
        [
            Keyboard(
                (Emoji.RADIO_BUTTON if current_value is None else "") + phrases.TEXT_NEVER,
                info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: None},
                inbound_info=inbound_keyboard.info,
                style=ButtonStyle.SUCCESS if current_value is None else None,
            )
        ],
    )

    ot_text = phrases.AUTO_DELETE_SET.format(
        phrases.TEXT_NEVER if current_value is None else convert_minutes_to_duration(current_value)
    )
    await full_message_send(
        context,
        ot_text,
        update=update,
        keyboard=numeric_keyboard,
        add_delete_button=True,
        use_close_delete=True,
        inbound_keyboard=inbound_keyboard,
        should_auto_delete=False,
    )


def get_delete_not_available_text(delete_right: BotAdminRight) -> str:
    """
    Get the text that tells that the Bot can delete only its own messages
    :param delete_right: Whether the Bot can delete messages of others in the chat (it can't)
    :return: The text
    """

    if delete_right == BotAdminRight.NOT_ADMIN:
        return phrases.AUTO_DELETE_NOT_ADMIN

    return phrases.AUTO_DELETE_NOT_GRANTED
