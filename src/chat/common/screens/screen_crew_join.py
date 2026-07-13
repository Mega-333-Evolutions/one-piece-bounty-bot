from resources import phrases as phrases, Environment as Env
from src.model.Crew import Crew
from src.model.User import User
from src.model.error.CustomException import (
    CrewJoinValidationUserException,
    CrewJoinValidationCrewException,
    CrewValidationException,
)
from src.service.date_service import get_remaining_time_from_next_cron


def validate(
    user: User,
    crew: Crew,
    specific_user_error: bool = False,
    specific_crew_error: bool = False,
    for_invite: bool = False,
) -> None:
    """
    Validate the crew join request
    :param user: The user object
    :param crew: The crew object
    :param specific_user_error: If True, raise a specific error message for the user
    :param specific_crew_error: If True, raise a specific error message for the crew
    :param for_invite: If True, use invite-specific wording for the "already in a crew" error,
    since in that case the message is shown to the inviter/invitee and not to the joining user
    :return: Raise an exception if the request is not valid
    """
    try:
        # User in same Crew
        if user.crew == crew:
            raise CrewJoinValidationUserException(
                phrases.CREW_USER_ALREADY_IN_SAME_CREW if specific_user_error else None
            )

        # Target crew has reached the maximum number of members
        crew.set_is_full()  # Should not be necessary, but better to be safe
        if crew.is_full:
            raise CrewJoinValidationCrewException(
                phrases.CREW_JOIN_REQUEST_CREW_FULL if specific_crew_error else None
            )

        # Target crew cannot accept new members
        if not crew.can_accept_new_members:
            raise CrewJoinValidationCrewException(
                phrases.CREW_JOIN_REQUEST_CREW_CANNOT_ACCEPT_NEW_MEMBERS_UNTIL_NEXT_RESET.format(
                    get_remaining_time_from_next_cron(Env.CRON_SEND_LEADERBOARD.get())
                )
                if specific_crew_error
                else None
            )

        # User cannot join a Crew
        if not user.can_join_crew:
            raise CrewJoinValidationUserException(
                phrases.CREW_USER_CANNOT_JOIN_CREW_UNTIL_RESET.format(
                    get_remaining_time_from_next_cron(Env.CRON_SEND_LEADERBOARD.get())
                )
                if specific_user_error
                else None
            )

        # User already in a Crew
        if user.is_crew_member():
            if not specific_user_error:
                already_in_crew_message = None
            elif for_invite:
                already_in_crew_message = phrases.CREW_INVITE_TARGET_ALREADY_IN_CREW
            else:
                already_in_crew_message = phrases.CREW_JOIN_USER_ALREADY_IN_CREW

            raise CrewJoinValidationUserException(already_in_crew_message)

    except CrewJoinValidationUserException as e:
        raise CrewValidationException(
            e.message
            if e.message is not None
            else phrases.CREW_JOIN_REQUEST_CREW_CANNOT_ACCEPT_USER
        )
    except CrewJoinValidationCrewException as e:
        raise CrewValidationException(
            e.message if e.message is not None else phrases.CREW_JOIN_REQUEST_USER_CANNOT_JOIN_CREW
        )
