import datetime

from peewee import *

from src.model.BaseModel import BaseModel
from src.model.User import User


class LegendaryPirate(BaseModel):
    """
    Legendary Pirate class
    """

    user = ForeignKeyField(
        User, backref="legendary_pirates", on_delete="CASCADE", on_update="CASCADE"
    )
    epithet = CharField(max_length=99, null=True)
    reason = CharField(max_length=999, null=True)
    end_date = DateTimeField(null=True)
    original_end_date = DateTimeField(null=True)
    revoke_reason = CharField(max_length=999, null=True)
    is_permanent = BooleanField(default=False)

    class Meta:
        db_table = "legendary_pirate"

    @staticmethod
    def get_active() -> list["LegendaryPirate"]:
        """
        Get active legendary pirates
        :return: Active legendary pirates
        """

        ensure_legendary_pirate_schema()
        now = datetime.datetime.now()
        return LegendaryPirate.select().where(
            (LegendaryPirate.end_date.is_null()) | (LegendaryPirate.end_date > now)
        )

    def is_active(self) -> bool:
        """
        Returns True if the legendary pirate is active
        :return: True if the legendary pirate is active
        """

        return self.end_date is None or self.end_date > datetime.datetime.now()

    @staticmethod
    def get_active_user_ids() -> list[int]:
        """
        Get active legendary pirate user ids
        :return: Active legendary pirate user ids
        """

        return [legendary_pirate.user.id for legendary_pirate in LegendaryPirate.get_active()]

    @staticmethod
    def get_active_order_by_bounty() -> list["LegendaryPirate"]:
        """
        Get active legendary pirates ordered by bounty
        :return: Active legendary pirates
        """

        ensure_legendary_pirate_schema()
        now = datetime.datetime.now()
        return list(
            LegendaryPirate.select()
            .join(User)
            .where((LegendaryPirate.end_date.is_null()) | (LegendaryPirate.end_date > now))
            .order_by(User.bounty.desc())
        )

    @staticmethod
    def get_active_permanent_order_by_bounty() -> list["LegendaryPirate"]:
        """
        Get active permanent legendary pirates ordered by bounty
        :return: Active permanent legendary pirates
        """

        ensure_legendary_pirate_schema()
        now = datetime.datetime.now()
        return list(
            LegendaryPirate.select()
            .join(User)
            .where(
                (LegendaryPirate.is_permanent == True)
                & ((LegendaryPirate.end_date.is_null()) | (LegendaryPirate.end_date > now))
            )
            .order_by(User.bounty.desc())
        )

    @staticmethod
    def get_latest_active_by_user(user: User) -> "LegendaryPirate | None":
        """
        Get the latest active legendary pirate record for a user
        :param user: The user
        :return: The legendary pirate record
        """

        ensure_legendary_pirate_schema()
        now = datetime.datetime.now()
        return (
            LegendaryPirate.select()
            .where(
                (LegendaryPirate.user == user)
                & ((LegendaryPirate.end_date.is_null()) | (LegendaryPirate.end_date > now))
            )
            .order_by(LegendaryPirate.date.desc())
            .first()
        )


_schema_ensured = False


def ensure_legendary_pirate_schema() -> None:
    """
    Ensure legendary_pirate table has all required columns.
    """

    global _schema_ensured
    if _schema_ensured:
        return

    db = LegendaryPirate._meta.database
    db.connect(reuse_if_open=True)

    if not db.table_exists("legendary_pirate"):
        LegendaryPirate.create_table()
        _schema_ensured = True
        return

    existing_columns = {column.name for column in db.get_columns("legendary_pirate")}
    migrations = {
        "end_date": "ALTER TABLE legendary_pirate ADD COLUMN end_date DATETIME NULL",
        "original_end_date": "ALTER TABLE legendary_pirate ADD COLUMN original_end_date DATETIME NULL",
        "revoke_reason": "ALTER TABLE legendary_pirate ADD COLUMN revoke_reason VARCHAR(999) NULL",
        "is_permanent": "ALTER TABLE legendary_pirate ADD COLUMN is_permanent TINYINT(1) NOT NULL DEFAULT 0",
    }

    for column_name, alter_sql in migrations.items():
        if column_name not in existing_columns:
            db.execute_sql(alter_sql)

    if "is_permanent" in existing_columns or "is_permanent" in migrations:
        db.execute_sql(
            "UPDATE legendary_pirate SET is_permanent = 1 "
            "WHERE end_date IS NULL AND revoke_reason IS NULL AND is_permanent = 0"
        )

    _schema_ensured = True


LegendaryPirate.create_table(safe=True)
