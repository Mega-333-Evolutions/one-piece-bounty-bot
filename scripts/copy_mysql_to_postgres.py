#!/usr/bin/env python3
"""
Copy the whole database of the bot from MySQL / TiDB to PostgreSQL (e.g. Supabase), once.

What it does: reads every table of the old database (only reads, nothing is changed or deleted
there), creates the tables in the new one the way the bot does, copies all the rows with their ids,
sets the id counters of the new database to continue after the copied rows, and then checks that
every table has the same number of rows and the same totals of its number columns.
It all happens in one transaction: if anything goes wrong, nothing is written to the new database.

The new database is the bot's normal database setting (DB_TYPE=postgres and the DB_* variables, in
the environment or in the .env file); the old one is given with SRC_DB_* variables, which only this
script reads:
    SRC_DB_HOST, SRC_DB_PORT, SRC_DB_USER, SRC_DB_PASSWORD, SRC_DB_NAME
The script loads the code of the bot, which refuses to start without BOT_TOKEN, BOT_ID,
BOT_USERNAME, API_ID and API_HASH: they have to be in the .env file too, but the script doesn't
connect to Telegram, so any placeholder value will do. The easiest is a copy of the bot's .env
file with DB_TYPE and DB_* changed to the new database and the SRC_DB_* lines added.

Usage, from the project folder:
    pip install -r requirements.txt
    python scripts/copy_mysql_to_postgres.py [--env-file path/to/.env] [--wipe-target] [--yes]

  --env-file     the .env file to read (default: the .env file of the project, like the bot)
  --wipe-target  empty the bot's tables of the new database first. Needed to run the script again
                 when the new database already has rows (the script refuses to mix with them)
  --yes          don't ask for confirmation

Stop the bot before running it (a bot that keeps running writes to the old database after it was
copied) and start it again with DB_TYPE=postgres when the script has finished.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_ENV_VARIABLES = (
    "SRC_DB_HOST",
    "SRC_DB_PORT",
    "SRC_DB_USER",
    "SRC_DB_PASSWORD",
    "SRC_DB_NAME",
)

# Rows per INSERT
BATCH_SIZE = 500


class CopyError(Exception):
    """An error that stops the copy, with a message that says what to do"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Parse the command line arguments
    :param argv: The arguments, without the name of the script
    :return: The arguments
    """

    parser = argparse.ArgumentParser(
        description="Copy the database of the bot from MySQL/TiDB to PostgreSQL, once."
    )
    parser.add_argument("--env-file", help="The .env file to read (default: the project's .env)")
    parser.add_argument(
        "--wipe-target",
        action="store_true",
        help="Empty the bot's tables of the new database first",
    )
    parser.add_argument("--yes", action="store_true", help="Don't ask for confirmation")
    return parser.parse_args(argv)


def build_source_database() -> Any:
    """
    Connect to the old database (MySQL / TiDB) with the SRC_DB_* environment variables
    :return: The peewee database, not connected yet
    """

    from peewee import MySQLDatabase

    missing = [name for name in SOURCE_ENV_VARIABLES if not os.environ.get(name)]
    if missing:
        raise CopyError(
            "These environment variables of the old (MySQL/TiDB) database are not set: "
            + ", ".join(missing)
        )

    return MySQLDatabase(
        os.environ["SRC_DB_NAME"],
        host=os.environ["SRC_DB_HOST"],
        port=int(os.environ["SRC_DB_PORT"]),
        user=os.environ["SRC_DB_USER"],
        password=os.environ["SRC_DB_PASSWORD"],
        charset="utf8mb4",
        # Same as the bot: TiDB needs an encrypted connection
        ssl={"ssl": {}},
    )


def load_models() -> tuple[list[Any], Any]:
    """
    Import all the models of the bot (importing them creates the tables that don't exist yet in the
    database of the bot, which is the new database) and get them with the parents first, so that
    a row is always copied after the rows it points to
    :return: The models, the database of the bot (the new one)
    """

    import importlib
    import pkgutil

    from peewee import sort_models

    import src.model as model_package
    from src.model.BaseModel import BaseModel, db_obj

    for module in pkgutil.iter_modules(model_package.__path__):
        if not module.ispkg:
            importlib.import_module(f"src.model.{module.name}")

    def all_subclasses(cls: type) -> set[type]:
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses |= all_subclasses(subclass)
        return subclasses

    models = sorted(all_subclasses(BaseModel), key=lambda model: model._meta.table_name)
    return sort_models(models), db_obj.get_db()


def describe(db: Any) -> str:
    """
    :param db: A peewee database
    :return: Where the database is, e.g. "mydb on host:5432"
    """

    port = db.connect_params.get("port")
    return f"{db.database} on {db.connect_params.get('host')}" + (f":{port}" if port else "")


def same_database(source_db: Any, target_db: Any) -> bool:
    """
    :return: Whether the two peewee databases are the same database (same name, host and port)
    """

    def identity(db: Any) -> tuple:
        return (
            str(db.database),
            str(db.connect_params.get("host")).lower(),
            str(db.connect_params.get("port")),
        )

    return identity(source_db) == identity(target_db)


def check_source(source_db: Any, models: list[Any]) -> None:
    """
    Check that every table of the bot is in the old database with every column the bot needs
    :param source_db: The old database
    :param models: The models
    :return: None, raises CopyError if something is missing
    """

    tables = set(source_db.get_tables())
    for model in models:
        table = model._meta.table_name
        if table not in tables:
            raise CopyError(
                f"The old database has no table '{table}'. Is SRC_DB_NAME the database of the bot?"
            )

        columns = {column.name for column in source_db.get_columns(table)}
        missing = [
            f.column_name for f in model._meta.sorted_fields if f.column_name not in columns
        ]
        if missing:
            raise CopyError(
                f"The table '{table}' of the old database has no column {', '.join(missing)}. "
                f"Start the bot once on the old database (it adds the missing columns by itself) "
                f"and run this script again"
            )


def count_rows(db: Any, model: Any) -> int:
    """
    :return: The number of rows of the table of the model in the database
    """

    with db.bind_ctx([model], bind_refs=False, bind_backrefs=False):
        return model.select().count()


def fingerprint(db: Any, model: Any) -> tuple[int, dict[str, int]]:
    """
    Describe the content of a table: the number of rows and the total of every number column.
    The same table in the old and the new database must have the same fingerprint
    :param db: The database
    :param model: The model
    :return: The number of rows, the total of every number column by column name
    """

    from peewee import ForeignKeyField, IntegerField, fn

    with db.bind_ctx([model], bind_refs=False, bind_backrefs=False):
        totals = {}
        for field in model._meta.sorted_fields:
            if isinstance(field, (IntegerField, ForeignKeyField)):
                total = model.select(fn.SUM(field)).scalar()
                totals[field.column_name] = int(total or 0)

        return model.select().count(), totals


def read_rows(source_db: Any, model: Any, fields: list[Any]) -> list[tuple]:
    """
    Read all the rows of a table of the old database, in the order of their ids
    :param source_db: The old database
    :param model: The model
    :param fields: The fields to read
    :return: The rows, as tuples with the values in the order of the fields
    """

    with source_db.bind_ctx([model], bind_refs=False, bind_backrefs=False):
        query = model.select(*fields).order_by(model._meta.primary_key)
        return list(query.tuples())


def copy_table(source_db: Any, model: Any, stats: dict[str, int]) -> int:
    """
    Copy all the rows of a table from the old database to the new one (the database the model is
    bound to). To be called inside a transaction of the new database
    :param source_db: The old database
    :param model: The model
    :param stats: Counters of what was changed on the way, updated
    :return: The number of rows copied
    """

    from peewee import ForeignKeyField

    fields = list(model._meta.sorted_fields)
    primary_key_index = fields.index(model._meta.primary_key)

    # A row that points to another row of the same table (e.g. the revenge of a fight) is first
    # written without the link, and the link is added when all the rows are there
    self_links = [
        index
        for index, field in enumerate(fields)
        if isinstance(field, ForeignKeyField) and field.rel_model is model and field.null
    ]

    rows = []
    links_to_add = []  # (id of the row, index of the field, id of the row it points to)
    for row in read_rows(source_db, model, fields):
        values = list(row)
        for index, value in enumerate(values):
            # PostgreSQL text can't contain the NUL character (MySQL's can)
            if isinstance(value, str) and "\x00" in value:
                values[index] = value.replace("\x00", "")
                stats["nul_characters_removed"] += 1

        for index in self_links:
            if values[index] is not None:
                links_to_add.append((values[primary_key_index], index, values[index]))
                values[index] = None

        rows.append(values)

    for start in range(0, len(rows), BATCH_SIZE):
        model.insert_many(rows[start : start + BATCH_SIZE], fields=fields).execute()

    for row_id, index, linked_id in links_to_add:
        model.update({fields[index]: linked_id}).where(model._meta.primary_key == row_id).execute()

    return len(rows)


def reset_sequences(target_db: Any, models: list[Any]) -> None:
    """
    Make the id counter of every table continue after the highest id copied. Without this, the
    first new row of a table would get id 1 and fail because that id is already taken
    :param target_db: The new (PostgreSQL) database
    :param models: The models
    :return: None
    """

    for model in models:
        table = model._meta.table_name
        column = model._meta.primary_key.column_name

        sequence = target_db.execute_sql(
            "SELECT pg_get_serial_sequence(%s, %s)", (f'"{table}"', column)
        ).fetchone()[0]
        if sequence is None:
            raise CopyError(f"The table '{table}' has no id counter in the new database")

        target_db.execute_sql(
            f'SELECT setval(%s, COALESCE((SELECT MAX("{column}") FROM "{table}"), 0) + 1, false)',
            (sequence,),
        )


def copy_database(
    source_db: Any,
    target_db: Any,
    models: list[Any],
    wipe_target: bool = False,
    log=print,
) -> dict[str, int]:
    """
    Copy all the tables of the bot from the old database to the new one and check the result
    :param source_db: The old database (MySQL / TiDB), only read
    :param target_db: The new database (PostgreSQL), the one the models are bound to
    :param models: The models, parents first
    :param wipe_target: Whether to empty the tables of the new database first
    :param log: Function that prints a line
    :return: The number of rows copied by table name
    """

    from peewee import PostgresqlDatabase

    if not isinstance(target_db, PostgresqlDatabase):
        raise CopyError(
            "The new database must be PostgreSQL: set DB_TYPE=postgres and the DB_* variables"
        )

    if same_database(source_db, target_db):
        raise CopyError("The old and the new database are the same database")

    check_source(source_db, models)

    # The new database must be empty: the copy doesn't merge with rows that are already there
    target_counts = {model._meta.table_name: count_rows(target_db, model) for model in models}
    not_empty = {table: count for table, count in target_counts.items() if count > 0}
    if not_empty and not wipe_target:
        shown = list(not_empty.items())[:5]
        more = len(not_empty) - len(shown)
        raise CopyError(
            "The new database already has rows ("
            + ", ".join(f"{table}: {count}" for table, count in shown)
            + (f" and {more} more tables" if more > 0 else "")
            + "). To replace them with a fresh copy, run the script again with --wipe-target"
        )

    stats = {"nul_characters_removed": 0}
    copied: dict[str, int] = {}

    # Everything, including the check of the result, is in one transaction: when something is wrong
    # nothing is written to the new database
    with target_db.atomic():
        if wipe_target:
            names = ", ".join(f'"{model._meta.table_name}"' for model in models)
            target_db.execute_sql(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE")

        for model in models:
            copied[model._meta.table_name] = copy_table(source_db, model, stats)
            log(f"  {model._meta.table_name:<40} {copied[model._meta.table_name]:>8} rows")

        reset_sequences(target_db, models)

        # Check the result: same number of rows and same totals in every table
        problems = []
        for model in models:
            expected = fingerprint(source_db, model)
            actual = fingerprint(target_db, model)
            if expected != actual:
                problems.append(f"{model._meta.table_name}: old {expected} / new {actual}")

        if problems:
            raise CopyError(
                "The tables are not the same in the two databases after the copy:\n  "
                + "\n  ".join(problems)
            )

    if stats["nul_characters_removed"]:
        log(
            f"Note: {stats['nul_characters_removed']} NUL character(s) were removed from texts "
            f"(PostgreSQL can't store them)"
        )

    return copied


def main(argv: list[str] | None = None) -> int:
    """
    Run the script
    :param argv: The command line arguments, without the name of the script
    :return: The exit code
    """

    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.env_file and not os.path.isfile(args.env_file):
        print(f"The .env file {args.env_file} does not exist")
        return 1

    # resources/Environment.py reads the first command line argument as the path of the .env file
    sys.argv = [sys.argv[0]] + ([args.env_file] if args.env_file else [])
    sys.path.insert(0, ROOT_DIR)

    try:
        source_db = build_source_database()
        models, target_db = load_models()

        print(f"Old database (MySQL/TiDB): {describe(source_db)}")
        print(f"New database (PostgreSQL): {describe(target_db)}")
        if args.wipe_target:
            print("The bot's tables of the new database will be EMPTIED first (--wipe-target).")

        if not args.yes and input("Type 'copy' to continue: ").strip().lower() != "copy":
            print("Cancelled, nothing was changed.")
            return 1

        copied = copy_database(source_db, target_db, models, wipe_target=args.wipe_target)
    except CopyError as e:
        print(f"\nStopped, nothing was written to the new database: {e}")
        return 1

    print(f"\nDone: {sum(copied.values())} rows in {len(copied)} tables copied and checked.")
    print("Now set DB_TYPE=postgres and the DB_* variables of the new database wherever the bot")
    print("runs, and start the bot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
