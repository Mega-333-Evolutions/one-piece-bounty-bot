import logging
from datetime import datetime

from peewee import *

from resources.Database import Database

db_obj = Database()

# Divisor to use in a database expression that divides a column by two, e.g. User.bounty / DIVIDE_BY_TWO.
# A plain "/ 2" is divided as whole numbers by PostgreSQL (the result is rounded down) while MySQL
# divides with decimals and rounds the result when it is saved, so e.g. 5 / 2 would give 2 on
# PostgreSQL and 3 on MySQL. Written as SQL, the division has decimals on both databases. (Writing it
# as the number 2.0 would not work: peewee turns the number into the integer 2 for an integer column)
DIVIDE_BY_TWO = SQL("2.0")

# The connection peewee opens to MySQL is not in strict mode (it sets sql_mode to just PIPES_AS_CONCAT), so
# MySQL quietly "fixes" a value it can't store instead of refusing it, and the bot came to rely on that.
# PostgreSQL refuses every one of them ("null value in column ... violates not-null constraint", "value too
# long for type character varying(255)"), so the command or button that saved the row did nothing at all
# (the error was only logged). BaseModel.save() below gives PostgreSQL the same forgiving behaviour:
#   * a NOT NULL column without a default that an INSERT leaves out gets what MySQL stores for it: an empty
#     string for text and 0 for numbers. The bot often saves a row first and sets a column like
#     DailyReward.limitation (only set when the reward is limited), IncomeTaxEvent.contribution_list or
#     Leaderboard.message_id (filled in after the message is sent) later, or never
#   * a text longer than its column (e.g. the text of an error that is saved in SystemUpdateUser.error or
#     GroupChat.last_error_message) is cut to the length of the column, as MySQL does
#   * a whole number outside the range of its column (e.g. a 25 digit "required bounty" typed for a crew) is
#     set to the nearest end of the range, as MySQL does ("bigint out of range" on PostgreSQL)
_NO_IMPLICIT_DEFAULT = object()
_implicit_defaults_by_model: dict = {}


def _get_implicit_default(field: Field):
    """
    Get the value MySQL stores for a NOT NULL column that an INSERT leaves out
    :param field: The field
    :return: The value, or _NO_IMPLICIT_DEFAULT if it has none that is worth giving it. Keys have
    none either in MySQL (the 0 MySQL would store points to no row, so the INSERT fails there too)
    and neither do dates (MySQL's zero date can't be stored in PostgreSQL)
    """

    if field.primary_key or field.null or field.default is not None:
        return _NO_IMPLICIT_DEFAULT

    if isinstance(field, (CharField, TextField)):
        return ""

    if isinstance(field, BooleanField):
        return False

    if isinstance(field, (IntegerField, FloatField, DecimalField)):
        return 0

    return _NO_IMPLICIT_DEFAULT


def _get_integer_range(field: Field) -> tuple[int, int] | None:
    """
    Get the smallest and the biggest number a whole number column holds
    :param field: The field
    :return: The range, or None if the field is not a whole number column (or is a key)
    """

    if not isinstance(field, IntegerField) or field.primary_key:
        return None

    if isinstance(field, SmallIntegerField):
        bits = 16
    elif isinstance(field, BigIntegerField):
        bits = 64
    else:
        bits = 32

    return -(2 ** (bits - 1)), 2 ** (bits - 1) - 1


class BaseModel(Model):
    """
    BaseModel class
    Used to manage Entities and Database connection
    """

    id: int | PrimaryKeyField = PrimaryKeyField()
    date = DateTimeField(default=datetime.now)

    class Meta:
        database = db_obj.get_db()
        only_save_dirty = True

    @classmethod
    def get_implicit_defaults(cls) -> dict:
        """
        Get the NOT NULL columns without a default and the value MySQL stores for them when an
        INSERT leaves them out
        :return: The values by field name
        """

        if cls not in _implicit_defaults_by_model:
            implicit_defaults = {}
            for name, field in cls._meta.fields.items():
                value = _get_implicit_default(field)
                if value is not _NO_IMPLICIT_DEFAULT:
                    implicit_defaults[name] = value
            _implicit_defaults_by_model[cls] = implicit_defaults

        return _implicit_defaults_by_model[cls]

    def save(self, *args, **kwargs):
        """
        Save the model. First it gets, as MySQL would have done and PostgreSQL would refuse, the
        value MySQL stores for every NOT NULL column a new row has no value for (see
        _get_implicit_default), the texts that are too long for their column are cut and the whole
        numbers that are outside the range of their column are set to the nearest end of it
        """

        force_insert = kwargs.get("force_insert", args[0] if args else False)
        if force_insert or self._pk is None:
            for name, value in self.get_implicit_defaults().items():
                if name not in self.__data__:
                    setattr(self, name, value)

        for name in list(self._dirty):
            field = self._meta.fields.get(name)
            value = self.__data__.get(name)
            if (
                isinstance(field, CharField)
                and field.max_length
                and isinstance(value, str)
                and len(value) > field.max_length
            ):
                logging.warning(
                    f"{type(self).__name__}.{name} is {len(value)} characters long but its column "
                    f"holds {field.max_length}: saving the first {field.max_length} "
                    f"({value[:40]!r}...)"
                )
                setattr(self, name, value[: field.max_length])

            integer_range = _get_integer_range(field)
            if (
                integer_range is not None
                and isinstance(value, int)
                and not isinstance(value, bool)
                and not integer_range[0] <= value <= integer_range[1]
            ):
                clipped = max(integer_range[0], min(integer_range[1], value))
                logging.warning(
                    f"{type(self).__name__}.{name} is {value} but its column holds from "
                    f"{integer_range[0]} to {integer_range[1]}: saving {clipped}"
                )
                setattr(self, name, clipped)

        return super().save(*args, **kwargs)
