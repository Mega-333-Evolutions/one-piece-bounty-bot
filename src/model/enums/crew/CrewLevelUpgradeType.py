from enum import StrEnum

from src.utils.LazyPhraseDict import LazyPhraseDict


class CrewLevelUpgradeType(StrEnum):
    MEMBER = "member"
    ABILITY = "ability"

    @staticmethod
    def get_by_level(level: int):
        """
        Returns the upgrade type by level. Even levels increase the member count,
        odd levels increase the ability count
        :param level: The level
        :return: The upgrade type
        """

        return CrewLevelUpgradeType.ABILITY if level % 2 == 1 else CrewLevelUpgradeType.MEMBER

    def get_description(self) -> str:
        """
        Get the description of the upgrade type.
        :return: The description
        """
        return CREW_LEVEL_UPGRADE_TYPE_DESCRIPTIONS[self]


CREW_LEVEL_UPGRADE_TYPE_DESCRIPTIONS = LazyPhraseDict(
    {
        CrewLevelUpgradeType.MEMBER: "CREW_LEVEL_UPGRADE_TYPE_MEMBER",
        CrewLevelUpgradeType.ABILITY: "CREW_LEVEL_UPGRADE_TYPE_ABILITY",
    }
)
