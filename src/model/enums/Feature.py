from enum import IntEnum

from src.utils.LazyPhraseDict import LazyPhraseDict


class Feature(IntEnum):
    BOUNTY_GIFT = 1
    CHALLENGE = 3
    CREW = 4
    DEVIL_FRUIT_APPEARANCE = 5
    DOC_Q = 6
    FIGHT = 7
    LEADERBOARD = 8
    MESSAGE_FILTER = 9
    PREDICTION = 10
    SILENCE = 11
    STATUS = 12
    DEVIL_FRUIT_SELL = 13
    BOUNTY_LOAN = 14
    PLUNDER = 15
    DAILY_REWARD = 16

    def get_description(self) -> str:
        """
        Get the description of the feature

        :return: The description of the feature
        """

        return FEATURE_DESCRIPTION_MAP[self]

    @staticmethod
    def get_all() -> list["Feature"]:
        """
        Get all the features

        :return: All the features
        """
        return [
            Feature.BOUNTY_GIFT,
            Feature.CHALLENGE,
            Feature.CREW,
            Feature.DEVIL_FRUIT_APPEARANCE,
            Feature.DOC_Q,
            Feature.FIGHT,
            Feature.LEADERBOARD,
            Feature.MESSAGE_FILTER,
            Feature.PREDICTION,
            Feature.SILENCE,
            Feature.STATUS,
            Feature.DEVIL_FRUIT_SELL,
            Feature.BOUNTY_LOAN,
            Feature.PLUNDER,
            Feature.DAILY_REWARD,
        ]

    @staticmethod
    def get_restricted() -> list["Feature"]:
        """
        Get all the features that are restricted to the main group_chat

        :return: All the features that are restricted
        """
        return [Feature.MESSAGE_FILTER]

    @staticmethod
    def get_non_restricted() -> list["Feature"]:
        """
        Get all the features that are not restricted to the main group_chat

        :return: All the features that are not restricted
        """

        return list(set(Feature.get_all()) - set(Feature.get_restricted()))

    def is_restricted(self) -> bool:
        """
        Checks if the feature is restricted to the main group_chat

        :return: True if the feature is restricted, False otherwise
        """

        return self in Feature.get_restricted()

    @staticmethod
    def get_pinnable() -> list["Feature"]:
        """
        Get all the features that can be pinned

        :return: All the features that can be pinned
        """

        return [Feature.LEADERBOARD, Feature.PREDICTION]

    def is_pinnable(self) -> bool:
        """
        Checks if the feature can be pinned

        :return: True if the feature can be pinned, False otherwise
        """

        return self in Feature.get_pinnable()

    @staticmethod
    def get_disabled_by_default() -> list["Feature"]:
        """
        Get all the features that are disabled by default

        :return: All the features that are disabled by default
        """

        return [Feature.MESSAGE_FILTER]

    def is_enabled_by_default(self) -> bool:
        """
        Checks if the feature is enabled by default

        :return: True if the feature is enabled by default, False otherwise
        """

        return self not in Feature.get_disabled_by_default()

    @staticmethod
    def get_pinned_by_default() -> list["Feature"]:
        """
        Get all the pinnable features that are pinned by default

        :return: All the pinnable features that are pinned by default
        """

        return [Feature.LEADERBOARD]

    def is_pinned_by_default(self) -> bool:
        """
        Checks if the feature is pinned by default

        :return: True if the feature is pinned by default, False otherwise
        """

        return self in Feature.get_pinned_by_default()


FEATURE_DESCRIPTION_MAP = LazyPhraseDict(
    {
        Feature.BOUNTY_GIFT: "FEATURE_BOUNTY_GIFT",
        Feature.CHALLENGE: "FEATURE_CHALLENGE",
        Feature.CREW: "FEATURE_CREW",
        Feature.DEVIL_FRUIT_APPEARANCE: "FEATURE_DEVIL_FRUIT_APPEARANCE",
        Feature.DOC_Q: "FEATURE_DOC_Q",
        Feature.FIGHT: "FEATURE_FIGHT",
        Feature.LEADERBOARD: "FEATURE_LEADERBOARD",
        Feature.MESSAGE_FILTER: "FEATURE_MESSAGE_FILTER",
        Feature.PREDICTION: "FEATURE_PREDICTION",
        Feature.SILENCE: "FEATURE_SILENCE",
        Feature.STATUS: "FEATURE_STATUS",
        Feature.DEVIL_FRUIT_SELL: "FEATURE_DEVIL_FRUIT_SELL",
        Feature.BOUNTY_LOAN: "FEATURE_BOUNTY_LOAN",
        Feature.PLUNDER: "FEATURE_PLUNDER",
        Feature.DAILY_REWARD: "FEATURE_DAILY_REWARD",
    }
)
