from enum import Enum


class BotAdminRight(Enum):
    """
    Whether the bot has an administrator right (e.g. to pin or to delete messages) in a chat
    """

    GRANTED = 1  # The bot has the right
    NOT_ADMIN = 2  # The bot is not an administrator of the chat
    NOT_GRANTED = 3  # The bot is an administrator, but without that right
    UNKNOWN = 4  # Telegram could not tell right now

    def is_granted(self) -> bool:
        """
        :return: True if the bot has the right
        """
        return self is BotAdminRight.GRANTED

    def is_missing(self) -> bool:
        """
        :return: True if it is known that the bot does not have the right
        """
        return self in (BotAdminRight.NOT_ADMIN, BotAdminRight.NOT_GRANTED)
