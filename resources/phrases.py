"""
This module is a drop-in replacement for what used to be a plain module of English string
constants. It transparently resolves every phrase to the language currently active for the
chat being processed (see src.service.language_service), while every other part of the
codebase keeps using it exactly as before, e.g. `from resources import phrases` then
`phrases.SOME_CONSTANT`.

How it works:
    - resources/phrases_en.py holds the original English constants (source of truth).
    - resources/phrases_fa.py holds the Persian (Farsi) translations, using the exact same
      constant names.
    - This module dynamically resolves `phrases.SOME_CONSTANT` to the value defined in the
      currently active language's module, falling back to English if a translation is
      missing, so a missing/incomplete translation never breaks the Bot.

If a new phrase constant is added, it only needs to be added to phrases_en.py (and ideally
phrases_fa.py too). No changes are required in this file.
"""

import sys
from types import ModuleType

import resources.phrases_en as phrases_en
import resources.phrases_fa as phrases_fa
from src.model.enums.Language import Language
from src.service.language_service import get_current_language

_LANGUAGE_MODULES: dict[Language, ModuleType] = {
    Language.ENGLISH: phrases_en,
    Language.PERSIAN: phrases_fa,
}


class _PhrasesModule(ModuleType):
    """
    Proxy module that resolves attribute access to the phrase defined for the currently
    active language, falling back to English if not found.
    """

    def __getattr__(self, item: str):
        language = get_current_language()
        module = _LANGUAGE_MODULES.get(language, phrases_en)

        try:
            return getattr(module, item)
        except AttributeError:
            # Fallback to English if the translation is missing for this constant
            return getattr(phrases_en, item)


sys.modules[__name__].__class__ = _PhrasesModule
