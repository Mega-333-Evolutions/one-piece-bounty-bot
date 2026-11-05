import logging
from enum import StrEnum

from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

import resources.phrases as phrases
from src.chat.common.screens.screen_game_manage import dispatch_game, end_game_that_did_not_start
from src.model.Game import Game
from src.model.User import User
from src.model.enums.GameStatus import GameStatus
from src.model.enums.ReservedKeyboardKeys import ReservedKeyboardKeys
from src.model.pojo.Keyboard import Keyboard
from src.service.game_service import (
    delete_game,
    validate_game,
    collect_game_wagers_and_set_in_progress,
)
from src.service.message_service import mention_markdown_user, full_media_send, full_message_send
from src.utils.string_utils import get_belly_formatted


class GameOpponentConfirmationReservedKeys(StrEnum):
    """
    The reserved keys for this screen
    """

    GAME_ID = "a"
    CANCEL = "c"


async def manage(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, inbound_keyboard: Keyboard
) -> None:
    """
    Manage the game screen
    :param update: The update object
    :param context: The context object
    :param user: The user object
    :param inbound_keyboard: The inbound keyboard
    :return: None
    """

    # Get the game from validation, will handle error messages
    game = await validate_game(update, context, inbound_keyboard)
    if game is None:
        return

    # Only a challenge that is still waiting for its opponent can be accepted, rejected or
    # cancelled from this message; every other press is a late one and is ignored completely.
    # The buttons stay on every player's screen until the bot has edited the message, which
    # takes a moment after the first Accept has been claimed. Anything pressed in that moment -
    # a second Accept of an open challenge, or the challenger's Cancel right after somebody
    # accepted - reaches a game that is already being started, whose message is being edited
    # right now. Answering it would write over that message ("Item in wrong status" error), or,
    # worse, delete the game that just started (the "not enough bounty" and "cancel" answers),
    # losing the stakes both players have just paid. Nothing may happen instead.
    if game.get_status() is not GameStatus.AWAITING_OPPONENT_CONFIRMATION:
        logging.info(
            f"Ignored a press of user {user.id} on game {game.id}: it is no longer waiting for"
            f" its opponent (status {game.get_status().name})"
        )
        user.should_update_model = False
        return

    # User clicked on cancel button or opponent rejected
    if (
        GameOpponentConfirmationReservedKeys.CANCEL in inbound_keyboard.info
        or not inbound_keyboard.info[ReservedKeyboardKeys.CONFIRM]
    ):
        should_delete_message = True

        if ReservedKeyboardKeys.CONFIRM in inbound_keyboard.info:  # Opponent rejected
            should_delete_message = False
            ot_text = phrases.GAME_CHALLENGE_REJECTED.format(mention_markdown_user(game.opponent))
            await full_media_send(
                context,
                caption=ot_text,
                update=update,
                add_delete_button=True,
                authorized_users=game.get_players(),
                edit_only_caption_and_keyboard=True,
            )

        await delete_game(context, update, game, should_delete_message=should_delete_message)
        user.should_update_model = False
        return

    # Opponent does not have enough bounty
    if user.bounty < game.wager:
        if game.opponent is not None:
            await delete_game(context, update, game, should_delete_message=False)
            await full_media_send(
                context,
                caption=phrases.ACTION_INSUFFICIENT_BOUNTY.format(get_belly_formatted(game.wager)),
                update=update,
                add_delete_button=True,
                edit_only_caption_and_keyboard=True,
            )
            user.should_update_model = False
            return
        else:  # Open to everyone, alert
            await full_message_send(
                context,
                phrases.ACTION_INSUFFICIENT_BOUNTY.format(get_belly_formatted(game.wager)),
                update=update,
                show_alert=True,
            )
            return

    # Challenger clicked on confirm button
    challenger: User = game.challenger
    if user == challenger:
        await full_message_send(
            context, phrases.KEYBOARD_USE_UNAUTHORIZED, update=update, show_alert=True
        )
        return

    # Atomically claim this Accept: only proceed if the game is still awaiting confirmation.
    # The status was read above and is written here, and nothing but this conditional UPDATE
    # keeps that pair safe when two presses are handled at the same time (another process, or
    # two handlers interleaving at an await): both would pass the check above, deduct the wager
    # and start the game, and the message would flicker between the game starting and an error
    # as they raced to edit it. Only the press that wins this claim proceeds, the other one is
    # ignored.
    # The chosen opponent of a direct challenge, if any
    opponent_id_before_start = game.opponent_id
    claimed_rows = (
        Game.update(status=GameStatus.IN_PROGRESS)
        .where((Game.id == game.id) & (Game.status == GameStatus.AWAITING_OPPONENT_CONFIRMATION))
        .execute()
    )
    if claimed_rows == 0:
        logging.info(f"Ignored the Accept of user {user.id} on game {game.id}: lost the claim")
        user.should_update_model = False
        return

    # The wagers are taken and the game, with its opponent and the doubled wager, is saved in the
    # same transaction: the game must never be left without what the players paid for it (the
    # refund of a game that is ended later is worked out from its row)
    try:
        await collect_game_wagers_and_set_in_progress(
            update, game, challenger=challenger, opponent=user
        )
    except BaseException:
        # The game could not be started and nothing was saved (a player has less bounty than the
        # wager now, for example). Give the claim back, or the challenge would stay "in progress"
        # without an opponent and ignore everybody who presses Accept from now on
        Game.update(status=GameStatus.AWAITING_OPPONENT_CONFIRMATION).where(
            (Game.id == game.id)
            & (Game.status == GameStatus.IN_PROGRESS)
            & (Game.opponent == opponent_id_before_start)
        ).execute()
        raise

    try:
        await dispatch_game(update, context, user, inbound_keyboard, game)
    except Exception:
        # Both players have paid, but the game failed to start (the board of a guess game could
        # not be built, for example) and nobody can play it: the stakes would be held until the
        # inactive games are ended. Give them back now, and let the error go on as it did
        await end_game_that_did_not_start(context, game, user)
        raise
