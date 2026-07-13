from datetime import datetime
from enum import IntEnum

import resources.Environment as Env
from resources import phrases
from src.utils.LazyPhraseDict import LazyPhraseDict
import src.model.enums.Location as Location
from src.model.BountyLoan import BountyLoan
from src.model.Crew import Crew
from src.model.CrewAbility import CrewAbility
from src.model.DavyBackFight import DavyBackFight
from src.model.DavyBackFightParticipant import DavyBackFightParticipant
from src.model.DevilFruit import DevilFruit
from src.model.DevilFruitTrade import DevilFruitTrade
from src.model.Fight import Fight
from src.model.Game import Game
from src.model.ImpelDownLog import ImpelDownLog
from src.model.Plunder import Plunder
from src.model.Prediction import Prediction
from src.model.PredictionOption import PredictionOption
from src.model.PredictionOptionUser import PredictionOptionUser
from src.model.User import User
from src.model.Warlord import Warlord
from src.model.LegendaryPirate import LegendaryPirate
from src.model.enums.Emoji import Emoji
from src.model.enums.GameStatus import GameStatus
from src.model.enums.Log import Log
from src.model.enums.LogType import LogType
from src.model.enums.ReservedKeyboardKeys import ReservedKeyboardKeys, LogTypeReservedKeys
from src.model.enums.Screen import Screen
from src.model.enums.impel_down.ImpelDownBountyAction import ImpelDownBountyAction
from src.model.enums.impel_down.ImpelDownSentenceType import ImpelDownSentenceType
from src.model.game.GameType import GameType
from src.model.pojo.Keyboard import Keyboard
from src.service.date_service import (
    default_datetime_format,
    convert_days_to_duration,
    get_remaining_time_in_days,
)
from src.service.date_service import get_remaining_duration
from src.service.message_service import (
    get_image_preview,
    escape_valid_markdown_chars,
    mention_markdown_user,
    get_message_url,
)
from src.utils.math_utils import format_percentage_value
from src.utils.string_utils import get_belly_formatted


class NotificationCategory(IntEnum):
    """Enum for different categories of notifications"""

    CREW = 1
    LOCATION = 2
    GAME = 3
    IMPEL_DOWN = 4
    PREDICTION = 5
    DELETED_MESSAGE = 6
    BOUNTY_GIFT = 7
    DEVIL_FRUIT = 8
    BOUNTY_LOAN = 9
    WARLORD = 10
    DAVY_BACK_FIGHT = 11
    FIGHT = 12
    PLUNDER = 13
    LEGENDARY_PIRATE = 14


NOTIFICATION_CATEGORY_DESCRIPTIONS = LazyPhraseDict(
    {
        NotificationCategory.CREW: "NOTIFICATION_CATEGORY_CREW",
        NotificationCategory.LOCATION: "NOTIFICATION_CATEGORY_LOCATION",
        NotificationCategory.GAME: "NOTIFICATION_CATEGORY_GAME",
        NotificationCategory.IMPEL_DOWN: "NOTIFICATION_CATEGORY_IMPEL_DOWN",
        NotificationCategory.PREDICTION: "NOTIFICATION_CATEGORY_PREDICTION",
        NotificationCategory.DELETED_MESSAGE: "NOTIFICATION_CATEGORY_DELETED_MESSAGE",
        NotificationCategory.BOUNTY_GIFT: "NOTIFICATION_CATEGORY_BOUNTY_GIFT",
        NotificationCategory.DEVIL_FRUIT: "NOTIFICATION_CATEGORY_DEVIL_FRUIT",
        NotificationCategory.BOUNTY_LOAN: "NOTIFICATION_CATEGORY_BOUNTY_LOAN",
        NotificationCategory.WARLORD: "NOTIFICATION_CATEGORY_WARLORD",
        NotificationCategory.DAVY_BACK_FIGHT: "NOTIFICATION_CATEGORY_DAVY_BACK_FIGHT",
        NotificationCategory.FIGHT: "NOTIFICATION_CATEGORY_FIGHT",
        NotificationCategory.PLUNDER: "NOTIFICATION_CATEGORY_PLUNDER",
        NotificationCategory.LEGENDARY_PIRATE: "NOTIFICATION_CATEGORY_LEGENDARY_PIRATE",
    }
)


class NotificationType(IntEnum):
    """Enum for the different types of notifications."""

    CREW_LEAVE = 1
    LOCATION_UPDATE = 2
    CREW_DISBAND = 3
    CREW_DISBAND_WARNING = 4
    GAME_TURN = 5
    CREW_MEMBER_REMOVE = 6
    IMPEL_DOWN_RESTRICTION_PLACED = 7
    IMPEL_DOWN_RESTRICTION_REMOVED = 8
    PREDICTION_RESULT = 9
    PREDICTION_BET_INVALID = 10
    DELETED_MESSAGE_ARREST = 11
    DELETED_MESSAGE_MUTE = 12
    DELETED_MESSAGE_LOCATION = 13
    BOUNTY_GIFT_RECEIVED = 14
    DEVIL_FRUIT_AWARDED = 15
    DEVIL_FRUIT_EXPIRED = 16
    DEVIL_FRUIT_REVOKE_WARNING = 17
    DEVIL_FRUIT_REVOKE = 18
    BOUNTY_LOAN_PAYMENT = 19
    BOUNTY_LOAN_FORGIVEN = 20
    BOUNTY_LOAN_EXPIRED = 21
    WARLORD_APPOINTMENT = 22
    WARLORD_REVOCATION = 23
    CREW_ABILITY_ACTIVATED = 24
    CREW_FIRST_MATE_PROMOTION = 25
    CREW_FIRST_MATE_DEMOTION = 26
    CREW_JOIN_REQUEST_ACCEPTED = 27
    CREW_JOIN_REQUEST_REJECTED = 28
    IMPEL_DOWN_BAIL_POSTED = 29
    DAVY_BACK_FIGHT_REQUEST_ACCEPTED = 30
    DAVY_BACK_FIGHT_REQUEST_REJECTED = 31
    DAVY_BACK_FIGHT_START = 32
    DAVY_BACK_FIGHT_END = 33
    CREW_CONSCRIPTION_START = 34
    CREW_CONSCRIPTION_START_CAPTAIN = 35
    CREW_CONSCRIPTION_END = 36
    DEVIL_FRUIT_SOLD = 37
    CREW_CAPTAIN_PROMOTION = 38
    FIGHT_ATTACK = 39
    PLUNDER_ATTACK = 40
    GAME_OUTCOME = 41
    LEGENDARY_PIRATE_APPOINTMENT = 42
    LEGENDARY_PIRATE_REVOCATION = 43


