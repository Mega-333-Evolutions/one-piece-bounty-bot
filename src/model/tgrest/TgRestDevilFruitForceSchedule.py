from src.model.DevilFruit import DevilFruit
from src.model.tgrest.TgRest import TgRest
from src.model.tgrest.TgRestObjectType import TgRestObjectType


class TgRestDevilFruitForceSchedule(TgRest):
    """
    TgRestDevilFruitForceSchedule class is used to create a Telegram REST API request.
    """

    def __init__(
        self,
        bot_id: str,
        object_type: TgRestObjectType,
        devil_fruit_id: int,
    ):
        """
        Constructor

        :param devil_fruit_id: The devil fruit id
        """

        super().__init__(bot_id, object_type)

        self.devil_fruit_id: int = devil_fruit_id
        self.devil_fruit = DevilFruit.get(DevilFruit.id == devil_fruit_id)
