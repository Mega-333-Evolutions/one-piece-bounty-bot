#!/usr/bin/env python3
"""
Copy the whole database of the bot from MySQL / TiDB to PostgreSQL (e.g. Supabase), once.
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

BATCH_SIZE = 500


class CopyError(Exception):
    pass


def parse_args(argv: list[str]) -> argparse.Namespace:
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
    from peewee import MySQLDatabase

    missing = [name for name in SOURCE_ENV_VARIABLES if not os.environ.get(name)]
    if missing:
        raise CopyError("Missing env variables: " + ", ".join(missing))

    return MySQLDatabase(
        os.environ["SRC_DB_NAME"],
        host=os.environ["SRC_DB_HOST"],
        port=int(os.environ["SRC_DB_PORT"]),
        user=os.environ["SRC_DB_USER"],
        password=os.environ["SRC_DB_PASSWORD"],
        charset="utf8mb4",
        ssl={"ssl": {}},
    )


def load_models() -> tuple[list[Any], Any]:
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
    port = db.connect_params.get("port")
    return f"{db.database} on {db.connect_params.get('host')}" + (f":{port}" if port else "")


def same_database(source_db: Any, target_db: Any) -> bool:
    def identity(db: Any) -> tuple:
        return (
            str(db.database),
            str(db.connect_params.get("host")).lower(),
            str(db.connect_params.get("port")),
        )
    return identity(source_db) == identity(target_db)


def check_source(source_db: Any, models: list[Any]) -> None:
    tables = set(source_db.get_tables())
    for model in models:
        table = model._meta.table_name
        if table not in tables:
            raise CopyError(f"Missing table '{table}'")

        columns = {column.name for column in source_db.get_columns(table)}
        missing = [
            f.column_name for f in model._meta.sorted_fields if f.column_name not in columns
        ]
        if missing:
            raise CopyError(f"Table '{table}' missing columns: {', '.join(missing)}")


def count_rows(db: Any, model: Any) -> int:
    with db.bind_ctx([model], bind_refs=False, bind_backrefs=False):
        return model.select().count()


def fingerprint(db: Any, model: Any) -> tuple[int, dict[str, int]]:
    from peewee import ForeignKeyField, IntegerField, fn

    with db.bind_ctx([model], bind_refs=False, bind_backrefs=False):
        totals = {}
        for field in model._meta.sorted_fields:
            if isinstance(field, (IntegerField, ForeignKeyField)):
                total = model.select(fn.SUM(field)).scalar()
                totals[field.column_name] = int(total or 0)

        return model.select().count(), totals


def read_rows(source_db: Any, model: Any, fields: list[Any]) -> list[tuple]:
    with source_db.bind_ctx([model], bind_refs=False, bind_backrefs=False):
        query = model.select(*fields).order_by(model._meta.primary_key)
        return list(query.tuples())


def copy_table(source_db: Any, model: Any, stats: dict[str, int]) -> int:
    from peewee import ForeignKeyField

    fields = list(model._meta.sorted_fields)
    primary_key_index = fields.index(model._meta.primary_key)

    self_links = [
        index
        for index, field in enumerate(fields)
        if isinstance(field, ForeignKeyField) and field.rel_model is model and field.null
    ]

    rows = []
    links_to_add = []
    for row in read_rows(source_db, model, fields):
        values = list(row)
        for index, value in enumerate(values):
            if isinstance(value, str) and "\x00" in value:
                values[index] = value.replace("\x00", "")
                stats["nul_characters_removed"] += 1

        for index in self_links:
            if values[index] is not None:
                links_to_add.append((values[primary_key_index], index, values[index]))
                values[index] = None

        rows.append(values)

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        clean_batch = [
            ["1970-01-01 00:00:00" if str(v).startswith("0000-00-00") else v for v in row_values]
            for row_values in batch
        ]
        model.insert_many(clean_batch, fields=fields).execute()

    for row_id, index, linked_id in links_to_add:
        model.update({fields[index]: linked_id}).where(model._meta.primary_key == row_id).execute()

    return len(rows)


def reset_sequences(target_db: Any, models: list[Any]) -> None:
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
    from peewee import PostgresqlDatabase

    if not isinstance(target_db, PostgresqlDatabase):
        raise CopyError("The new database must be PostgreSQL")

    if same_database(source_db, target_db):
        raise CopyError("Databases are identical")

    check_source(source_db, models)

    target_counts = {model._meta.table_name: count_rows(target_db, model) for model in models}
    not_empty = {table: count for table, count in target_counts.items() if count > 0}
    if not_empty and not wipe_target:
        raise CopyError("The new database already has rows. Pass --wipe-target.")

    stats = {"nul_characters_removed": 0}
    copied: dict[str, int] = {}

    with target_db.atomic():
        if wipe_target:
            names = ", ".join(f'"{model._meta.table_name}"' for model in models)
            target_db.execute_sql(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE")

        for model in models:
            copied[model._meta.table_name] = copy_table(source_db, model, stats)
            log(f"  {model._meta.table_name:<40} {copied[model._meta.table_name]:>8} rows")

        reset_sequences(target_db, models)

        problems = []
        for model in models:
            expected = fingerprint(source_db, model)
            actual = fingerprint(target_db, model)
            if expected != actual:
                problems.append(f"{model._meta.table_name}: old {expected} / new {actual}")

        if problems:
            raise CopyError("Mismatch after copy:\n  " + "\n  ".join(problems))

    return copied


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sys.argv = [sys.argv[0]] + ([args.env_file] if args.env_file else [])
    sys.path.insert(0, ROOT_DIR)

    try:
        source_db = build_source_database()
        models, target_db = load_models()

        print(f"Old database: {describe(source_db)}")
        print(f"New database: {describe(target_db)}")
        
        copied = copy_database(source_db, target_db, models, wipe_target=args.wipe_target)
    except CopyError as e:
        print(f"\nStopped: {e}")
        return 1

    print(f"\nDone: {sum(copied.values())} rows copied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())