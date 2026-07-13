from resources import phrases


class LazyPhraseDict(dict):
    """
    A dict that is built once at import time with phrase *constant names* (strings) as
    values instead of resolved phrase strings, and resolves them against the currently
    active language every time a value is read.

    This is needed because dicts such as `{SomeEnum.A: phrases.SOME_TEXT}` are normally
    built once when the module is first imported, "freezing" the phrase in whatever
    language was active at that time (usually the default language, since imports happen
    at Bot startup). By storing the phrase constant *name* instead of its value, and
    resolving it lazily on every access, the dict stays correct no matter which language
    is active when it's read.

    Usage:
        MY_DICT = LazyPhraseDict({MyEnum.A: "SOME_PHRASE_CONSTANT_NAME"})
        MY_DICT[MyEnum.A]  # Resolved in the language currently active

        # If the phrase needs .format() args that are already known at import time
        # (e.g. static Env values), store a tuple of (constant_name, args_tuple) instead:
        MY_DICT = LazyPhraseDict({MyEnum.A: ("SOME_PHRASE_CONSTANT_NAME", (arg1, arg2))})
    """

    def __getitem__(self, key):
        value = super().__getitem__(key)

        if isinstance(value, tuple):
            phrase_constant_name, format_args = value
            return getattr(phrases, phrase_constant_name).format(*format_args)

        return getattr(phrases, value)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def values(self):
        return [self[key] for key in self.keys()]

    def items(self):
        return [(key, self[key]) for key in self.keys()]