class Notification:
    """Class for notifications."""

    def __init__(
        self,
        category: NotificationCategory,
        notification_type: NotificationType,
        text: str,
        description: str,
        button_text: str,
        disable_web_page_preview: bool = True,
        disable_notification: bool = True,
        item_screen: Screen = None,
        item_info: dict = None,
        go_to_item_button_text: str = None,
        item_previous_screens: list[Screen] = None,
        item_button_is_deeplink: bool = False,
        keyboard: list[list[Keyboard]] = None,
    ):
        """
        Constructor

        :param category: Category of the notification
        :param notification_type: The type of notification
        :param text: Base text that will be sent
        :param description: Description of the notification to be provided in settings
        :param button_text: Text for the button to change the notification settings
        :param disable_web_page_preview: True if the web page preview should be disabled
        :param disable_notification: True if telegram should not notify of the message
        :param item_screen: The screen of the item that is related to this notification
        :param item_info: The info of the item that is related to this notification
        :param go_to_item_button_text: The text for the button to go to the item
        :param item_previous_screens: The previous screens of the item
        :param item_button_is_deeplink: True if the item button is a deeplink
        :param keyboard: The keyboard
        """

        self.category = category
        self.type = notification_type
        self._text_key = text
        self._description_key = description
        self._button_text_key = button_text
        self.disable_web_page_preview = disable_web_page_preview
        self.disable_notification = disable_notification
        self.item_screen = item_screen
        self.item_info = item_info
        self._go_to_item_button_text_key = go_to_item_button_text
        self.item_previous_screens = item_previous_screens if item_previous_screens else []
        self.item_button_is_deeplink = item_button_is_deeplink
        self.keyboard = keyboard if keyboard else []

    @staticmethod
    def _resolve(value: str) -> str:
        """
        Resolves a phrases.py constant name to its value in the currently active language.
        If the value isn't a known constant name (e.g. it's already resolved text, or an
        empty string), it's returned unchanged.
        """

        if isinstance(value, str) and hasattr(phrases, value):
            return getattr(phrases, value)

        return value

    @property
    def text(self) -> str:
        """Base text that will be sent, resolved in the currently active language"""
        return self._resolve(self._text_key)

    @text.setter
    def text(self, value: str) -> None:
        self._text_key = value

    @property
    def description(self) -> str:
        """Description of the notification, resolved in the currently active language"""
        return self._resolve(self._description_key)

    @property
    def button_text(self) -> str:
        """Text for the button to change the notification settings"""
        return self._resolve(self._button_text_key)

    @property
    def go_to_item_button_text(self) -> str | None:
        """Text for the button to go to the item, resolved in the currently active language"""
        if self._go_to_item_button_text_key is None:
            return None

        return self._resolve(self._go_to_item_button_text_key)

    def build(self):
        """Builds the notification."""

        return self.text

    def get_go_to_item_keyboard(self) -> list[Keyboard]:
        """Gets the go to item keyboard."""

        if self.item_screen is None or self.go_to_item_button_text is None:
            return []

        return [
            Keyboard(
                self.go_to_item_button_text,
                screen=self.item_screen,
                info=self.item_info,
                previous_screen_list=self.item_previous_screens,
                from_deeplink=self.item_button_is_deeplink,
            )
        ]

    def get_keyboard(self) -> list[list[Keyboard]]:
        """Gets the keyboard."""

        return self.keyboard + [self.get_go_to_item_keyboard()]


class CrewLeaveNotification(Notification):
    """Class for crew leave notifications."""

    def __init__(self, crew_member: User = None):
        """
        :param crew_member: Member of the crew that left
        """

        self.crew_member = crew_member
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_LEAVE,
            "CREW_LEAVE_NOTIFICATION",
            "CREW_LEAVE_NOTIFICATION_DESCRIPTION",
            "CREW_LEAVE_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification."""

        return self.text.format(mention_markdown_user(self.crew_member))


class LocationUpdateNotification(Notification):
    """Class for location update notifications."""

    def __init__(self, user: User = None, location: Location = None):
        """
        :param user: User
        :param location: The new location
        """

        self.user = user
        self.location = location
        super().__init__(
            NotificationCategory.LOCATION,
            NotificationType.LOCATION_UPDATE,
            "LOCATION_UPDATE_NOTIFICATION",
            "LOCATION_UPDATE_NOTIFICATION_DESCRIPTION",
            "LOCATION_UPDATE_NOTIFICATION_KEY",
            disable_web_page_preview=False,
        )

    def build(self) -> str:
        """Builds the notification."""

        from src.utils.string_utils import get_belly_formatted

        location: Location = self.location
        # Determine preposition to use for the location
        if "island" in location.name.lower() or "archipelago" in location.name.lower():
            preposition = "on"
            if location.name.lower().startswith("island"):
                preposition += " the"
        else:
            preposition = "in"

        # Determine text suffix
        try:
            next_location = Location.get_by_level(location.level + 1)
            text_suffix = phrases.LOCATION_NEXT_LEVEL_REQUIREMENT.format(
                get_belly_formatted(next_location.required_bounty)
            )
        except ValueError:
            text_suffix = phrases.LOCATION_CURRENT_LEVEL_MAX

        return self.text.format(
            get_image_preview(location.image_url),
            mention_markdown_user(self.user),
            preposition,
            escape_valid_markdown_chars(location.name),
            text_suffix,
        )


class CrewDisbandNotification(Notification):
    """Class for crew disband notifications."""

    def __init__(self):
        """Constructor"""

        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_DISBAND,
            "CREW_DISBAND_NOTIFICATION",
            "CREW_DISBAND_NOTIFICATION_DESCRIPTION",
            "CREW_DISBAND_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification."""

        return self.text


class CrewDisbandWarningNotification(Notification):
    """Class for crew disband warning notifications."""

    def __init__(self):
        """Constructor"""

        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_DISBAND_WARNING,
            "CREW_DISBAND_WARNING_NOTIFICATION",
            "CREW_DISBAND_WARNING_NOTIFICATION_DESCRIPTION",
            "CREW_DISBAND_WARNING_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification."""
        from src.service.bounty_service import get_duration_to_next_bounty_reset

        return self.text.format(get_duration_to_next_bounty_reset())


class GameTurnNotification(Notification):
    """Class for game turn notifications."""

    def __init__(self, game: Game = None, opponent: User = None):
        """Constructor

        :param game: The game
        :param opponent: The opponent whose turn it's not
        """

        self.game = game
        self.opponent = opponent
        super().__init__(
            NotificationCategory.GAME,
            NotificationType.GAME_TURN,
            "GAME_TURN_NOTIFICATION",
            "GAME_TURN_NOTIFICATION_DESCRIPTION",
            "GAME_TURN_NOTIFICATION_KEY",
            disable_notification=False,
        )

    def build(self) -> str:
        """Builds the notification."""
        from src.service.game_service import get_auto_move_warning

        return self.text.format(
            GameType(self.game.type).get_name(),
            mention_markdown_user(self.opponent),
            get_message_url(self.game.message_id, self.game.group_chat),
            get_auto_move_warning(),
        )


class CrewMemberRemoveNotification(Notification):
    """Class for crew member remove notifications."""

    def __init__(self, crew_member: User = None):
        """Constructor

        :param crew_member: The crew member that was removed
        """

        self.crew_member = crew_member
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_MEMBER_REMOVE,
            "CREW_MEMBER_REMOVE_NOTIFICATION",
            "CREW_MEMBER_REMOVE_NOTIFICATION_DESCRIPTION",
            "CREW_MEMBER_REMOVE_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification"""

        return self.text.format(mention_markdown_user(self.crew_member))


