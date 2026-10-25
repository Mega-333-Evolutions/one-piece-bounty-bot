from datetime import datetime

from peewee import *

from resources.Database import Database

db_obj = Database()

# Divisor to use in a database expression that divides a column by two, e.g. User.bounty / DIVIDE_BY_TWO.
# A plain "/ 2" is divided as whole numbers by PostgreSQL (the result is rounded down) while MySQL
# divides with decimals and rounds the result when it is saved, so e.g. 5 / 2 would give 2 on
# PostgreSQL and 3 on MySQL. Written as SQL, the division has decimals on both databases. (Writing it
# as the number 2.0 would not work: peewee turns the number into the integer 2 for an integer column)
DIVIDE_BY_TWO = SQL("2.0")


class BaseModel(Model):
    """
    BaseModel class
    Used to manage Entities and Database connection
    """

    id: int | PrimaryKeyField = PrimaryKeyField()
    date = DateTimeField(default=datetime.now)

    class Meta:
        database = db_obj.get_db()
        only_save_dirty = True
