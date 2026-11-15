from enum import StrEnum


class ButtonStyle(StrEnum):
    SUCCESS = "success"
    DANGER = "danger"
    PRIMARY = "primary"
    # No colour at all, not even the one the text of the button would get by itself (see
    # get_semantic_button_style). For a button whose text only happens to be the same as a
    # coloured one, like the notification category called "Fight"
    NONE = "none"
