from src.model.error.Error import Error
from src.model.error.ErrorSource import ErrorSource


class TgRestChatError(Error):
    source = ErrorSource.TG_REST

    UNKNOWN_PREDICTION_ACTION = Error(1, "UNKNOWN_PREDICTION_ACTION", source)
