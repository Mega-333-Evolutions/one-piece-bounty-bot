from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

import resources.phrases as phrases
from src.model.GroupChat import GroupChat
from src.model.enums.Language import Language
from src.model.enums.Screen import Screen
from src.model.pojo.Keyboard import Keyboard
from src.service.message_service import full_message_send


class LanguageReservedKeys:
    """
    The reserved keys for the language setting screen
    """

    LANGUAGE = "l"


async def manage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    inbound_keyboard: Keyboard,
    group_chat: GroupChat,
) -> None:
    """
    Manage the group language setting screen
    :param update: The update
    :param context: The context
    :param inbound_keyboard: The inbound keyboard
    :param group_chat: The group chat
    :return: None
    """

    group = group_chat.group

    if inbound_keyboard is not None and LanguageReservedKeys.LANGUAGE in inbound_keyboard.info:
        group.language = Language(inbound_keyboard.info[LanguageReservedKeys.LANGUAGE]).value
        group.save()

    inline_keyboard: list[list[Keyboard]] = []
    for language in Language:
        is_current = language == group.get_language()
        prefix = "✅ " if is_current else ""
        button_text = prefix + language.get_flag_emoji() + " " + language.get_name()

        inline_keyboard.append(
            [
                Keyboard(
                    button_text,
                    screen=Screen.GRP_SETTINGS_LANGUAGE,
                    info={LanguageReservedKeys.LANGUAGE: language.value},
                )
            ]
        )

    await full_message_send(
        context,
        phrases.GRP_TXT_SETTINGS_LANGUAGE.format(group.get_language().get_name()),
        update=update,
        keyboard=inline_keyboard,
        inbound_keyboard=inbound_keyboard,
    )
