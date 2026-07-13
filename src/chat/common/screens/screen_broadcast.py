from src.tg_compat import Update, Message
from src.tg_compat.ext import ContextTypes

import resources.phrases as phrases
import src.model.enums.Command as Command
from src.model.User import User
from src.model.enums.CommandName import CommandName
from src.service.broadcast_service import (
    broadcast_to_groups_dispatch,
    broadcast_to_players_dispatch,
)
from src.service.message_service import full_message_send, message_is_reply

PIN_FLAG = "-p"


async def manage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command: Command.Command,
    user: User,
) -> None:
    """
    Manage the owner-only /gcast and /pcast broadcast commands.
    Authorization and private-chat-only restrictions are already enforced before this is
    reached (see is_owner_only_command in manage_message.py and the lack of a group Screen
    for these commands).
    :param update: The update
    :param context: The context
    :param command: The command
    :param user: The owner
    :return: None
    """

    if not message_is_reply(update):
        await full_message_send(context, phrases.BROADCAST_REPLY_REQUIRED, update=update)
        return

    should_pin = PIN_FLAG in command.parameters
    from_chat_id = update.effective_chat.id
    message_id = update.effective_message.reply_to_message.message_id
    is_gcast = command.name is CommandName.GCAST

    progress_message: Message = await full_message_send(
        context,
        phrases.BROADCAST_GROUPS_PROGRESS if is_gcast else phrases.BROADCAST_PLAYERS_PROGRESS,
        update=update,
    )

    if is_gcast:
        await broadcast_to_groups_dispatch(
            context, user, from_chat_id, message_id, should_pin, progress_message.message_id
        )
    else:
        await broadcast_to_players_dispatch(
            context, user, from_chat_id, message_id, should_pin, progress_message.message_id
        )
