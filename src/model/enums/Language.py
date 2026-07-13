from enum import StrEnum


class Language(StrEnum):
    """
    Enum for the supported bot languages.
    """

    ENGLISH = "en"
    PERSIAN = "fa"

    def get_name(self) -> str:
        """
        Get the display name of the language, always in its own language
        :return: The display name
        """

        match self:
            case Language.ENGLISH:
                return "English"
            case Language.PERSIAN:
                return "فارسی"

        return self.value

    def get_flag_emoji(self) -> str:
        """
        Get the flag emoji of the language
        :return: The flag emoji
        """

        match self:
            case Language.ENGLISH:
                return "🇬🇧"
            case Language.PERSIAN:
                return "🇮🇷"

        return ""


LANGUAGE_DEFAULT = Language.ENGLISH
