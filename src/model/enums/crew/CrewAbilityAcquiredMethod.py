from enum import IntEnum


class CrewAbilityAcquiredMethod(IntEnum):
    """
    How a crew ability was acquired. It is stored in CrewAbility.acquired_method, a SmallIntegerField.

    The values used to be the texts "chosen" and "random": MySQL quietly stored 0 for them, PostgreSQL
    refuses them ("invalid input syntax for type smallint"), so activating an ability did nothing on
    PostgreSQL. A 0 in the database is a row that was saved before this was a number
    """

    CHOSEN = 1
    RANDOM = 2
