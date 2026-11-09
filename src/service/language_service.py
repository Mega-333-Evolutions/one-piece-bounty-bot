import contextlib
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


@contextlib.contextmanager
def using_language(language: Language | str | None):
    """
    Generate the phrases inside the block in the given language, then put back the language that
    was set before, whatever happens inside the block (an error included).

    Every message is written in the language of the chat it is sent to: the DM language of the
    user for a private chat and the language of the group for a group chat, no matter who caused
    it. The task that handles an update starts with the language of the user that sent it (and of
    the group, if it came from one), so whatever is written for somebody else (another player, a
    group, a crew mate...) has to be built in a block like this one:

        with using_language(recipient.get_language()):
            text = phrases.SOMETHING.format(...)
            await full_message_send(context, text, chat_id=recipient.tg_user_id)

    :param language: The language to use inside the block. If None, the default language
    :return: None
    """

    previous = _current_language.get()
    set_current_language(language)
    try:
        yield
    finally:
        _current_language.set(previous)
