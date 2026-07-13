from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

import resources.phrases as phrases
from src.model.User import User
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
    update: Update, context: ContextTypes.DEFAULT_TYPE, inbound_keyboard: Keyboard, user: User
) -> None:
    """
    Manage the language setting screen
    :param update: The update
    :param context: The context
    :param inbound_keyboard: The inbound keyboard
    :param user: The user
    :return: None
    """

    if inbound_keyboard is not None and LanguageReservedKeys.LANGUAGE in inbound_keyboard.info:
        user.language = Language(inbound_keyboard.info[LanguageReservedKeys.LANGUAGE]).value

    inline_keyboard: list[list[Keyboard]] = []
    for language in Language:
        is_current = language == user.get_language()
        prefix = "✅ " if is_current else ""
        button_text = prefix + language.get_flag_emoji() + " " + language.get_name()

        inline_keyboard.append(
            [
                Keyboard(
                    button_text,
                    screen=Screen.PVT_SETTINGS_LANGUAGE,
                    info={LanguageReservedKeys.LANGUAGE: language.value},
                )
            ]
        )

    await full_message_send(
        context,
        phrases.PVT_TXT_SETTINGS_LANGUAGE.format(user.get_language().get_name()),
        update=update,
        keyboard=inline_keyboard,
        inbound_keyboard=inbound_keyboard,
        previous_screens=user.get_private_screen_list()[:-1],
    )
