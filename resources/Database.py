from peewee import InterfaceError, MySQLDatabase, OperationalError, PostgresqlDatabase
from playhouse.shortcuts import ReconnectMixin

import resources.Environment as Env

# Values accepted by the DB_TYPE environment variable
DB_TYPES_MYSQL = ("mysql", "mariadb", "tidb")
DB_TYPES_POSTGRES = ("postgres", "postgresql")


# Removed the ABC inheritance as it is unnecessary here
class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


class ReconnectPostgresDatabase(ReconnectMixin, PostgresqlDatabase):
    """
    PostgreSQL database that reconnects by itself when the server has dropped the connection
    (server restart, idle timeout, connection pooler, a paused free-tier project being resumed...).

    peewee's ReconnectMixin only knows the MySQL error codes, so without the PostgreSQL messages
    below the bot would keep failing on every query after a dropped connection until restarted
    """

    reconnect_errors = ReconnectMixin.reconnect_errors + (
        (OperationalError, "terminating connection"),
        (OperationalError, "server closed the connection"),
        (OperationalError, "ssl syscall error"),
        (OperationalError, "ssl connection has been closed"),
        (OperationalError, "could not receive data from server"),
        (OperationalError, "could not send data to server"),
        (OperationalError, "connection already closed"),
        (InterfaceError, "connection already closed"),
    )


class Database:
    def __init__(self):
        db_type = Env.DB_TYPE.get().strip().lower()

        if db_type in DB_TYPES_POSTGRES:
            self.db = ReconnectPostgresDatabase(
                Env.DB_NAME.get(),
                host=Env.DB_HOST.get(),
                port=Env.DB_PORT.get_int(),
                user=Env.DB_USER.get(),
                password=Env.DB_PASSWORD.get(),
                sslmode=Env.DB_SSL_MODE.get(),
                application_name="one_piece_bounty_bot",
                # Fail instead of hanging when the server can not be reached
                connect_timeout=10,
                # Notice a connection that was silently dropped (NAT, pooler, paused project) instead
                # of waiting minutes on it: probe an idle connection after 30 seconds and give up on
                # data that stays unacknowledged for 30 seconds
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=3,
                tcp_user_timeout=30000,
            )
        elif db_type in DB_TYPES_MYSQL:
            self.db = ReconnectMySQLDatabase(
                Env.DB_NAME.get(),
                host=Env.DB_HOST.get(),
                port=Env.DB_PORT.get_int(),
                user=Env.DB_USER.get(),
                password=Env.DB_PASSWORD.get(),
                charset="utf8mb4",
                ssl={"ssl": {}},  # <-- Added the SSL requirement for TiDB here
            )
        else:
            raise Exception(
                f"Unsupported DB_TYPE '{Env.DB_TYPE.get()}'. Use 'mysql' (MySQL, MariaDB, TiDB) or "
                f"'postgres' (PostgreSQL, Supabase)"
            )

    def get_db(self):
        # Let Peewee and ReconnectMixin manage the connection lifecycle automatically!
        # Do NOT manually check usability or force .connect() here.
        return self.db

    def close(self):
        # Safely check if the connection is already closed before closing (self.db does not exist
        # when the constructor failed, e.g. because of an unsupported DB_TYPE)
        db = getattr(self, "db", None)
        if db is not None and not db.is_closed():
            db.close()

    def __del__(self):
        self.close()
