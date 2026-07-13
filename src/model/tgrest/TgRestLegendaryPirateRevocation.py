from src.model.LegendaryPirate import LegendaryPirate
from src.model.User import User
from src.model.tgrest.TgRest import TgRest
from src.model.tgrest.TgRestObjectType import TgRestObjectType


class TgRestLegendaryPirateRevocation(TgRest):
    """
    TgRestLegendaryPirateRevocation class is used to create a Telegram REST API request.
    """

    def __init__(
        self, bot_id: str, object_type: TgRestObjectType, user_id: int, legendary_pirate_id: int
    ):
        """
        Constructor

        :param user_id: The user id
        :param legendary_pirate_id: The legendary pirate id
        """

        super().__init__(bot_id, object_type)

        self.user: User = User.get_by_id(user_id)
        self.legendary_pirate: LegendaryPirate = LegendaryPirate.get_by_id(legendary_pirate_id)