class ImpelDownNotificationRestrictionPlaced(Notification):
    """Class for impel down restriction place notifications."""

    def __init__(
        self,
        sentence_type: ImpelDownSentenceType = None,
        release_date_time: datetime = None,
        bounty_action: ImpelDownBountyAction = None,
        reason: str = None,
        impel_down_log: ImpelDownLog = None,
    ):
        """
        Constructor

        :param sentence_type: The sentence type
        :param release_date_time: The release date time
        :param bounty_action: The bounty action
        :param reason: The reason
        :param impel_down_log: The impel down log
        """

        from src.service.impel_down_service import get_post_bail_deeplink_button

        self.sentence_type = sentence_type
        self.release_date_time = release_date_time
        self.bounty_action = bounty_action
        self.reason = reason
        self.impel_down_log = impel_down_log

        post_bail_button = get_post_bail_deeplink_button(impel_down_log)
        keyboard = [[post_bail_button]] if post_bail_button is not None else []

        super().__init__(
            NotificationCategory.IMPEL_DOWN,
            NotificationType.IMPEL_DOWN_RESTRICTION_PLACED,
            "IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION",
            "IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_DESCRIPTION",
            "IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_KEY",
            keyboard=keyboard,
        )

    def build(self) -> str:
        """Builds the notification"""

        restriction_text = ""
        duration_text = ""
        bail_text = ""

        # Bounty action
        if self.bounty_action is ImpelDownBountyAction.HALVE:
            restriction_text += phrases.IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_BOUNTY_HALVED
        elif self.bounty_action is ImpelDownBountyAction.ERASE:
            restriction_text += phrases.IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_BOUNTY_ERASED

        # Sentence type
        if self.sentence_type is not ImpelDownSentenceType.NONE:
            restriction_text += phrases.IMPEL_DOWN_RESTRICTIONS

            duration_text = phrases.IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_DURATION.format(
                get_remaining_duration(self.release_date_time)
                if self.sentence_type is ImpelDownSentenceType.TEMPORARY
                else phrases.IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_DURATION_PERMANENT
            )

            if self.sentence_type is ImpelDownSentenceType.TEMPORARY:
                bail_text = phrases.IMPEL_DOWN_RESTRICTION_BAIL_GUIDE

        return self.text.format(
            escape_valid_markdown_chars(self.reason), restriction_text, duration_text, bail_text
        )


class ImpelDownNotificationRestrictionRemoved(Notification):
    """Class for impel down restriction remove notifications."""

    def __init__(self):
        """Constructor"""

        super().__init__(
            NotificationCategory.IMPEL_DOWN,
            NotificationType.IMPEL_DOWN_RESTRICTION_REMOVED,
            "IMPEL_DOWN_RESTRICTION_REMOVED_NOTIFICATION",
            "IMPEL_DOWN_RESTRICTION_REMOVED_NOTIFICATION_DESCRIPTION",
            "IMPEL_DOWN_RESTRICTION_REMOVED_NOTIFICATION_KEY",
        )


