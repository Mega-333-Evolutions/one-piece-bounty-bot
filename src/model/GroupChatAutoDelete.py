import datetime

from peewee import *

from src.model.BaseModel import BaseModel
from src.model.GroupChat import GroupChat


class GroupChatAutoDelete(BaseModel):
    """
    Group Chat Auto Delete class
    """

    group_chat: GroupChat | ForeignKeyField = ForeignKeyField(
        GroupChat, backref="auto_delete", on_delete="CASCADE"
    )
    message_id: int | IntegerField = IntegerField()
    delete_date: datetime.datetime | DateTimeField = DateTimeField()

    class Meta:
        db_table = "group_chat_auto_delete"


GroupChatAutoDelete.create_table()

# Auto-migrate: index delete_date. This column is queried every minute by auto_delete()
# (WHERE delete_date < NOW() ... LIMIT 20) with no index, forcing a full table scan on every
# single run, 24/7 - a steady, avoidable cost on a usage-billed database.
try:
    from playhouse.migrate import MySQLMigrator, migrate as pw_migrate
    from src.model.BaseModel import db_obj

    _migrator = MySQLMigrator(db_obj.get_db())
    pw_migrate(
        _migrator.add_index("group_chat_auto_delete", ("delete_date",), unique=False),
    )
except Exception:
    pass  # Index already exists
