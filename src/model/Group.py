import datetime

from peewee import *

from src.model.BaseModel import BaseModel
from src.model.User import User
from src.model.enums.Language import Language, LANGUAGE_DEFAULT


class Group(BaseModel):
    """
    Group class
    """

    tg_group_id = CharField(unique=True)
    tg_group_name = CharField()
    tg_group_username = CharField(null=True)
    is_forum = BooleanField(default=False)
    last_message_date = DateTimeField(default=datetime.datetime.now)
    last_error_date = DateTimeField(null=True)
    last_error_message = CharField(null=True)
    is_active = BooleanField(default=True)
    is_muted = BooleanField(default=False)
    language = CharField(max_length=5, default=LANGUAGE_DEFAULT.value)

    # Backref
    group_chats = None

    class Meta:
        db_table = "group"

    def get_active_users(self) -> list[User]:
        """
        Get the active users in the group
        :return: The active users in the group
        """
        from src.model.GroupUser import GroupUser

        return (
            User()
            .select()
            .join(GroupUser)
            .join(Group)
            .where((Group.id == self.id) & (GroupUser.is_active == True))
        )

    def get_active_users_ids(self) -> list[int]:
        """
        Get the active users ids in the group
        :return: The active users ids in the group
        """

        return [user.id for user in self.get_active_users()]

    def get_language(self) -> Language:
        """
        Returns the language of the group, used for texts sent in this group's chat
        :return: The language of the group
        """

        try:
            return Language(self.language)
        except ValueError:
            return LANGUAGE_DEFAULT


Group.create_table()

# Auto-migrate: add language column for the group language setting
try:
    from playhouse.migrate import MySQLMigrator, migrate as pw_migrate
    from src.model.BaseModel import db_obj

    _migrator = MySQLMigrator(db_obj.get_db())
    pw_migrate(
        _migrator.add_column(
            "group", "language", CharField(max_length=5, default=LANGUAGE_DEFAULT.value)
        ),
    )
except Exception:
    pass  # Column already exists
