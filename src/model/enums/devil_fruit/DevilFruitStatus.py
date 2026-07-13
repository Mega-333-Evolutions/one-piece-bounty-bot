from enum import IntEnum

from src.utils.LazyPhraseDict import LazyPhraseDict


class DevilFruitStatus(IntEnum):
    """
    Enum for the status of a Devil Fruit
    """

    NEW = 1  # Just created
    COMPLETED = 2  # Abilities added
    ENABLED = 3  # Enabled in the system
    SCHEDULED = 4  # Scheduled to be released
    RELEASED = 5  # Released in the system
    COLLECTED = 6  # Collected by a user
    EATEN = 7  # Eaten by a user

    @staticmethod
    def get_released_statuses() -> list:
        """
        Get the statuses that are released
        :return: The statuses that are released
        """
        return [
            DevilFruitStatus.SCHEDULED,
            DevilFruitStatus.RELEASED,
            DevilFruitStatus.COLLECTED,
            DevilFruitStatus.EATEN,
        ]

    def get_description(self) -> str:
        """
        Get the description of the status
        :return: The description
        """
        return DEVIL_FRUIT_STATUS_DESCRIPTION[self]


DEVIL_FRUIT_STATUS_DESCRIPTION = LazyPhraseDict(
    {
        DevilFruitStatus.NEW: "DEVIL_FRUIT_STATUS_DESCRIPTION_NEW",
        DevilFruitStatus.COMPLETED: "DEVIL_FRUIT_STATUS_DESCRIPTION_COMPLETED",
        DevilFruitStatus.ENABLED: "DEVIL_FRUIT_STATUS_DESCRIPTION_ENABLED",
        DevilFruitStatus.SCHEDULED: "DEVIL_FRUIT_STATUS_DESCRIPTION_SCHEDULED",
        DevilFruitStatus.RELEASED: "DEVIL_FRUIT_STATUS_DESCRIPTION_RELEASED",
        DevilFruitStatus.COLLECTED: "DEVIL_FRUIT_STATUS_DESCRIPTION_COLLECTED",
        DevilFruitStatus.EATEN: "DEVIL_FRUIT_STATUS_DESCRIPTION_EATEN",
    }
)
