import re

import resources.phrases_en as phrases_en
import resources.phrases_fa as phrases_fa
from src.model.enums.ButtonStyle import ButtonStyle

# Both language modules are used directly (bypassing the language-aware phrases.py proxy)
# so that semantic button matching works regardless of which language is currently active.
_LANGUAGE_MODULES = [phrases_en, phrases_fa]


def normalize_button_text(text: str) -> str:
    """
    Normalize button text for semantic style lookup, stripping emojis/symbols and casing.
    Works with any script (Latin, Persian, etc.), not just English.
    """

    if not text:
        return ""

    # Matches any letter in any language/script, excluding digits, punctuation and emojis
    words = re.findall(r"[^\W\d_]+", text, re.UNICODE)
    return " ".join(w.lower() for w in words)


def _normalized_values(*values: str) -> set[str]:
    return {normalize_button_text(v) for v in values if v}


def _build_style_sets() -> tuple[set[str], set[str], set[str]]:
    success_texts: set[str] = set()
    danger_texts: set[str] = set()
    primary_texts: set[str] = set()

    for p in _LANGUAGE_MODULES:
        success_texts |= _normalized_values(
            p.TEXT_YES,
            p.KEYBOARD_OPTION_YES,
            p.KEYBOARD_OPTION_ACCEPT,
            p.KEY_CONFIRM,
            p.KEYBOARD_OPTION_SEND_REQUEST,
            p.GRP_KEY_GAME_PLAY,
            p.TEXT_ONLY.format(p.TEXT_WON),
            p.KEY_OPEN,
            p.KEYBOARD_OPTION_RETREAT,
            p.KEY_JOIN_A_CREW,
            p.PVT_KEY_CREW_SEARCH_JOIN,
            p.KEYBOARD_OPTION_CHOOSE,
            p.GRP_KEY_DAILY_REWARD_PRIZE_RANDOM,
        )
        danger_texts |= _normalized_values(
            p.TEXT_NO,
            p.KEYBOARD_OPTION_NO,
            p.KEYBOARD_OPTION_REJECT,
            p.KEYBOARD_OPTION_CANCEL,
            p.KEYBOARD_OPTION_DELETE,
            p.KEY_REMOVE,
            p.PVT_KEY_CREW_DISBAND,
            p.TEXT_ONLY.format(p.TEXT_LOST),
            p.KEYBOARD_OPTION_CLOSE,
            p.KEY_CLOSE,
            p.KEYBOARD_OPTION_FIGHT,
            p.KEYBOARD_OPTION_PLUNDER,
            p.PVT_KEY_CREW_DAVY_BACK_FIGHT,
        )
        primary_texts |= _normalized_values(
            p.KEYBOARD_OPTION_BACK,
            p.PVT_KEY_SHOW_ALL,
            p.GRP_KEY_GAME_START_GLOBAL,
            p.KEYBOARD_OPTION_SCOUT,
            p.KEYBOARD_OPTION_NEW_SCOUT,
            p.GRP_KEY_DAILY_REWARD_PRIZE_ACCEPT,  # "Accept offer" - exception to the
            # general accept=success rule
        )

    return success_texts, danger_texts, primary_texts


_SUCCESS_TEXTS, _DANGER_TEXTS, _PRIMARY_TEXTS = _build_style_sets()


def get_semantic_button_style(text: str) -> ButtonStyle | None:
    """
    Return a default style for globally-known semantic button labels, matched against
    both English and Persian phrasing so the styling works regardless of the currently
    active language.
    """

    normalized_text = normalize_button_text(text)

    if not normalized_text:
        return None

    if normalized_text in _SUCCESS_TEXTS:
        return ButtonStyle.SUCCESS

    if normalized_text in _DANGER_TEXTS:
        return ButtonStyle.DANGER

    if normalized_text in _PRIMARY_TEXTS:
        return ButtonStyle.PRIMARY

    return None
