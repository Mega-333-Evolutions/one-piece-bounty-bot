from enum import IntEnum

import resources.Environment as Env
from src.utils.LazyPhraseDict import LazyPhraseDict


class GameDifficulty(IntEnum):
    EASY = 1
    MEDIUM = 2
    HARD = 3

    @staticmethod
    def get_from_total_wager(total_wager: int) -> "GameDifficulty":
        """
        Get the game level from the total wager
        :param total_wager: The total wager
        :return: The game level
        """

        if total_wager <= Env.GAME_MAX_TOTAL_WAGER_EASY.get_int():
            return GameDifficulty.EASY

        if total_wager <= Env.GAME_MAX_TOTAL_WAGER_MEDIUM.get_int():
            return GameDifficulty.MEDIUM

        return GameDifficulty.HARD

    def get_name(self) -> str:
        """
        Get the name for this GameDifficulty
        :return: The name
        """
        return GAME_DIFFICULTY_NAME_DICT[self]


GAME_DIFFICULTY_NAME_DICT = LazyPhraseDict(
    {
        GameDifficulty.EASY: "GAME_DIFFICULTY_EASY",
        GameDifficulty.MEDIUM: "GAME_DIFFICULTY_MEDIUM",
        GameDifficulty.HARD: "GAME_DIFFICULTY_HARD",
    }
)
