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
    def get_max_rank_attained(user: User) -> "LeaderboardUser":
        """
        Get the highest rank attained by a user
        param user: The user
        return: The highest rank attained
        """

        from src.model.enums.LeaderboardRank import LeaderboardRankIndex

        # The lower the rank index, the higher the rank, except for Rookie: its index (5) is lower
        # than the ones of Admiral, Legendary Pirate and Warlord (6, 7, 8), but it is the lowest
        # rank there is. A player who lost one of those ranks is left with a Rookie entry in the
        # leaderboard, which must not count as the highest rank he attained
        is_rookie = Case(None, [(LeaderboardUser.rank_index == LeaderboardRankIndex.ROOKIE, 1)], 0)

        return (
            LeaderboardUser()
            .select()
            .join(Leaderboard)
            .where((LeaderboardUser.user == user) & (Leaderboard.group.is_null()))
            .order_by(is_rookie.asc(), LeaderboardUser.rank_index.asc())
            .first()
        )

    @staticmethod
    def get_max_bounty_attained(user: User) -> "LeaderboardUser":
        """
        Get the highest bounty attained by a user
        param user: The user
        return: The highest bounty attained
        """

        return (
            LeaderboardUser()
            .select()
            .join(Leaderboard)
            .where((LeaderboardUser.user == user) & (Leaderboard.group.is_null()))
            .order_by(LeaderboardUser.bounty.desc())
            .first()
        )


LeaderboardUser.create_table()
