from peewee import MySQLDatabase
from playhouse.shortcuts import ReconnectMixin

import resources.Environment as Env

# Removed the ABC inheritance as it is unnecessary here
class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


class Database:
    def __init__(self):
        self.db = ReconnectMySQLDatabase(
            Env.DB_NAME.get(),
            host=Env.DB_HOST.get(),
            port=Env.DB_PORT.get_int(),
            user=Env.DB_USER.get(),
            password=Env.DB_PASSWORD.get(),
            charset="utf8mb4",
            ssl={'ssl': {}}  # <-- Added the SSL requirement for TiDB here
        )

    def get_db(self):
        # Let Peewee and ReconnectMixin manage the connection lifecycle automatically!
        # Do NOT manually check usability or force .connect() here.
        return self.db

    def close(self):
        # Safely check if the connection is already closed before closing
        if not self.db.is_closed():
            self.db.close()

    def __del__(self):
        self.close()
