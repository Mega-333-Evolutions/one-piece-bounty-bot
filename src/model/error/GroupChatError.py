from src.model.error.Error import Error
from src.model.error.ErrorSource import ErrorSource


class GroupChatError(Error):
    source = ErrorSource.GROUP_CHAT

    USER_NOT_IN_DB = Error(1, "USER_NOT_FOUND", source)
    UNRECOGNIZED_SCREEN = Error(2, "UNRECOGNIZED_SCREEN", source)
    SAVED_MEDIA_NOT_FOUND = Error(3, "SAVED_MEDIA_NOT_FOUND", source)
    DOC_Q_GAME_NOT_FOUND = Error(4, "DOC_Q_GAME_NOT_FOUND", source)
    KEYBOARD_NOT_FOUND = Error(5, "KEYBOARD_NOT_FOUND", source)
    INVALID_CHANGE_REGION_REQUEST = Error(
        6, "LOCATION_INVALID_CHANGE_REGION_REQUEST", source
    )
    FIGHT_NOT_FOUND = Error(7, "FIGHT_NOT_FOUND", source)
    FIGHT_OPPONENT_NOT_FOUND = Error(8, "FIGHT_OPPONENT_NOT_FOUND", source)
    GAME_NOT_FOUND = Error(9, "GAME_NOT_FOUND", source)
    INVALID_GAME = Error(10, "GAME_INVALID", source)
    ITEM_IN_WRONG_STATUS = Error(11, "ITEM_IN_WRONG_STATUS", source)
    ITEM_NOT_FOUND = Error(12, "ITEM_NOT_FOUND_NO_CONTACT", source)


class GroupChatException(Exception):
    def __init__(self, error: GroupChatError):
        self.message = error.build()
        super().__init__(self.message)
