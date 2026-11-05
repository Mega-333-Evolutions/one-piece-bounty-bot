import datetime
import logging

from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

from resources import phrases
from src.chat.common.screens.screen_game_manage import dispatch_game
from src.model.Game import Game
from src.model.User import User
from src.model.enums.GameStatus import GameStatus
from src.model.enums.ReservedKeyboardKeys import ReservedKeyboardKeys
from src.model.enums.Screen import Screen
from src.model.pojo.Keyboard import Keyboard
from src.service.game_service import (
    get_game_from_keyboard,
    collect_game_wagers_and_set_in_progress,
    get_text,
)
from src.service.message_service import full_message_send, mention_markdown_user, full_media_send
from src.utils.string_utils import get_belly_formatted


async def manage(
    update: Update, context: ContextTypes.DEFAULT_TYPE, inbound_keyboard: Keyboard, user: User
) -> None:
    """
    Manage the game input screen
    :param update: The update
    :param context: The context
    :param inbound_keyboard: The inbound keyboard
    :param user: The user
    :return: None
    """

    game: Game = get_game_from_keyboard(inbound_keyboard)

    # User is not a player of the game
    if not game.is_player(user):
        await full_message_send(context, phrases.GAME_INPUT_NOT_PLAYER, update=update)
        return

    game_status: GameStatus = GameStatus(game.status)

    # May be in progress, may be ended, dunno don't care, let the manage of the game handle it
    if game_status is not GameStatus.AWAITING_OPPONENT_CONFIRMATION:
        await dispatch_game(update, context, user, inbound_keyboard, game)
        return

    # Atomically claim the start: only proceed if the challenge is still waiting for its opponent.
    # The status was read above and is written below, and the Accept of another player in the
    # group is handled in the same way (see screen_game_opponent_confirmation.py): if both pass
    # their check before either has written the new status, both would take the challenger's
    # wager and start the game, one of them as a game with an opponent and the other as a global
    # challenge, saving over each other's game. The same goes for this very button pressed twice.
    # Only the press that wins this claim goes on.
    claimed_rows = (
        Game.update(status=GameStatus.IN_PROGRESS)
        .where((Game.id == game.id) & (Game.status == GameStatus.AWAITING_OPPONENT_CONFIRMATION))
        .execute()
    )
    if claimed_rows == 0:
        # Somebody else started it first, and what the game looks like now is theirs to show: the
        # game in memory is the one from before that, and this user (read at the same time) must
        # not be saved either, or the wager that was taken from them would be given back
        logging.info(
            f"Ignored the start of user {user.id} on game {game.id}: it was started by somebody"
            f" else first"
        )
        user.should_update_model = False
        return

    # Collect wagers
    game.global_challenger_start_date = datetime.datetime.now()
    try:
        await collect_game_wagers_and_set_in_progress(
            update, game, challenger=user, should_remove_bounty_opponent=False
        )
    except BaseException:
        # The game could not be started and nothing was saved (the challenger has less bounty
        # than the wager now, for example). Give the claim back, or the challenge would stay "in
        # progress" with nobody having paid for it and ignore every press from now on
        Game.update(status=GameStatus.AWAITING_OPPONENT_CONFIRMATION).where(
            (Game.id == game.id)
            & (Game.status == GameStatus.IN_PROGRESS)
            & (Game.opponent.is_null())
        ).execute()
        raise

    # Edit group message to show that it's now a global challenge, best effort
    if game.group_chat is not None:
        ot_text = phrases.GAME_REQUEST_OPEN_HEADER.format(
            mention_markdown_user(game.challenger),
            game.get_type().get_name(),
            get_belly_formatted(game.wager),
            game.get_type().get_description(),
        )
        outbound_keyboard: list[list[Keyboard]] = [
            # Start as global button
            [
                Keyboard(
                    phrases.KEYBOARD_OPTION_ACCEPT,
                    info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: game.id},
                    screen=Screen.PVT_GAME_GLOBAL_START_OPPONENT,
                    is_deeplink=True,
                )
            ],
        ]
        context.application.create_task(
            full_media_send(
                context,
                caption=ot_text,
                chat_id=game.group_chat.group.tg_group_id,
                edit_message_id=game.message_id,
                keyboard=outbound_keyboard,
                add_delete_button=True,
                edit_only_caption_and_keyboard=True,
                group_chat=game.group_chat,
                authorized_users=[game.challenger],
            )
        )
    # If global and guess based started in private, edit that message too
    elif game.is_global() and game.is_guess_based():
        ot_text = get_text(game, False, is_for_group_global=True)
        outbound_keyboard: list[list[Keyboard]] = [
            # Play as global button
            [
                Keyboard(
                    phrases.GRP_KEY_GAME_PLAY,
                    info={ReservedKeyboardKeys.DEFAULT_PRIMARY_KEY: game.id},
                    screen=Screen.PVT_GAME_GLOBAL_START_CHALLENGER,
                    is_deeplink=True,
                )
            ],
        ]

        context.application.create_task(
            full_media_send(
                context,
                caption=ot_text,
                keyboard=outbound_keyboard,
                edit_only_caption_and_keyboard=True,
                update=update,
            )
        )

    await dispatch_game(
        update, context, user, inbound_keyboard, game, should_start_immediately=True
    )
