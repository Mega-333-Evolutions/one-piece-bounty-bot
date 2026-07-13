from enum import StrEnum


class CommandName(StrEnum):
    EMPTY = ""
    START = "start"
    STATUS = "status"
    DOC_Q = "docq"
    NEW_WORLD = "newworld"
    PARADISE = "paradise"
    FIGHT = "fight"
    GAME = "challenge"
    PREDICTION_BET = "bet"
    PREDICTION_BET_REMOVE = "bremove"
    PREDICTION_BET_STATUS = "bstatus"
    CREW_JOIN = "join"
    CREW_INVITE = "invite"
    SILENCE = "silence"
    SILENCE_END = "silenceend"
    SPEAK = "speak"
    BOUNTY_GIFT = "gift"
    BOUNTY_LOAN = "loan"
    DEVIL_FRUIT_SELL = "dfsell"
    PLUNDER = "steal"
    SETTINGS = "settings"
    DAILY_REWARD = "reward"
    ADD_BOUNTY = "add"
    TAKE_BOUNTY = "take"
    REVERT_PENDING_BOUNTY = "rpending"
    REVERT_PENDING_BOUNTY_ALL = "rpendingall"
    GCAST = "gcast"
    PCAST = "pcast"

    def get_formatted(self):
        """
        Returns the command formatted for the text display.
        """
        return "`/{}`".format(self)

    def get_non_formatted(self):
        """
        Returns the command formatted for the text display.
        """
        return "/{}".format(self)
