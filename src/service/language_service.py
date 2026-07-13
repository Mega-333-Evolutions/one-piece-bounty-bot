import contextvars

from src.model.enums.Language import Language, LANGUAGE_DEFAULT

# Holds the language that should be used for any phrase generated in the current
# asyncio Task (e.g. the Task handling a single Telegram update, or a Task created
# to send a single notification/broadcast message). Every asyncio Task gets its own
# copy of the context, so setting this in one Task never affects another Task that
# is running concurrently.
_current_language: contextvars.ContextVar[Language] = contextvars.ContextVar(
    "current_language", default=LANGUAGE_DEFAULT
)


def set_current_language(language: Language | str | None) -> None:
    """
    Set the language to use for phrases generated for the remainder of the current task
    :param language: The language to set. If None, defaults to the default language
    :return: None
    """

    if language is None:
        language = LANGUAGE_DEFAULT
    elif not isinstance(language, Language):
        language = Language(language)

    _current_language.set(language)


def get_current_language() -> Language:
    """
    Get the language currently set for this task
    :return: The current language
    """

    return _current_language.get()
