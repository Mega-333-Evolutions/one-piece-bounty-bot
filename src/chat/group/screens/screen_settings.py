from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

import resources.phrases as phrases
from src.model.enums.Screen import Screen
from src.model.pojo.Keyboard import Keyboard
from src.service.message_service import full_message_send


async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Manage the settings screen
    :param update: The update
    :param context: The context
    :return: None
    """

    inline_keyboard: list[list[Keyboard]] = [
        # Features
        [Keyboard(phrases.GRP_KEY_SETTINGS_FEATURES, screen=Screen.GRP_SETTINGS_FEATURES)],
        # Auto delete
        [Keyboard(phrases.GRP_KEY_SETTINGS_AUTO_DELETE, screen=Screen.GRP_SETTINGS_AUTO_DELETE)],
        # Language
        [Keyboard(phrases.GRP_KEY_SETTINGS_LANGUAGE, screen=Screen.GRP_SETTINGS_LANGUAGE)],
    ]

    await full_message_send(
        context,
        phrases.TXT_SETTINGS,
        update=update,
        keyboard=inline_keyboard,
        add_delete_button=True,
        use_close_delete=True,
        should_auto_delete=False,
    )