class PredictionResultNotification(Notification):
    """Class for prediction result notifications."""

    def __init__(
        self,
        prediction: Prediction = None,
        prediction_options: list[PredictionOption] = None,
        correct_prediction_options: list[PredictionOption] = None,
        total_win: int = None,
        user: User = None,
    ):
        """
        Constructor

        :param prediction: The prediction
        :param prediction_options: The prediction options that were chosen by the user
        :param correct_prediction_options: The correct prediction options
        :param total_win: The total win
        :param user: The user
        """

        self.prediction = prediction
        self.prediction_options = prediction_options
        self.correct_prediction_options = correct_prediction_options
        self.total_win = total_win
        self.user = user

        super().__init__(
            NotificationCategory.PREDICTION,
            NotificationType.PREDICTION_RESULT,
            "PREDICTION_RESULT_NOTIFICATION",
            "PREDICTION_RESULT_NOTIFICATION_DESCRIPTION",
            "PREDICTION_RESULT_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification"""

        from src.utils.string_utils import get_belly_formatted
        from src.service.prediction_service import get_max_wager_refund

        # Result text
        result_text = phrases.TEXT_WON if self.total_win >= 0 else phrases.TEXT_LOST

        # User prediction options
        user_prediction_options_list = ""
        for option in self.prediction_options:
            option_emoji = Emoji.LOG_POSITIVE if option.is_correct else Emoji.LOG_NEGATIVE
            user_prediction_options_list += phrases.PREDICTION_RESULT_NOTIFICATION_OPTION.format(
                option_emoji, escape_valid_markdown_chars(option.option)
            )
        phrase_to_use = (
            phrases.PREDICTION_RESULT_NOTIFICATION_YOUR_OPTION
            if len(self.prediction_options) == 1
            else phrases.PREDICTION_RESULT_NOTIFICATION_YOUR_OPTIONS
        )
        user_prediction_options_text = phrase_to_use.format(user_prediction_options_list)

        prediction_has_correct_options = len(self.correct_prediction_options) > 0
        # Correct prediction options
        prediction_has_multiple_options = (
            len(self.correct_prediction_options) > 0 or len(self.prediction_options) > 0
        )
        user_got_the_only_correct_option = (
            len(self.correct_prediction_options) == 1
            and len([option for option in self.prediction_options if option.is_correct]) == 1
        )

        # Show correct options list if:
        # - Prediction has at least one correct option
        # - Prediction has multiple options or didn't get the only correct option
        correct_prediction_options_text = ""
        if prediction_has_correct_options and (
            prediction_has_multiple_options and not user_got_the_only_correct_option
        ):
            correct_prediction_options_list = ""
            for option in self.correct_prediction_options:
                correct_prediction_options_list += (
                    phrases.PREDICTION_RESULT_NOTIFICATION_OPTION_NO_EMOJI.format(
                        escape_valid_markdown_chars(option.option)
                    )
                )
            correct_prediction_options_text = (
                phrases.PREDICTION_RESULT_NOTIFICATION_CORRECT_OPTIONS.format(
                    correct_prediction_options_list
                )
            )

        # Wager refunded notice
        wager_refunded_text = ""
        if not prediction_has_correct_options:
            wager_refunded_text = (
                phrases.PREDICTION_RESULT_NOTIFICATION_WAGER_REFUNDED_NO_CORRECT_OPTIONS
            )
        elif self.prediction.refund_wager:
            max_refund_wager = get_max_wager_refund(prediction=self.prediction, user=self.user)
            # User lost more than the refundable amount
            if self.total_win < 0 and abs(self.total_win) > max_refund_wager:  #
                wager_refunded_text = (
                    phrases.PREDICTION_RESULT_NOTIFICATION_WAGER_REFUNDED_PARTIAL.format(
                        get_belly_formatted(max_refund_wager)
                    )
                )
            else:
                wager_refunded_text = phrases.PREDICTION_RESULT_NOTIFICATION_WAGER_REFUNDED

        return self.text.format(
            result_text,
            get_belly_formatted(abs(self.total_win)),
            escape_valid_markdown_chars(self.prediction.question),
            user_prediction_options_text,
            correct_prediction_options_text,
            wager_refunded_text,
        )


class PredictionBetInvalidNotification(Notification):
    """Class for invalid prediction bet notifications."""

    def __init__(
        self,
        prediction: Prediction = None,
        prediction_options_user: list[PredictionOptionUser] = None,
        total_refund: int = None,
    ):
        """
        Constructor

        :param prediction: The prediction
        :param prediction_options_user: The invalid prediction options that were chosen by the user
        :param total_refund: The total refund
        """

        self.prediction = prediction
        self.prediction_options_user = prediction_options_user
        self.total_refund = total_refund

        super().__init__(
            NotificationCategory.PREDICTION,
            NotificationType.PREDICTION_BET_INVALID,
            "PREDICTION_BET_INVALID_NOTIFICATION",
            "PREDICTION_BET_INVALID_NOTIFICATION_DESCRIPTION",
            "PREDICTION_BET_INVALID_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        from src.utils.string_utils import get_belly_formatted

        if len(self.prediction_options_user) == 1:
            bet_has = phrases.PREDICTION_BET_INVALID_BET_HAS
            it_was = phrases.TEXT_IT_WAS
        else:
            bet_has = phrases.PREDICTION_BET_INVALID_BETS_HAVE
            it_was = phrases.TEXT_THEY_WERE

        invalid_prediction_options_list = ""
        for prediction_option_user in self.prediction_options_user:
            prediction_option: PredictionOption = prediction_option_user.prediction_option
            invalid_prediction_options_list += (
                phrases.PREDICTION_BET_INVALID_NOTIFICATION_OPTION.format(
                    escape_valid_markdown_chars(prediction_option.option),
                    default_datetime_format(prediction_option_user.date),
                )
            )

        return self.text.format(
            bet_has,
            escape_valid_markdown_chars(self.prediction.question),
            it_was,
            default_datetime_format(self.prediction.cut_off_date),
            invalid_prediction_options_list,
            get_belly_formatted(self.total_refund),
        )


class DeletedMessageArrestNotification(Notification):
    """Class for deleted messages because user is arrested notifications."""

    def __init__(self):
        """Constructor"""

        super().__init__(
            NotificationCategory.DELETED_MESSAGE,
            NotificationType.DELETED_MESSAGE_ARREST,
            "DELETED_MESSAGE_ARREST_NOTIFICATION",
            "DELETED_MESSAGE_ARREST_NOTIFICATION_DESCRIPTION",
            "DELETED_MESSAGE_ARREST_NOTIFICATION_KEY",
            disable_notification=False,
        )


class DeletedMessageMuteNotification(Notification):
    """Class for deleted messages because user is muted notifications."""

    def __init__(self):
        """Constructor"""

        super().__init__(
            NotificationCategory.DELETED_MESSAGE,
            NotificationType.DELETED_MESSAGE_MUTE,
            "DELETED_MESSAGE_MUTE_NOTIFICATION",
            "DELETED_MESSAGE_MUTE_NOTIFICATION_DESCRIPTION",
            "DELETED_MESSAGE_MUTE_NOTIFICATION_KEY",
            disable_notification=False,
        )


class DeletedMessageLocationNotification(Notification):
    """
    Class for deleted messages because user has not reached the required location notifications.
    """

    def __init__(self, user: User = None, required_location_level: int = None):
        """
        Constructor

        :param user: The user
        :param required_location_level: The required location level
        """

        self.user = user
        self.required_location_level = required_location_level

        super().__init__(
            NotificationCategory.DELETED_MESSAGE,
            NotificationType.DELETED_MESSAGE_LOCATION,
            "DELETED_MESSAGE_LOCATION_NOTIFICATION",
            "DELETED_MESSAGE_LOCATION_NOTIFICATION_DESCRIPTION",
            "DELETED_MESSAGE_LOCATION_NOTIFICATION_KEY",
            disable_notification=False,
        )

    def build(self) -> str:
        current_location: Location = Location.get_by_level(self.user.location_level)
        required_location: Location = Location.get_by_level(self.required_location_level)
        return self.text.format(
            escape_valid_markdown_chars(current_location.name),
            escape_valid_markdown_chars(required_location.name),
        )


class BountyGiftReceivedNotification(Notification):
    """Class for bounty gift received notifications."""

    def __init__(self, sender: User = None, amount: int = None):
        """
        Constructor

        :param sender: The sender
        :param amount: The amount
        """

        self.sender = sender
        self.amount = amount

        super().__init__(
            NotificationCategory.BOUNTY_GIFT,
            NotificationType.BOUNTY_GIFT_RECEIVED,
            "BOUNTY_GIFT_RECEIVED_NOTIFICATION",
            "BOUNTY_GIFT_RECEIVED_NOTIFICATION_DESCRIPTION",
            "BOUNTY_GIFT_RECEIVED_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        from src.utils.string_utils import get_belly_formatted

        return self.text.format(
            get_belly_formatted(self.amount), self.sender.get_markdown_mention()
        )


class DevilFruitAwardedNotification(Notification):
    """Class for Devil Fruit awarded notifications."""

    def __init__(self, devil_fruit: DevilFruit = None, reason: str = None):
        """
        Constructor

        :param devil_fruit: The Devil Fruit
        :param reason: The reason
        """

        self.devil_fruit = devil_fruit
        self.reason = reason

        item_id = devil_fruit.id if devil_fruit is not None else None
        super().__init__(
            NotificationCategory.DEVIL_FRUIT,
            NotificationType.DEVIL_FRUIT_AWARDED,
            "DEVIL_FRUIT_AWARDED_NOTIFICATION",
            "DEVIL_FRUIT_AWARDED_NOTIFICATION_DESCRIPTION",
            "DEVIL_FRUIT_AWARDED_NOTIFICATION_KEY",
            item_screen=Screen.PVT_DEVIL_FRUIT_DETAIL,
            item_info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id},
            go_to_item_button_text="KEY_MANAGE_DEVIL_FRUIT",
        )

    def build(self) -> str:
        return self.text.format(
            escape_valid_markdown_chars(self.devil_fruit.get_full_name()),
            escape_valid_markdown_chars(self.reason),
        )


class DevilFruitExpiredNotification(Notification):
    """Class for Devil Fruit expired notifications."""

    def __init__(self, devil_fruit: DevilFruit = None):
        """
        Constructor

        :param devil_fruit: The Devil Fruit
        """

        self.devil_fruit = devil_fruit

        super().__init__(
            NotificationCategory.DEVIL_FRUIT,
            NotificationType.DEVIL_FRUIT_EXPIRED,
            "DEVIL_FRUIT_EXPIRED_NOTIFICATION",
            "DEVIL_FRUIT_EXPIRED_NOTIFICATION_DESCRIPTION",
            "DEVIL_FRUIT_EXPIRED_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(escape_valid_markdown_chars(self.devil_fruit.get_full_name()))


class DevilFruitRevokeNotification(Notification):
    """Class for Devil Fruit revoke notifications."""

    def __init__(self, devil_fruit: DevilFruit = None):
        """
        Constructor

        :param devil_fruit: The Devil Fruit
        """

        self.devil_fruit = devil_fruit

        super().__init__(
            NotificationCategory.DEVIL_FRUIT,
            NotificationType.DEVIL_FRUIT_REVOKE,
            "DEVIL_FRUIT_REVOKE_NOTIFICATION",
            "DEVIL_FRUIT_REVOKE_NOTIFICATION_DESCRIPTION",
            "DEVIL_FRUIT_REVOKE_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification."""

        return self.text.format(escape_valid_markdown_chars(self.devil_fruit.get_full_name()))


class DevilFruitRevokeWarningNotification(Notification):
    """Class for crew disband warning notifications."""

    def __init__(self, devil_fruit: DevilFruit = None):
        """
        Constructor

        :param devil_fruit: The Devil Fruit
        """

        self.devil_fruit = devil_fruit

        super().__init__(
            NotificationCategory.DEVIL_FRUIT,
            NotificationType.DEVIL_FRUIT_REVOKE_WARNING,
            "DEVIL_FRUIT_REVOKE_WARNING_NOTIFICATION",
            "DEVIL_FRUIT_REVOKE_WARNING_NOTIFICATION_DESCRIPTION",
            "DEVIL_FRUIT_REVOKE_WARNING_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        """Builds the notification."""

        from src.model.Leaderboard import Leaderboard
        from src.service.message_service import get_message_url

        leaderboard_url = ""
        latest_global_leaderboards = Leaderboard.get_latest_n(1, group=None)
        if latest_global_leaderboards:
            leaderboard_url = get_message_url(
                message_id=latest_global_leaderboards[0].message_id,
                chat_id=Env.UPDATES_CHAT_ID.get(),
                chat_username=Env.UPDATES_CHAT_USERNAME.get_or_none(),
            )

        return self.text.format(
            leaderboard_url, escape_valid_markdown_chars(self.devil_fruit.get_full_name())
        )


class BountyLoanPaymentNotification(Notification):
    """Class for bounty loan payment notifications."""

    def __init__(self, loan: BountyLoan = None, amount: int = None):
        """
        Constructor

        :param loan: The loan
        :param amount: The amount
        """

        self.loan = loan
        self.amount = amount

        item_id = loan.id if loan is not None else None
        super().__init__(
            NotificationCategory.BOUNTY_LOAN,
            NotificationType.BOUNTY_LOAN_PAYMENT,
            "BOUNTY_LOAN_PAYMENT_NOTIFICATION",
            "BOUNTY_LOAN_PAYMENT_NOTIFICATION_DESCRIPTION",
            "BOUNTY_LOAN_PAYMENT_NOTIFICATION_KEY",
            item_screen=Screen.PVT_BOUNTY_LOAN_DETAIL,
            item_info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id},
            go_to_item_button_text=(
                "BOUNTY_LOAN_NOTIFICATION_GO_TO_ITEM_BUTTON_TEXT"
            ),
        )

    def build(self) -> str:
        from src.utils.string_utils import get_belly_formatted

        borrower: User = self.loan.borrower
        return self.text.format(get_belly_formatted(self.amount), borrower.get_markdown_mention())


class BountyLoanForgivenNotification(Notification):
    """Class for bounty loan forgiven notifications."""

    def __init__(self, loan: BountyLoan = None):
        """
        Constructor

        :param loan: The loan
        """

        self.loan = loan

        item_id = loan.id if loan is not None else None
        super().__init__(
            NotificationCategory.BOUNTY_LOAN,
            NotificationType.BOUNTY_LOAN_FORGIVEN,
            "BOUNTY_LOAN_FORGIVEN_NOTIFICATION",
            "BOUNTY_LOAN_FORGIVEN_NOTIFICATION_DESCRIPTION",
            "BOUNTY_LOAN_FORGIVEN_NOTIFICATION_KEY",
            item_screen=Screen.PVT_BOUNTY_LOAN_DETAIL,
            item_info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id},
            go_to_item_button_text=(
                "BOUNTY_LOAN_NOTIFICATION_GO_TO_ITEM_BUTTON_TEXT"
            ),
        )

    def build(self) -> str:
        from src.utils.string_utils import get_belly_formatted

        loaner: User = self.loan.loaner
        return self.text.format(
            get_belly_formatted(self.loan.amount), loaner.get_markdown_mention()
        )


class BountyLoanExpiredNotification(Notification):
    """Class for bounty loan expired notifications."""

    def __init__(self, loan: BountyLoan = None):
        """
        Constructor

        :param loan: The loan
        """

        self.loan = loan

        item_id = loan.id if loan is not None else None
        super().__init__(
            NotificationCategory.BOUNTY_LOAN,
            NotificationType.BOUNTY_LOAN_EXPIRED,
            "BOUNTY_LOAN_EXPIRED_NOTIFICATION",
            "BOUNTY_LOAN_EXPIRED_NOTIFICATION_DESCRIPTION",
            "BOUNTY_LOAN_EXPIRED_NOTIFICATION_KEY",
            item_screen=Screen.PVT_BOUNTY_LOAN_DETAIL,
            item_info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id},
            go_to_item_button_text=(
                "BOUNTY_LOAN_NOTIFICATION_GO_TO_ITEM_BUTTON_TEXT"
            ),
        )

    def build(self) -> str:
        from src.utils.string_utils import get_belly_formatted

        loaner: User = self.loan.loaner
        return self.text.format(
            get_belly_formatted(self.loan.amount),
            loaner.get_markdown_mention(),
            Env.BOUNTY_LOAN_GARNISH_PERCENTAGE.get(),
            loaner.get_markdown_mention(),
        )


class WarlordAppointmentNotification(Notification):
    """Class for warlord appointment notifications."""

    def __init__(self, warlord: Warlord = None, days: int = None):
        """
        Constructor

        :param warlord: The warlord
        """

        self.warlord = warlord
        self.days = days

        super().__init__(
            NotificationCategory.WARLORD,
            NotificationType.WARLORD_APPOINTMENT,
            "WARLORD_APPOINTMENT_NOTIFICATION",
            "WARLORD_APPOINTMENT_NOTIFICATION_DESCRIPTION",
            "WARLORD_APPOINTMENT_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(
            escape_valid_markdown_chars(self.warlord.epithet),
            convert_days_to_duration(self.days),
            escape_valid_markdown_chars(self.warlord.reason),
        )


class WarlordRevocationNotification(Notification):
    """Class for warlord revocation notifications."""

    def __init__(self, warlord: Warlord = None):
        """
        Constructor

        :param warlord: The warlord
        """

        self.warlord = warlord

        super().__init__(
            NotificationCategory.WARLORD,
            NotificationType.WARLORD_REVOCATION,
            "WARLORD_REVOCATION_NOTIFICATION",
            "WARLORD_REVOCATION_NOTIFICATION_DESCRIPTION",
            "WARLORD_REVOCATION_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(escape_valid_markdown_chars(self.warlord.revoke_reason))


class LegendaryPirateAppointmentNotification(Notification):
    """Class for legendary pirate appointment notifications."""

    def __init__(
        self,
        legendary_pirate: "LegendaryPirate" = None,
        days: int = None,
        is_permanent: bool = False,
    ):
        """
        Constructor

        :param legendary_pirate: The legendary pirate
        :param days: The appointment duration in days
        :param is_permanent: Whether the appointment is permanent
        """

        self.legendary_pirate = legendary_pirate
        self.days = days
        self.is_permanent = is_permanent or (
            legendary_pirate is not None and legendary_pirate.is_permanent
        )

        super().__init__(
            NotificationCategory.LEGENDARY_PIRATE,
            NotificationType.LEGENDARY_PIRATE_APPOINTMENT,
            "LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION",
            "LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION_DESCRIPTION",
            "LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        if self.is_permanent or self.legendary_pirate.end_date is None:
            duration_text = "Permanent"
        else:
            days = self.days
            if days is None:
                days = get_remaining_time_in_days(
                    self.legendary_pirate.end_date, self.legendary_pirate.date
                )
            duration_text = convert_days_to_duration(days)

        text = self.text.format(
            escape_valid_markdown_chars(self.legendary_pirate.epithet),
            duration_text,
            escape_valid_markdown_chars(self.legendary_pirate.reason),
        )

        if self.is_permanent or self.legendary_pirate.end_date is None:
            text += phrases.LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION_PERMANENT_FOOTER

        return text


class LegendaryPirateRevocationNotification(Notification):
    """Class for legendary pirate revocation notifications."""

    def __init__(self, legendary_pirate: "LegendaryPirate" = None):
        """
        Constructor

        :param legendary_pirate: The legendary pirate
        """

        self.legendary_pirate = legendary_pirate

        super().__init__(
            NotificationCategory.LEGENDARY_PIRATE,
            NotificationType.LEGENDARY_PIRATE_REVOCATION,
            "LEGENDARY_PIRATE_REVOCATION_NOTIFICATION",
            "LEGENDARY_PIRATE_REVOCATION_NOTIFICATION_DESCRIPTION",
            "LEGENDARY_PIRATE_REVOCATION_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(escape_valid_markdown_chars(self.legendary_pirate.revoke_reason))


class CrewAbilityActivatedNotification(Notification):
    """Class for crew ability activated notifications."""

    def __init__(self, crew_ability: CrewAbility = None):
        """
        Constructor

        :param crew_ability: The crew ability
        """

        self.crew_ability = crew_ability

        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_ABILITY_ACTIVATED,
            "CREW_ABILITY_ACTIVATED_NOTIFICATION",
            "CREW_ABILITY_ACTIVATED_NOTIFICATION_DESCRIPTION",
            "CREW_ABILITY_ACTIVATED_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(
            escape_valid_markdown_chars(self.crew_ability.get_description()),
            self.crew_ability.get_value_with_sign(),
            get_remaining_duration(self.crew_ability.expiration_date, self.crew_ability.date),
        )


class CrewFirstMatePromotionNotification(Notification):
    """Class for crew first mate promotion notifications."""

    def __init__(self):
        """
        Constructor
        """

        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_FIRST_MATE_PROMOTION,
            "CREW_FIRST_MATE_PROMOTION_NOTIFICATION",
            "CREW_FIRST_MATE_PROMOTION_NOTIFICATION_DESCRIPTION",
            "CREW_FIRST_MATE_PROMOTION_NOTIFICATION_KEY",
        )


class CrewFirstMateDemotionNotification(Notification):
    """Class for crew first mate demotion notifications."""

    def __init__(self):
        """
        Constructor
        """

        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_FIRST_MATE_DEMOTION,
            "CREW_FIRST_MATE_DEMOTION_NOTIFICATION",
            "CREW_FIRST_MATE_DEMOTION_NOTIFICATION_DESCRIPTION",
            "CREW_FIRST_MATE_DEMOTION_NOTIFICATION_KEY",
        )


class CrewJoinRequestAcceptedNotification(Notification):
    """Class for crew join request accepted notifications."""

    def __init__(self, crew: Crew = None):
        """
        Constructor
        """

        self.crew: Crew = crew
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_JOIN_REQUEST_ACCEPTED,
            "CREW_JOIN_REQUEST_ACCEPTED_NOTIFICATION",
            "CREW_JOIN_REQUEST_ACCEPTED_NOTIFICATION_DESCRIPTION",
            "CREW_JOIN_REQUEST_ACCEPTED_NOTIFICATION_KEY",
            item_screen=Screen.PVT_CREW,
            go_to_item_button_text="KEY_VIEW",
        )

    def build(self) -> str:
        return self.text.format(self.crew.get_name_with_deeplink())


class CrewJoinRequestRejectedNotification(Notification):
    """Class for crew join request rejected notifications."""

    def __init__(self, crew: Crew = None):
        """
        Constructor
        """

        self.crew: Crew = crew
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_JOIN_REQUEST_REJECTED,
            "CREW_JOIN_REQUEST_REJECTED_NOTIFICATION",
            "CREW_JOIN_REQUEST_REJECTED_NOTIFICATION_DESCRIPTION",
            "CREW_JOIN_REQUEST_REJECTED_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(self.crew.get_name_with_deeplink())


class CrewConscriptionStartNotification(Notification):
    """Class for crew conscription start notifications."""

    def __init__(self, user: User = None):
        """
        Constructor
        """

        self.user: User = user
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_CONSCRIPTION_START,
            "CREW_CONSCRIPTION_START_NOTIFICATION",
            "CREW_CONSCRIPTION_START_NOTIFICATION_DESCRIPTION",
            "CREW_CONSCRIPTION_START_NOTIFICATION_KEY",
            item_screen=Screen.PVT_CREW,
            go_to_item_button_text="KEY_VIEW",
        )

    def build(self) -> str:
        return self.text.format(
            self.user.crew.get_name_with_deeplink(), self.user.get_conscription_remaining_time()
        )


class CrewConscriptionStartCaptainNotification(Notification):
    """Class for crew conscription start captain notifications."""

    def __init__(self, user: User = None):
        """
        Constructor
        """

        self.user: User = user
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_CONSCRIPTION_START_CAPTAIN,
            "CREW_CONSCRIPTION_START_CAPTAIN_NOTIFICATION",
            "CREW_CONSCRIPTION_START_CAPTAIN_NOTIFICATION_DESCRIPTION",
            "CREW_CONSCRIPTION_START_CAPTAIN_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(
            self.user.get_markdown_mention(),
            self.user.crew.get_name_with_deeplink(),
            self.user.get_conscription_remaining_time(),
        )


class CrewConscriptionEndNotification(Notification):
    """Class for crew conscription end notifications."""

    def __init__(self, user: User = None):
        """
        Constructor
        """

        self.user: User = user
        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_CONSCRIPTION_END,
            "CREW_CONSCRIPTION_END_NOTIFICATION",
            "CREW_CONSCRIPTION_END_NOTIFICATION_DESCRIPTION",
            "CREW_CONSCRIPTION_END_NOTIFICATION_KEY",
            item_screen=Screen.PVT_CREW,
            go_to_item_button_text="KEY_VIEW",
        )

    def build(self) -> str:
        return self.text.format(self.user.crew.get_name_with_deeplink())


class DavyBackFightRequestAcceptedNotification(Notification):
    """Class for davy back fight request accepted notifications."""

    def __init__(self, crew: Crew = None, davy_back_fight: DavyBackFight = None):
        """
        Constructor
        """

        self.crew: Crew = crew
        item_id = davy_back_fight.id if davy_back_fight is not None else None

        super().__init__(
            NotificationCategory.DAVY_BACK_FIGHT,
            NotificationType.DAVY_BACK_FIGHT_REQUEST_ACCEPTED,
            "DAVY_BACK_FIGHT_REQUEST_ACCEPTED_NOTIFICATION",
            "DAVY_BACK_FIGHT_REQUEST_ACCEPTED_NOTIFICATION_DESCRIPTION",
            "DAVY_BACK_FIGHT_REQUEST_ACCEPTED_NOTIFICATION_KEY",
            item_screen=Screen.PVT_CREW_DAVY_BACK_FIGHT_DETAIL,
            item_info={
                ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id,
                ReservedKeyboardKeys.DIRECT_ITEM: False,
            },
            go_to_item_button_text="KEY_MANAGE",
            item_previous_screens=[Screen.PVT_CREW],
        )

    def build(self) -> str:
        return self.text.format(self.crew.get_name_with_deeplink())


class DavyBackFightRequestRejectedNotification(Notification):
    """Class for davy back fight request rejected notifications."""

    def __init__(self, crew: Crew = None):
        """
        Constructor
        """

        self.crew: Crew = crew
        super().__init__(
            NotificationCategory.DAVY_BACK_FIGHT,
            NotificationType.DAVY_BACK_FIGHT_REQUEST_REJECTED,
            "CREW_DAVY_BACK_FIGHT_REQUEST_REJECTED_NOTIFICATION",
            "DAVY_BACK_FIGHT_REQUEST_REJECTED_NOTIFICATION_DESCRIPTION",
            "DAVY_BACK_FIGHT_REQUEST_REJECTED_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(self.crew.get_name_with_deeplink())


class DavyBackFightStartNotification(Notification):
    """Class for davy back fight start notifications."""

    def __init__(self, opponent_crew: Crew = None, davy_back_fight: DavyBackFight = None):
        """
        Constructor
        """

        self.opponent_crew: Crew = opponent_crew
        self.davy_back_fight: DavyBackFight = davy_back_fight
        item_id = davy_back_fight.id if davy_back_fight is not None else None

        super().__init__(
            NotificationCategory.DAVY_BACK_FIGHT,
            NotificationType.DAVY_BACK_FIGHT_START,
            "DAVY_BACK_FIGHT_START_NOTIFICATION",
            "DAVY_BACK_FIGHT_START_NOTIFICATION_DESCRIPTION",
            "DAVY_BACK_FIGHT_START_NOTIFICATION_KEY",
            item_screen=Screen.PVT_CREW_DAVY_BACK_FIGHT_DETAIL,
            item_info={
                ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id,
                ReservedKeyboardKeys.DIRECT_ITEM: False,
            },
            go_to_item_button_text="KEY_VIEW",
            item_previous_screens=[Screen.PVT_CREW],
        )

    def build(self) -> str:
        return self.text.format(
            self.opponent_crew.get_name_with_deeplink(),
            self.davy_back_fight.get_remaining_time(),
        )


class DavyBackFightEndNotification(Notification):
    """Class for davy back fight end notifications."""

    def __init__(self, opponent_crew: Crew = None, participant: DavyBackFightParticipant = None):
        """
        Constructor
        """

        self.opponent_crew: Crew = opponent_crew
        self.participant: DavyBackFightParticipant = participant
        self.davy_back_fight: DavyBackFight = participant.davy_back_fight if participant else None
        item_id = self.davy_back_fight.id if self.davy_back_fight is not None else None

        super().__init__(
            NotificationCategory.DAVY_BACK_FIGHT,
            NotificationType.DAVY_BACK_FIGHT_END,
            "DAVY_BACK_FIGHT_END_NOTIFICATION",
            "DAVY_BACK_FIGHT_END_NOTIFICATION_DESCRIPTION",
            "DAVY_BACK_FIGHT_END_NOTIFICATION_KEY",
            item_screen=Screen.PVT_CREW_DAVY_BACK_FIGHT_DETAIL,
            item_info={
                ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: item_id,
                ReservedKeyboardKeys.DIRECT_ITEM: False,
            },
            go_to_item_button_text="KEY_VIEW",
            item_previous_screens=[Screen.PVT_CREW],
        )

    def build(self) -> str:
        if self.participant.in_winner_crew():
            return phrases.DAVY_BACK_FIGHT_END_NOTIFICATION_WON.format(
                self.opponent_crew.get_name_with_deeplink(),
                get_belly_formatted(self.participant.win_amount),
                format_percentage_value(self.participant.get_contribution_percentage()),
                get_remaining_duration(self.davy_back_fight.penalty_end_date),
            )

        return phrases.DAVY_BACK_FIGHT_END_NOTIFICATION_LOST.format(
            self.opponent_crew.get_name_with_deeplink(),
            get_remaining_duration(self.davy_back_fight.penalty_end_date),
        )


class ImpelDownBailPostedNotification(Notification):
    """Class for impel down bail posted notifications."""

    def __init__(self, impel_down_log: ImpelDownLog = None):
        """
        Constructor

        :param impel_down_log: The impel down log
        """

        self.impel_down_log: ImpelDownLog = impel_down_log

        super().__init__(
            NotificationCategory.IMPEL_DOWN,
            NotificationType.IMPEL_DOWN_BAIL_POSTED,
            "IMPEL_DOWN_BAIL_POSTED_NOTIFICATION",
            "IMPEL_DOWN_BAIL_POSTED_NOTIFICATION_DESCRIPTION",
            "IMPEL_DOWN_BAIL_POSTED_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        from src.utils.string_utils import get_belly_formatted

        return self.text.format(
            self.impel_down_log.bail_payer.get_markdown_mention(),
            get_belly_formatted(self.impel_down_log.bail_amount),
            get_remaining_duration(self.impel_down_log.release_date_time),
        )


class DevilFruitSoldNotification(Notification):
    """Class for devil fruit sold notifications."""

    def __init__(self, devil_fruit_trade: DevilFruitTrade = None):
        """
        Constructor

        :param devil_fruit_trade: The trade
        """

        self.trade: DevilFruitTrade = devil_fruit_trade

        super().__init__(
            NotificationCategory.DEVIL_FRUIT,
            NotificationType.DEVIL_FRUIT_SOLD,
            "DEVIL_FRUIT_SOLD_NOTIFICATION",
            "DEVIL_FRUIT_SOLD_NOTIFICATION_DESCRIPTION",
            "DEVIL_FRUIT_SOLD_NOTIFICATION_KEY",
        )

    def build(self) -> str:
        return self.text.format(
            escape_valid_markdown_chars(self.trade.devil_fruit.get_full_name()),
            get_belly_formatted(self.trade.price),
            self.trade.receiver.get_markdown_mention(),
        )


class CrewCaptainPromotionNotification(Notification):
    """Class for crew captain promotion notifications."""

    def __init__(self):
        """
        Constructor
        """

        super().__init__(
            NotificationCategory.CREW,
            NotificationType.CREW_CAPTAIN_PROMOTION,
            "CREW_CAPTAIN_PROMOTION_NOTIFICATION",
            "CREW_CAPTAIN_PROMOTION_NOTIFICATION_DESCRIPTION",
            "CREW_CAPTAIN_PROMOTION_NOTIFICATION_KEY",
        )


class FightAttackNotification(Notification):
    """Class for fight attack notifications."""

    def __init__(self, fight: Fight = None):
        """
        Constructor

        :param fight: The fight
        """

        self.fight = fight

        super().__init__(
            NotificationCategory.FIGHT,
            NotificationType.FIGHT_ATTACK,
            "FIGHT_ATTACK_NOTIFICATION",
            "FIGHT_ATTACK_NOTIFICATION_DESCRIPTION",
            "FIGHT_ATTACK_NOTIFICATION_KEY",
            item_screen=Screen.PVT_LOGS_TYPE_DETAIL,
            item_info={
                LogTypeReservedKeys.TYPE: LogType.FIGHT,
                LogTypeReservedKeys.ITEM_ID: fight.id if fight is not None else None,
            },
            go_to_item_button_text="KEY_VIEW_LOG",
        )

    def build(self) -> str:
        if self.fight.get_status() is GameStatus.LOST:
            won_lost_text = phrases.TEXT_WON
            won_lost_emoji = Emoji.CONFETTI
        else:
            won_lost_text = phrases.TEXT_LOST
            won_lost_emoji = Emoji.LOSER

        ot_text = self.text.format(
            won_lost_text,
            self.fight.challenger.get_markdown_mention(),
            won_lost_emoji,
            won_lost_text,
            get_belly_formatted(self.fight.belly),
        )

        # Fight can be revenged
        if self.fight.can_revenge():
            ot_text += phrases.FIGHT_ATTACK_CAN_REVENGE.format(
                self.fight.get_revenge_remaining_duration()
            )
        else:  # Only occasion a fight can't be revenged is if it was in response to another fight
            ot_text += phrases.FIGHT_ATTACK_CANNOT_REVENGE.format(
                Log.get_deeplink_by_type(LogType.FIGHT, self.fight.in_revenge_to_fight.id)
            )

        return ot_text


class PlunderAttackNotification(Notification):
    """Class for plunder attack notifications."""

    def __init__(self, plunder: Plunder = None):
        """
        Constructor

        :param plunder: The plunder
        """

        self.plunder = plunder

        super().__init__(
            NotificationCategory.PLUNDER,
            NotificationType.PLUNDER_ATTACK,
            "PLUNDER_ATTACK_NOTIFICATION",
            "PLUNDER_ATTACK_NOTIFICATION_DESCRIPTION",
            "PLUNDER_ATTACK_NOTIFICATION_KEY",
            item_screen=Screen.PVT_LOGS_TYPE_DETAIL,
            item_info={
                LogTypeReservedKeys.TYPE: LogType.PLUNDER,
                LogTypeReservedKeys.ITEM_ID: plunder.id if plunder is not None else None,
            },
            go_to_item_button_text="KEY_VIEW_LOG",
        )

    def build(self) -> str:
        if self.plunder.get_status() is GameStatus.LOST:
            text = phrases.PLUNDER_ATTACK_NOTIFICATION_WON
        else:
            text = phrases.PLUNDER_ATTACK_NOTIFICATION_LOST

        ot_text = text.format(
            self.plunder.challenger.get_markdown_mention(), get_belly_formatted(self.plunder.belly)
        )

        # Plunder can be revenged
        if self.plunder.can_revenge():
            ot_text += phrases.PLUNDER_ATTACK_CAN_REVENGE.format(
                self.plunder.get_revenge_remaining_duration()
            )
        else:  # Only occasion a plunder can't be revenged is if it was in response to another plunder
            ot_text += phrases.PLUNDER_ATTACK_CANNOT_REVENGE.format(
                Log.get_deeplink_by_type(LogType.PLUNDER, self.plunder.in_revenge_to_plunder.id)
            )

        return ot_text


class GameOutcomeNotification(Notification):
    """Class for game outcome notifications."""

    def __init__(self, game: Game = None, user: User = None, footer_text: str = ""):
        """Constructor

        :param game: The game
        :param user: The user to send the outcome to
        :param footer_text: Text to add as footer
        """

        self.game = game
        self.user = user
        self.footer_text = footer_text

        super().__init__(
            NotificationCategory.GAME,
            NotificationType.GAME_OUTCOME,
            "",
            "GAME_OUTCOME_NOTIFICATION_DESCRIPTION",
            "GAME_OUTCOME_NOTIFICATION_KEY",
            disable_notification=False,
            item_screen=Screen.PVT_LOGS_TYPE_DETAIL,
            item_info={
                LogTypeReservedKeys.TYPE: LogType.GAME,
                LogTypeReservedKeys.ITEM_ID: game.id if game is not None else None,
            },
            go_to_item_button_text="KEY_VIEW_LOG",
        )

    def build(self) -> str:
        """Builds the notification."""
        # Not supported if result is not win/lost/draw
        if self.game.get_status() not in [GameStatus.WON, GameStatus.LOST, GameStatus.DRAW]:
            raise ValueError(
                "send_outcome_to_user is not supported for this game outcome: "
                + str(self.game.get_status())
            )

        if self.game.get_status() is not GameStatus.DRAW:
            won = self.user == self.game.get_winner()
            if won:
                emoji = Emoji.LOG_POSITIVE
                text_won_lost = phrases.TEXT_WON
            else:
                emoji = Emoji.LOG_NEGATIVE
                text_won_lost = phrases.TEXT_LOST

            return (
                phrases.GAME_OUTCOME_NOTIFICATION.format(
                    emoji,
                    text_won_lost,
                    self.game.get_half_wager_formatted(),
                    GameType(self.game.type).get_name(),
                    mention_markdown_user(self.game.get_other_player(self.user)),
                )
                + self.footer_text
            )

        return (
            phrases.GAME_OUTCOME_NOTIFICATION_DRAW.format(
                GameType(self.game.type).get_name(),
                mention_markdown_user(self.game.get_other_player(self.user)),
                self.game.get_half_wager_formatted(),
            )
            + self.footer_text
        )


NOTIFICATIONS = [
    CrewLeaveNotification(),
    LocationUpdateNotification(),
    CrewDisbandNotification(),
    CrewDisbandWarningNotification(),
    GameTurnNotification(),
    CrewMemberRemoveNotification(),
    ImpelDownNotificationRestrictionPlaced(),
    ImpelDownNotificationRestrictionRemoved(),
    PredictionResultNotification(),
    PredictionBetInvalidNotification(),
    DeletedMessageArrestNotification(),
    DeletedMessageMuteNotification(),
    DeletedMessageLocationNotification(),
    BountyGiftReceivedNotification(),
    DevilFruitAwardedNotification(),
    DevilFruitExpiredNotification(),
    DevilFruitRevokeNotification(),
    DevilFruitRevokeWarningNotification(),
    BountyLoanPaymentNotification(),
    BountyLoanForgivenNotification(),
    BountyLoanExpiredNotification(),
    WarlordAppointmentNotification(),
    WarlordRevocationNotification(),
    LegendaryPirateAppointmentNotification(),
    LegendaryPirateRevocationNotification(),
    CrewAbilityActivatedNotification(),
    CrewFirstMatePromotionNotification(),
    CrewFirstMateDemotionNotification(),
    CrewJoinRequestAcceptedNotification(),
    CrewJoinRequestRejectedNotification(),
    CrewConscriptionStartNotification(),
    CrewConscriptionStartCaptainNotification(),
    CrewConscriptionEndNotification(),
    ImpelDownBailPostedNotification(),
    DavyBackFightRequestAcceptedNotification(),
    DavyBackFightRequestRejectedNotification(),
    DavyBackFightStartNotification(),
    DavyBackFightEndNotification(),
    DevilFruitSoldNotification(),
    CrewCaptainPromotionNotification(),
    FightAttackNotification(),
    PlunderAttackNotification(),
    GameOutcomeNotification(),
]


def get_notifications_by_category(
    notification_category: NotificationCategory,
) -> list[Notification]:
    """
    Get all notifications by category

    :param notification_category: The category
    :return: List of notifications
    """

    return [
        notification
        for notification in NOTIFICATIONS
        if notification.category is notification_category
    ]


def get_notification_by_type(notification_type: NotificationType) -> Notification:
    """
    Get a notification by type

    :param notification_type: The type
    :return: The notification
    """

    notification = next(
        notification for notification in NOTIFICATIONS if notification.type is notification_type
    )

    # Need to re-initialize the class since it would be initialized only once on program start, and it would keep in
    # memory items
    # noinspection PyArgumentList
    notification.__init__()

    return notification
