from resources import phrases
from src.model.error.ErrorSource import ErrorSource


class Error:
    """
    Error class
    """

    def __init__(self, code, message, source: ErrorSource, only_message: bool = False):
        """
        :param message: Either a phrases.py constant name (str) to be resolved lazily in the
        currently active language, or an already resolved message text
        """
        self.code = code
        self.message = message
        self.source = source
        self.only_message = only_message

    def get_message(self) -> str:
        """
        Resolve the message, translating it if it's a phrases.py constant name
        :return: The resolved message
        """

        if isinstance(self.message, str) and hasattr(phrases, self.message):
            return getattr(phrases, self.message)

        return self.message

    def __str__(self):
        if self.only_message:
            return self.get_message()

        result = f"Error " + self.source + str(self.code) + ": " + self.get_message()
        result += phrases.FORWARD_TO_SUPPORT_GROUP

        return result

    def build(self):
        return str(self)
