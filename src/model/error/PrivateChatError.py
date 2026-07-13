from src.model.error.Error import Error
from src.model.error.ErrorSource import ErrorSource


class PrivateChatError(Error):
    source = ErrorSource.PRIVATE_CHAT

    UNRECOGNIZED_SCREEN = Error(1, "UNRECOGNIZED_SCREEN", source)
    UNKNOWN_EXTRA_STEP = Error(2, "UNKNOWN_EXTRA_STEP", source)
    PRIVATE_STEP_NOT_SET = Error(3, "PRIVATE_STEP_NOT_SET", source)
    ITEM_NOT_FOUND = Error(4, "ITEM_NOT_FOUND", source)
    SAVED_USER_DATA_NOT_FOUND = Error(5, "SAVED_USER_DATA_NOT_FOUND", source)


class PrivateChatException(Exception):
    def __init__(self, error: PrivateChatError = None, text: str = None):
        if error is not None:
            self.message = error.build()
        else:
            self.message = text
        super().__init__(self.message)
