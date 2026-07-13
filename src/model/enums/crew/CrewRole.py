from enum import IntEnum

from src.utils.LazyPhraseDict import LazyPhraseDict


class CrewRole(IntEnum):
    """
    Enum class for Crew Roles
    """

    CAPTAIN = 1
    FIRST_MATE = 2
    CONSCRIPT = 3

    def get_description(self) -> str:
        """
        Returns the description of the Crew Role
        :return: The description of the Crew Role
        """

        return CREW_ROLE_NAME_MAP[self]


CREW_ROLE_NAME_MAP = LazyPhraseDict(
    {
        CrewRole.CAPTAIN: "CREW_ROLE_CAPTAIN",
        CrewRole.FIRST_MATE: "CREW_ROLE_FIRST_MATE",
        CrewRole.CONSCRIPT: "CREW_ROLE_CONSCRIPT",
    }
)
