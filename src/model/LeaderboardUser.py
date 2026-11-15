from peewee import *

from src.model.BaseModel import BaseModel
from src.model.Leaderboard import Leaderboard
from src.model.User import User


class LeaderboardUser(BaseModel):
    """
    Leaderboard class
    """

    leaderboard = ForeignKeyField(
        Leaderboard, backref="leaderboard_users", on_delete="CASCADE", on_update="CASCADE"
    )
    user = ForeignKeyField(
        User, backref="leaderboard_users", on_delete="CASCADE", on_update="CASCADE"
    )
    position = IntegerField()
    bounty = BigIntegerField()
    rank_index = SmallIntegerField()

    class Meta:
        db_table = "leaderboard_user"

    @staticmethod
    def get_appearances_as_rank(user: User, rank_index: int):
        """
        Get the appearances of a user as a rank
        param user: The user
        param rank: The rank
        return: The appearances
        """

        return (
            LeaderboardUser()
            .select()
            .join(Leaderboard)
            .where(
                (LeaderboardUser.user == user)
                & (Leaderboard.group.is_null())
                & (LeaderboardUser.rank_index == rank_index)
            )
            .count()
        )

    @staticmethod
    def get_global_entries_query(user: User, rank_indexes: tuple[int, ...] | None = None):
        """
        Get the query of the entries a user has in the global leaderboards
        param user: The user
        param rank_indexes: If given, only the entries with one of these rank indexes
        return: The query
        """

        query = (
            LeaderboardUser()
            .select()
            .join(Leaderboard)
            .where((LeaderboardUser.user == user) & (Leaderboard.group.is_null()))
        )

        if rank_indexes is not None:
            query = query.where(LeaderboardUser.rank_index.in_(rank_indexes))

        return query

    @staticmethod
    def get_max_rank_attained(
        user: User, rank_indexes: tuple[int, ...] | None = None
    ) -> "LeaderboardUser":
        """
        Get the highest rank attained by a user
        param user: The user
        param rank_indexes: If given, only the entries with one of these rank indexes count
        return: The highest rank attained
        """

        return (
            LeaderboardUser.get_global_entries_query(user, rank_indexes)
            .order_by(LeaderboardUser.rank_index.asc())
            .first()
        )

    @staticmethod
    def get_max_bounty_attained(
        user: User, rank_indexes: tuple[int, ...] | None = None
    ) -> "LeaderboardUser":
        """
        Get the highest bounty attained by a user
        param user: The user
        param rank_indexes: If given, only the entries with one of these rank indexes count
        return: The highest bounty attained
        """

        return (
            LeaderboardUser.get_global_entries_query(user, rank_indexes)
            .order_by(LeaderboardUser.bounty.desc())
            .first()
        )


LeaderboardUser.create_table()
