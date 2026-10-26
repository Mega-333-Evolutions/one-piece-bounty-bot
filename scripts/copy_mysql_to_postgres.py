#!/usr/bin/env python3
"""
Copy the whole database of the bot from MySQL / TiDB to PostgreSQL (e.g. Supabase), once.

What it does: reads every table of the old database (only reads, nothing is changed or deleted
there), creates the tables in the new one the way the bot does, copies all the rows with their ids,
sets the id counters of the new database to continue after the copied rows, and then checks that
every table has the same number of rows and the same totals of its number columns.
It all happens in one transaction: if anything goes wrong, nothing is written to the new database.

MySQL accepts some values that PostgreSQL refuses, so these are changed on the way and listed when
the copy has finished:
  - "empty" dates (0000-00-00 00:00:00, or a date with month or day 00): left empty (NULL) where the
    column can be empty, replaced with 1970-01-01 00:00:00 where it can't (like the empty date,
    that is older than any real date)
  - NUL characters in texts: removed
  - a link to a row that doesn't exist (a database that doesn't enforce its foreign keys can have
    them): cleared (NULL) where the column can be empty. Where it can't, the row can't be copied:
    the script then stops and lists them, and with --drop-orphans it leaves them out instead (they
    stay in the old database)
If PostgreSQL refuses some rows for another reason, the script lists all of them at once (table,
ids, why) and writes nothing.

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
                                             [--drop-orphans]

  --env-file      the .env file to read (default: the .env file of the project, like the bot)
  --wipe-target   empty the bot's tables of the new database first. Needed to run the script again
                  when the new database already has rows (the script refuses to mix with them)
  --drop-orphans  leave out the rows that point to a row that doesn't exist and can't be fixed by
                  clearing the link (see above)
  --yes           don't ask for confirmation

Stop the bot before running it (a bot that keeps running writes to the old database after it was
copied) and start it again with DB_TYPE=postgres when the script has finished.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from collections import Counter
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

# What an empty date of MySQL becomes in a column that can't be empty. Like the empty date, it is
# older than any real date of the bot, so "is it before ..." questions get the same answer
EMPTY_DATE_REPLACEMENT = datetime.datetime(1970, 1, 1)

# When PostgreSQL refuses a batch of rows, the batch is split again and again to find the rows it
# refuses. This is how many such rows of one table are looked for (the rest is only counted)
MAX_REFUSED_ROWS_LISTED = 100

# How many ids of rows are shown in a list
MAX_IDS_SHOWN = 10

# A date as MySQL writes it (what is left of an empty date once the driver gave up on it)
DATE_TEXT_PATTERN = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})")


class CopyError(Exception):
    """An error that stops the copy, with a message that says what to do"""


class CopyState:
    """
    What is known about the copy while it runs
    """

    def __init__(self, drop_orphans: bool = False):
        # Leave out the rows that point to a row that doesn't exist, instead of stopping
        self.drop_orphans: bool = drop_orphans

        # What was changed on the way: (kind, table, column) -> how many values were changed
        self.changes: Counter = Counter()

        # model -> ids of the rows of the table in the old database
        self.source_ids: dict = {}

        # model -> ids of the rows of the table that are in the new database
        self.copied_ids: dict = {}

        # (table, column, table it points to) -> (id of the row, id it points to, whether that row
        # doesn't exist in the old database either) of the rows that were left out because the column
        # points to a row that isn't in the new database, and can't be cleared
        self.left_out: dict = {}

        # (table, reason) -> ids of the rows that PostgreSQL refuses (None stands for rows that were
        # not looked at one by one)
        self.refused: dict = {}

        # table -> (number of rows, totals of the number columns) of the rows that were inserted
        self.expected: dict = {}


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
    parser.add_argument(
        "--drop-orphans",
        action="store_true",
        help="Leave out the rows that point to a row that doesn't exist, instead of stopping "
        "(they stay in the old database)",
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


def rows_fingerprint(fields: list[Any], rows: list[list]) -> tuple[int, dict[str, int]]:
    """
    The same as fingerprint(), for rows that are in memory
    :param fields: The fields of the table, in the order of the values of the rows
    :param rows: The rows
    :return: The number of rows, the total of every number column by column name
    """

    from peewee import ForeignKeyField, IntegerField

    totals = {}
    for index, field in enumerate(fields):
        if isinstance(field, (IntegerField, ForeignKeyField)):
            totals[field.column_name] = sum(
                int(row[index]) for row in rows if row[index] is not None
            )

    return len(rows), totals


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


def parse_date_text(text: str, date_only: bool) -> datetime.date | None:
    """
    Read a date that the driver left as text: the ones that are a real date, in a form peewee
    doesn't know, are kept
    :param text: The text
    :param date_only: True if the column holds dates without a time
    :return: The date, or None if the text is not a real date
    """

    try:
        parsed = datetime.datetime.fromisoformat(text.strip())
    except ValueError:
        return None

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    return parsed.date() if date_only else parsed


def fix_date(field: Any, value: Any) -> tuple[Any, str | None]:
    """
    Make the value of a date column something PostgreSQL accepts. MySQL can hold "empty" dates
    (0000-00-00 00:00:00, or 2020-00-10) that are not a day of the calendar; the driver hands them
    over as text, or as None. In a column that can be empty the value becomes NULL, in the others
    the earliest date
    :param field: The date field (DateTimeField or DateField)
    :param value: The value as the driver gave it
    :return: The value to copy, and what was wrong with the old one: None if nothing,
    "empty_date" for an empty date, "invalid_date" for a text that is not a date at all
    """

    from peewee import DateField

    date_only = isinstance(field, DateField)

    if value is None:
        if field.null:
            return None, None

        # Not null in the old database either: the driver turned the empty date into None
        problem = "empty_date"
    elif isinstance(value, str):
        parsed = parse_date_text(value, date_only)
        if parsed is not None:
            return parsed, None

        # 0000-00-00, 2020-00-10, 2020-05-00: a year, month or day 0
        match = DATE_TEXT_PATTERN.match(value)
        is_empty_date = match is not None and 0 in (int(part) for part in match.groups())
        problem = "empty_date" if is_empty_date else "invalid_date"
    else:
        return value, None

    if field.null:
        return None, problem

    return (EMPTY_DATE_REPLACEMENT.date() if date_only else EMPTY_DATE_REPLACEMENT), problem


def short_error(error: Exception) -> str:
    """
    :param error: A database error
    :return: What it says, in one line (without the part of the query that PostgreSQL repeats)
    """

    lines = [
        line.strip()
        for line in str(error).splitlines()
        if line.strip() and not line.startswith("LINE ") and set(line.strip()) != {"^"}
    ]
    return " ".join(lines[:2])[:300]


def format_ids(ids: list) -> str:
    """
    :param ids: Ids of rows
    :return: Some of them, e.g. "ids 4, 9, 12" or "ids 1, 2, 3 ... and 40 more"
    """

    shown = ", ".join(str(row_id) for row_id in ids[:MAX_IDS_SHOWN])
    more = len(ids) - MAX_IDS_SHOWN
    return f"id{'s' if len(ids) > 1 else ''} {shown}" + (f" and {more} more" if more > 0 else "")


def prepare_rows(model: Any, fields: list[Any], rows: list[tuple], state: CopyState) -> list[list]:
    """
    Get the rows of the old database ready for PostgreSQL: values it refuses are changed (and
    counted in the state) and the rows that can't be copied are left out (and listed in the state)
    :param model: The model
    :param fields: The fields, in the order of the values of the rows
    :param rows: The rows as read from the old database
    :param state: What is known about the copy, updated
    :return: The rows to insert
    """

    from peewee import DateField, DateTimeField, ForeignKeyField

    table = model._meta.table_name
    primary_key_index = fields.index(model._meta.primary_key)

    # Links to rows of other tables are only checked against the rows that really were copied
    links = []
    for index, field in enumerate(fields):
        if (
            isinstance(field, ForeignKeyField)
            and field.rel_model is not model
            and field.rel_model in state.copied_ids
            and field.rel_field is field.rel_model._meta.primary_key
        ):
            links.append((index, field, state.copied_ids[field.rel_model]))

    prepared = []
    for row in rows:
        values = list(row)
        changes = []  # What was changed in this row, counted in the state if the row is copied

        for index, field in enumerate(fields):
            value = values[index]

            if isinstance(field, (DateTimeField, DateField)):
                values[index], problem = fix_date(field, value)
                if problem:
                    outcome = "left_empty" if field.null else "replaced"
                    changes.append((f"{problem}_{outcome}", table, field.column_name))
            # PostgreSQL text can't contain the NUL character (MySQL's can)
            elif isinstance(value, str) and "\x00" in value:
                values[index] = value.replace("\x00", "")
                changes.append(("nul_removed", table, field.column_name))

        is_left_out = False
        for index, field, parent_ids in links:
            if values[index] is None or values[index] in parent_ids:
                continue

            if field.null:
                values[index] = None
                changes.append(("link_cleared", table, field.column_name))
            else:
                parent = field.rel_model
                key = (table, field.column_name, parent._meta.table_name)
                state.left_out.setdefault(key, []).append(
                    (
                        values[primary_key_index],
                        values[index],
                        values[index] not in state.source_ids.get(parent, ()),
                    )
                )
                is_left_out = True

        if not is_left_out:
            prepared.append(values)
            state.changes.update(changes)

    return prepared


def insert_rows(
    target_db: Any, model: Any, fields: list[Any], rows: list[list], state: CopyState
) -> set:
    """
    Insert rows in the new database. When PostgreSQL refuses a batch, the batch is split in two
    again and again (each try in its own savepoint, so the transaction goes on) until the rows it
    refuses are alone: they are listed in the state, with the reason
    :param target_db: The new database, inside a transaction
    :param model: The model
    :param fields: The fields, in the order of the values of the rows
    :param rows: The rows to insert
    :param state: What is known about the copy, updated
    :return: The ids of the rows that were inserted
    """

    from peewee import DataError, IntegrityError

    table = model._meta.table_name
    primary_key_index = fields.index(model._meta.primary_key)
    refused_errors = (DataError, IntegrityError, ValueError)

    inserted = set()
    found = 0  # Rows of this table that PostgreSQL refuses, found so far

    def insert(batch: list[list]) -> None:
        nonlocal found

        try:
            with target_db.atomic():
                model.insert_many(batch, fields=fields).execute()
            inserted.update(row[primary_key_index] for row in batch)
            return
        except refused_errors as error:
            reason = short_error(error)

        if len(batch) == 1:
            found += 1
            state.refused.setdefault((table, reason), []).append(batch[0][primary_key_index])
        elif found >= MAX_REFUSED_ROWS_LISTED:
            # Enough of them are known: the others are only counted (None stands for a row)
            state.refused.setdefault((table, reason), []).extend([None] * len(batch))
        else:
            middle = len(batch) // 2
            insert(batch[:middle])
            insert(batch[middle:])

    for start in range(0, len(rows), BATCH_SIZE):
        insert(rows[start : start + BATCH_SIZE])

    return inserted


def copy_table(source_db: Any, target_db: Any, model: Any, state: CopyState) -> int:
    """
    Copy all the rows of a table from the old database to the new one. To be called inside a
    transaction of the new database
    :param source_db: The old database
    :param target_db: The new database
    :param model: The model
    :param state: What is known about the copy, updated
    :return: The number of rows copied
    """

    from peewee import ForeignKeyField

    fields = list(model._meta.sorted_fields)
    primary_key_index = fields.index(model._meta.primary_key)
    table = model._meta.table_name

    read = read_rows(source_db, model, fields)

    # What was read must be what the old database says it has (a bot that is still running, or a
    # driver that loses something, would show here)
    expected = fingerprint(source_db, model)
    actual = rows_fingerprint(fields, read)
    if expected != actual:
        raise CopyError(
            f"The table '{table}' of the old database changed while it was read (is the bot still "
            f"running?): {expected} / {actual}"
        )

    state.source_ids[model] = {row[primary_key_index] for row in read}
    rows = prepare_rows(model, fields, read, state)

    # A row that points to another row of the same table (e.g. the revenge of a fight) is first
    # written without the link, and the link is added when all the rows are there
    self_links = [
        index
        for index, field in enumerate(fields)
        if isinstance(field, ForeignKeyField) and field.rel_model is model and field.null
    ]

    row_ids = {row[primary_key_index] for row in rows}
    for values in rows:
        for index in self_links:
            if values[index] is not None and values[index] not in row_ids:
                values[index] = None
                state.changes[("link_cleared", table, fields[index].column_name)] += 1

    # What the table must look like in the new database, with its links
    state.expected[table] = rows_fingerprint(fields, rows)

    links_to_add = []  # (id of the row, index of the field, id of the row it points to)
    for values in rows:
        for index in self_links:
            if values[index] is not None:
                links_to_add.append((values[primary_key_index], index, values[index]))
                values[index] = None

    inserted = insert_rows(target_db, model, fields, rows, state)
    state.copied_ids[model] = inserted

    for row_id, index, linked_id in links_to_add:
        if row_id in inserted and linked_id in inserted:
            model.update({fields[index]: linked_id}).where(
                model._meta.primary_key == row_id
            ).execute()

    return len(inserted)


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


def does_not_exist(ids: list) -> str:
    """
    :param ids: Ids of rows that don't exist
    :return: "doesn't exist" or "don't exist"
    """

    return "don't exist" if len(ids) > 1 else "doesn't exist"


def split_left_out(state: CopyState) -> tuple[list[tuple], dict[str, int]]:
    """
    :param state: What is known about the copy
    :return: The rows that were left out because they point to a row that doesn't exist in the old
    database, as (table, column, table it points to, ids of the rows, ids they point to), and the
    number of other rows that were left out by table (those point to a row that does exist in the
    old database, but that was left out or is refused itself)
    """

    roots = []
    root_rows = set()  # (table, id of the row)
    for (table, column, parent), entries in sorted(state.left_out.items()):
        found = [(row_id, parent_id) for row_id, parent_id, is_root in entries if is_root]
        if found:
            roots.append(
                (
                    table,
                    column,
                    parent,
                    [row_id for row_id, _ in found],
                    sorted({parent_id for _, parent_id in found}),
                )
            )
            root_rows.update((table, row_id) for row_id, _ in found)

    dependents: dict[str, int] = {}
    counted = set()  # A row with several links to rows that are left out is counted once
    for (table, _, _), entries in state.left_out.items():
        for row_id, _, is_root in entries:
            if not is_root and (table, row_id) not in root_rows and (table, row_id) not in counted:
                counted.add((table, row_id))
                dependents[table] = dependents.get(table, 0) + 1

    return roots, dependents


def describe_changes(state: CopyState) -> list[str]:
    """
    :param state: What is known about the copy
    :return: A line for every kind of value that was changed on the way, and for the rows left out
    """

    replacement = EMPTY_DATE_REPLACEMENT.strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    for (kind, table, column), count in sorted(state.changes.items()):
        where = f"{table}.{column}"
        if kind == "empty_date_left_empty":
            lines.append(
                f"{where}: {count} empty date(s) (0000-00-00) of MySQL left empty (NULL), "
                f"PostgreSQL has no such date"
            )
        elif kind == "empty_date_replaced":
            lines.append(
                f"{where}: {count} empty date(s) (0000-00-00) of MySQL replaced with {replacement}, "
                f"PostgreSQL has no such date and this column can't be empty"
            )
        elif kind == "invalid_date_left_empty":
            lines.append(f"{where}: {count} text(s) that are not a date left empty (NULL)")
        elif kind == "invalid_date_replaced":
            lines.append(
                f"{where}: {count} text(s) that are not a date replaced with {replacement}, "
                f"this column can't be empty"
            )
        elif kind == "nul_removed":
            lines.append(
                f"{where}: the NUL character was removed from {count} text(s), PostgreSQL can't "
                f"store it"
            )
        elif kind == "link_cleared":
            lines.append(
                f"{where}: {count} link(s) to a row that doesn't exist were cleared (NULL)"
            )

    roots, dependents = split_left_out(state)
    for table, column, parent, ids, parent_ids in roots:
        lines.append(
            f"{table}: {len(ids)} row(s) ({format_ids(ids)}) left out because their {column} "
            f"points to '{parent}' {format_ids(parent_ids)}, which {does_not_exist(parent_ids)}; "
            f"they stay in the old database"
        )
    for table, count in sorted(dependents.items()):
        lines.append(
            f"{table}: {count} more row(s) left out because they belong to rows that are left "
            f"out; they stay in the old database"
        )

    return lines


def describe_problems(state: CopyState) -> str:
    """
    :param state: What is known about the copy
    :return: What can't be copied as it is, with what to do about it
    """

    parts = []

    if state.refused:
        lines = []
        for (table, reason), ids in sorted(state.refused.items()):
            known = [row_id for row_id in ids if row_id is not None]
            not_examined = len(ids) - len(known)

            if known:
                rows = f"{len(known)} row(s) ({format_ids(known)})"
                if not_examined:
                    rows += f" and {not_examined} more that were not looked at one by one"
            else:
                rows = f"{not_examined} row(s) (not looked at one by one)"

            lines.append(f"  - {table}: {rows}: {reason}")

        parts.append("PostgreSQL refuses these rows:\n" + "\n".join(lines))

    roots, dependents = split_left_out(state)

    if roots:
        lines = [
            f"  - {table}.{column}: {len(ids)} row(s) ({format_ids(ids)}) point to '{parent}' "
            f"{format_ids(parent_ids)}, which {does_not_exist(parent_ids)}"
            for table, column, parent, ids, parent_ids in roots
        ]
        parts.append(
            "These rows point to a row that doesn't exist in the old database, and the link can't "
            "be cleared because the column can't be empty:\n" + "\n".join(lines)
        )

    if dependents:
        lines = [f"  - {table}: {count} row(s)" for table, count in sorted(dependents.items())]
        parts.append(
            "These rows belong to rows that can't be copied (the rows above), so they can't be "
            "copied either:\n" + "\n".join(lines)
        )

    if state.left_out:
        if state.refused:
            advice = (
                "Fix the rows PostgreSQL refuses in the old database first, then run the script "
                "again."
            )
            if roots:
                advice += (
                    " The rows that point to a row that doesn't exist can then be left out with "
                    "--drop-orphans (they stay in the old database)."
                )
        else:
            advice = (
                "Run the script again with --drop-orphans to leave all of these rows out (they "
                "stay in the old database), or fix them in the old database first."
            )
        parts.append(advice)

    return "\n\n".join(parts)


def copy_database(
    source_db: Any,
    target_db: Any,
    models: list[Any],
    wipe_target: bool = False,
    log=print,
    drop_orphans: bool = False,
    state: CopyState | None = None,
) -> dict[str, int]:
    """
    Copy all the tables of the bot from the old database to the new one and check the result
    :param source_db: The old database (MySQL / TiDB), only read
    :param target_db: The new database (PostgreSQL), the one the models are bound to
    :param models: The models, parents first
    :param wipe_target: Whether to empty the tables of the new database first
    :param log: Function that prints a line
    :param drop_orphans: Whether to leave out the rows that point to a row that doesn't exist (and
    can't be fixed by clearing the link) instead of stopping
    :param state: Where to keep what is known about the copy (a new one by default)
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

    if state is None:
        state = CopyState()
    state.drop_orphans = drop_orphans

    copied: dict[str, int] = {}

    # Everything, including the check of the result, is in one transaction: when something is wrong
    # nothing is written to the new database
    with target_db.atomic():
        if wipe_target:
            names = ", ".join(f'"{model._meta.table_name}"' for model in models)
            target_db.execute_sql(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE")

        for model in models:
            table = model._meta.table_name
            changes_before = sum(state.changes.values())

            copied[table] = copy_table(source_db, target_db, model, state)

            notes = []
            if sum(state.changes.values()) > changes_before:
                notes.append("values changed, see below")
            # The rows left out of a table are only added to the state while that table is copied
            if any(key[0] == table for key in state.left_out):
                notes.append("rows left out, see below")
            log(
                f"  {table:<40} {copied[table]:>8} rows"
                + (f"  ({'; '.join(notes)})" if notes else "")
            )

        # Rows that can't be copied: all of them are listed at once, and nothing is written
        if state.refused or (state.left_out and not drop_orphans):
            raise CopyError(
                "The old database has data that can't be copied as it is.\n\n"
                + describe_problems(state)
            )

        reset_sequences(target_db, models)

        # Check the result: same rows and same totals in every table as what was inserted
        problems = []
        for model in models:
            expected = state.expected[model._meta.table_name]
            actual = fingerprint(target_db, model)
            if expected != actual:
                problems.append(f"{model._meta.table_name}: expected {expected} / new {actual}")

        if problems:
            raise CopyError(
                "The tables are not the same in the two databases after the copy:\n  "
                + "\n  ".join(problems)
            )

    lines = describe_changes(state)
    if lines:
        log("\nChanges made to the data on the way (the old database was not changed):")
        for line in lines:
            log(f"  - {line}")

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

        copied = copy_database(
            source_db,
            target_db,
            models,
            wipe_target=args.wipe_target,
            drop_orphans=args.drop_orphans,
        )
    except CopyError as e:
        print(f"\nStopped, nothing was written to the new database: {e}")
        return 1

    print(f"\nDone: {sum(copied.values())} rows in {len(copied)} tables copied and checked.")
    print("Now set DB_TYPE=postgres and the DB_* variables of the new database wherever the bot")
    print("runs, and start the bot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())