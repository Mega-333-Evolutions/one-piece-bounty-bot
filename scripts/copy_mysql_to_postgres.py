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


def load_models() -> tuple[list[Any], Any