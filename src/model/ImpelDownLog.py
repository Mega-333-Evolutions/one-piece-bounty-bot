from datetime import datetime

from peewee import *

import resources.Environment as Env
from src.model.BaseModel import BaseModel
from src.model.User import User


class ImpelDownLog(BaseModel):
    """
    Impel Down Log class
    """

    user = ForeignKeyField(
        User, backref="impel_down_users", on_delete="CASCADE", on_update="CASCADE"
    )
    sentence_type = CharField(max_length=99, null=True)
    source = CharField(max_length=10, null=True)
    release_date_time = DateTimeField(null=True)
    is_permanent = BooleanField(default=False)
    bounty_action = CharField(max_length=99, null=True)
    reason = CharField(max_length=999, null=True)
    previous_bounty = BigIntegerField(null=True)
    new_bounty = BigIntegerField(null=True)
    message_sent = BooleanField(default=False)
    is_reversed = BooleanField(default=False)
    external_id = IntegerField(null=True)
    bail_amount = BigIntegerField(null=True)
    bail_date = DateTimeField(null=True)
    bail_payer: User | ForeignKeyField = ForeignKeyField(
        User, backref="impel_down_bail_payers", null=True, on_delete="RESTRICT"
    )

    class Meta:
        db_table = "impel_down_log"

    @staticmethod
    def get_current_for_user(user: User):
        """
        Get the current impel down log for the user.

        Always returns the LATEST active record (highest id) so that a new
        dashboard sentence is never shadowed by an older bot-created record
        that hasn't been reversed yet.

        :param user: The user
        :return: The impel down log, or None
        """
        if not user.is_arrested():
            return None

        return (
            ImpelDownLog.select()
            .where(
                (ImpelDownLog.user == user)
                & (ImpelDownLog.is_reversed == False)
                & (
                    (ImpelDownLog.is_permanent == True)
                    | (ImpelDownLog.release_date_time > datetime.now())
                )
                & (ImpelDownLog.bail_date.is_null())
            )
            .order_by(ImpelDownLog.id.desc())   # ← always use the newest sentence
            .first()
        )

    def get_bail(self) -> int:
        """
        Calculate the bail cost based on the number of whole minutes remaining.

        release_date_time is stored as a naive datetime by both the bot and the
        dashboard. tzinfo is stripped defensively so a timezone-aware value
        stored by a future migration doesn't cause a TypeError.

        :return: Bail amount in bounty
        """
        if self.release_date_time is None:
            return 0

        # Strip timezone info to ensure consistent naive-datetime arithmetic
        release_dt = (
            self.release_date_time.replace(tzinfo=None)
            if self.release_date_time.tzinfo is not None
            else self.release_date_time
        )

        remaining_seconds = (release_dt - datetime.now()).total_seconds()

        # Floor to whole minutes — never return a negative bail
        remaining_minutes = int(remaining_seconds // 60)
        if remaining_minutes <= 0:
            return 0

        return remaining_minutes * Env.IMPEL_DOWN_BAIL_PER_MINUTE.get_int()


ImpelDownLog.create_table()
