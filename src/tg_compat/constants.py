"""Drop-in replacement for the (small) subset of ``telegram.constants`` used
by the original codebase."""

from enum import StrEnum


class ChatMemberStatus(StrEnum):
    """Mirrors telegram.constants.ChatMemberStatus. Values match the literal
    strings used by the Bot API, since some of the original code may log or
    compare these directly."""

    OWNER = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    BANNED = "kicked"
