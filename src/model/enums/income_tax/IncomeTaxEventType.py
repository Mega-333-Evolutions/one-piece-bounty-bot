from enum import StrEnum

from src.utils.LazyPhraseDict import LazyPhraseDict
from src.model.enums.LogType import LogType


class IncomeTaxEventType(StrEnum):
    BOUNTY_GIFT = "bounty_gift"
    BOUNTY_LOAN = "bounty_loan"
    DEVIL_FRUIT_SELL = "devil_fruit_sell"
    DOC_Q_GAME = "doc_q_game"
    FIGHT = "fight"
    GAME = "game"
    PREDICTION = "prediction"
    PLUNDER = "plunder"
    DAVY_BACK_FIGHT = "davy_back_fight"

    def get_description(self) -> str:
        """
        Get the description of the income tax event type
        :return: The description
        """

        return INCOME_TAX_EVENT_TYPE_DESCRIPTIONS[self]

    def get_log_type(self) -> LogType | None:
        """
        Get the log type of the income tax event type
        :return: The log type
        """

        if self not in INCOME_TAX_EVENT_TYPE_LOG_TYPE:
            return None

        return INCOME_TAX_EVENT_TYPE_LOG_TYPE[self]


INCOME_TAX_EVENT_TYPE_DESCRIPTIONS = LazyPhraseDict(
    {
        IncomeTaxEventType.BOUNTY_GIFT: "BOUNTY_GIFT_LOG_ITEM_DETAIL_TEXT_FILL_IN",
        IncomeTaxEventType.BOUNTY_LOAN: "INCOME_TAX_EVENT_BOUNTY_LOAN",
        IncomeTaxEventType.DEVIL_FRUIT_SELL: "INCOME_TAX_EVENT_DEVIL_FRUIT_SELL",
        IncomeTaxEventType.DOC_Q_GAME: "DOC_Q_GAME_LOG_ITEM_DETAIL_TEXT_FILL_IN",
        IncomeTaxEventType.FIGHT: "FIGHT_LOG_ITEM_DETAIL_TEXT_FILL_IN",
        IncomeTaxEventType.GAME: "GAME_LOG_ITEM_DETAIL_TEXT_FILL_IN",
        IncomeTaxEventType.PREDICTION: "PREDICTION_ITEM_TEXT_FILL_IN",
        IncomeTaxEventType.PLUNDER: "PLUNDER_LOG_ITEM_DETAIL_TEXT_FILL_IN",
        IncomeTaxEventType.DAVY_BACK_FIGHT: "CREW_DAVY_BACK_FIGHT_ITEM_TEXT_FILL_IN",
    }
)

INCOME_TAX_EVENT_TYPE_LOG_TYPE = {
    IncomeTaxEventType.BOUNTY_GIFT: LogType.BOUNTY_GIFT,
    IncomeTaxEventType.DOC_Q_GAME: LogType.DOC_Q_GAME,
    IncomeTaxEventType.FIGHT: LogType.FIGHT,
    IncomeTaxEventType.GAME: LogType.GAME,
    IncomeTaxEventType.PLUNDER: LogType.PLUNDER,
}
