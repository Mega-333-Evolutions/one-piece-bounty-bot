from enum import StrEnum

from peewee import fn
from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

import src.model.enums.Command as Command
from src.model.User import User
from src.model.enums.CommandName import CommandName
from src.model.enums.MessageSource import MessageSource
from src.model.enums.ReservedKeyboardKeys import ReservedKeyboardKeys
from src.model.enums.Screen import Screen
from src.model.pojo.Keyboard import Keyboard
from src.service.bounty_service import (
    add_or_remove_bounty,
    get_amount_from_string,
    validate_amount,
)
from src.service.message_service import (
    full_message_or_media_send_or_edit,
    get_message_source,
    get_yes_no_keyboard,
    mention_markdown_user,
)
from src.utils.string_utils import get_belly_formatted


class OwnerBountyReservedKeys(StrEnum):
    """
    Reserved keys for owner bounty management.
    """

    ACTION = "a"


class OwnerBountyAction(StrEnum):
    """
    Owner bounty actions.
    """

    REVERT_PENDING_ALL = "rpall"


# Flag used with /add to add the full bounty amount as-is, bypassing income tax and any
# automatic bounty distribution (e.g. expired bounty loan garnishment). The player receives
# the full amount untouched. Without it, /add behaves as before: subject to tax/distributions
# like any other bounty gain.
EXEMPT_FLAG = "-e"


async def manage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command: Command.Command,
    user: User,
    inbound_keyboard: Keyboard = None,
    target_user: User = None,
) -> None:
    """
    Manage owner-only bounty adjustment commands.
    :param update: The update
    :param context: The context
    :param command: The command
    :param user: The owner user
    :param inbound_keyboard: Inbound keyboard for confirmation callbacks
    :param target_user: Target user from replied message in groups
    :return: None
    """

    if inbound_keyboard is not None:
        await manage_keyboard(update, context, inbound_keyboard)
        return

    is_group = get_message_source(update) is MessageSource.GROUP

    if command.name is CommandName.REVERT_PENDING_BOUNTY_ALL:
        if is_group:
            return

        await send_revert_pending_all_confirmation(update, context, user)
        return

    if command.name is CommandName.REVERT_PENDING_BOUNTY:
        await manage_revert_pending(update, context, command, target_user, is_group)
        return

    await manage_add_or_take(update, context, command, user, target_user, is_group)


async def manage_add_or_take(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command: Command.Command,
    user: User,
    target_user: User = None,
    is_group: bool = False,
) -> None:
    """
    Manage owner-only add/take bounty commands.
    :param update: The update
    :param context: The context
    :param command: The command
    :param user: The owner user
    :param target_user: Target user from replied message in groups
    :param is_group: Whether this is a group message
    :return: None
    """

    add_delete_button = is_group

    should_tax = EXEMPT_FLAG not in command.parameters
    parameters = [p for p in command.parameters if p != EXEMPT_FLAG]

    if is_group:
        if target_user is None:
            await full_message_or_media_send_or_edit(
                context,
                "This command can only be used in reply to someone's message.",
                update=update,
                add_delete_button=True,
            )
            return

        if len(parameters) == 0:
            await full_message_or_media_send_or_edit(
                context,
                get_missing_group_amount_text(command),
                update=update,
                add_delete_button=True,
            )
            return

        amount_text = parameters[0]
    else:
        if len(parameters) == 0:
            await full_message_or_media_send_or_edit(
                context,
                "Please specify the bounty amount.",
                update=update,
            )
            return

        amount_text = parameters[0]

        if len(parameters) < 2:
            await full_message_or_media_send_or_edit(
                context,
                "Please specify a target user by username or Telegram user ID.",
                update=update,
            )
            return

        target_user = get_target_user(parameters[1])
        if target_user is None:
            await full_message_or_media_send_or_edit(
                context,
                "Please specify a target user by username or Telegram user ID.",
                update=update,
            )
            return

    if not await validate_amount(
        update,
        context,
        user,
        amount_text,
        add_delete_button=add_delete_button,
        should_validate_user_has_amount=False,
    ):
        return

    amount = get_amount_from_string(amount_text, user)
    target_user = User.get_by_id(target_user.id)

    if command.name is CommandName.ADD_BOUNTY:
        await add_or_remove_bounty(
            target_user,
            amount,
            context=context,
            update=update,
            should_save=True,
            should_tax=should_tax,
            check_for_loan=should_tax,
        )
        if should_tax:
            text = "Added ฿{} Berries to {}.".format(
                get_belly_formatted(amount), mention_markdown_user(target_user)
            )
        else:
            text = "Added ฿{} Berries \\(exempt from income tax and bounty distributions\\) to {}.".format(
                get_belly_formatted(amount), mention_markdown_user(target_user)
            )
    else:
        if target_user.bounty < amount:
            target_user.bounty = 0
            target_user.save()
            text = (
                "{} doesn't have ฿{} Berries, so their bounty has been set to ฿0 instead.".format(
                    mention_markdown_user(target_user), get_belly_formatted(amount)
                )
            )
        else:
            target_user.bounty -= amount
            target_user.save()
            text = "Took ฿{} Berries from {}.".format(
                get_belly_formatted(amount), mention_markdown_user(target_user)
            )

    await full_message_or_media_send_or_edit(
        context,
        text,
        update=update,
        add_delete_button=add_delete_button,
    )


async def manage_revert_pending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command: Command.Command,
    target_user: User = None,
    is_group: bool = False,
) -> None:
    """
    Manage single-user pending bounty revert.
    :param update: The update
    :param context: The context
    :param command: The command
    :param target_user: Target user from replied message in groups
    :param is_group: Whether this is a group message
    :return: None
    """

    if is_group:
        if target_user is None:
            await full_message_or_media_send_or_edit(
                context,
                "Please reply to the player whose pending bounty you want to revert.",
                update=update,
                add_delete_button=True,
            )
            return
    else:
        if len(command.parameters) == 0:
            await full_message_or_media_send_or_edit(
                context,
                "Please specify a username or Telegram user ID.",
                update=update,
            )
            return

        target_user = get_target_user(command.parameters[0])
        if target_user is None:
            await full_message_or_media_send_or_edit(
                context,
                "Please specify a username or Telegram user ID.",
                update=update,
            )
            return

    text = revert_pending_bounty(target_user)
    await full_message_or_media_send_or_edit(
        context,
        text,
        update=update,
        add_delete_button=is_group,
    )


async def send_revert_pending_all_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User
) -> None:
    """
    Send pending bounty revert all confirmation.
    :param update: The update
    :param context: The context
    :param user: The owner
    :return: None
    """

    keyboard = [
        get_yes_no_keyboard(
            user,
            screen=Screen.PVT_OWNER_BOUNTY,
            extra_keys={
                OwnerBountyReservedKeys.ACTION: OwnerBountyAction.REVERT_PENDING_ALL,
            },
        )
    ]
    await full_message_or_media_send_or_edit(
        context,
        "Are you sure you want to revert the pending bounty for every player?",
        update=update,
        keyboard=keyboard,
    )


async def manage_keyboard(
    update: Update, context: ContextTypes.DEFAULT_TYPE, inbound_keyboard: Keyboard
) -> None:
    """
    Manage owner bounty keyboard actions.
    :param update: The update
    :param context: The context
    :param inbound_keyboard: Inbound keyboard
    :return: None
    """

    if (
        inbound_keyboard.get(OwnerBountyReservedKeys.ACTION)
        != OwnerBountyAction.REVERT_PENDING_ALL
    ):
        return

    if not inbound_keyboard.get_bool(ReservedKeyboardKeys.CONFIRM):
        await full_message_or_media_send_or_edit(
            context,
            "Pending bounty revert cancelled.",
            update=update,
        )
        return

    await full_message_or_media_send_or_edit(
        context,
        "Reverting pending bounty for all eligible players...",
        update=update,
    )
    processed, skipped = revert_pending_bounty_all()
    await full_message_or_media_send_or_edit(
        context,
        "Pending bounty revert completed successfully.\n\n"
        "*Statistics*\n"
        "• Players processed: *{}*\n"
        "• Players skipped \\(no pending bounty\\): *{}*".format(processed, skipped),
        update=update,
    )


def revert_pending_bounty(user: User) -> str:
    """
    Revert pending bounty for one user without applying income tax.
    :param user: The user
    :return: Result message
    """

    user = User.get_by_id(user.id)
    pending_bounty = user.pending_bounty or 0
    if pending_bounty == 0:
        return "{} doesn't have any pending bounty to revert.".format(mention_markdown_user(user))

    with User._meta.database.atomic():
        User.update(
            bounty=User.bounty + pending_bounty,
            pending_bounty=0,
        ).where(User.id == user.id).execute()

    return "Successfully reverted {}'s pending bounty of *{}* back to their main bounty.".format(
        mention_markdown_user(user), get_signed_belly_formatted(pending_bounty)
    )


def revert_pending_bounty_all() -> tuple[int, int]:
    """
    Revert pending bounty for every user without applying income tax.
    :return: Processed and skipped counts
    """

    processed = 0
    users_with_pending = User.select().where(
        (User.pending_bounty.is_null(False)) & (User.pending_bounty != 0)
    )

    for user in users_with_pending.iterator():
        pending_bounty = user.pending_bounty or 0
        with User._meta.database.atomic():
            User.update(
                bounty=User.bounty + pending_bounty,
                pending_bounty=0,
            ).where(User.id == user.id).execute()
        processed += 1

    skipped = User.select().count() - processed
    return processed, skipped


def get_signed_belly_formatted(amount: int) -> str:
    """
    Format a signed bounty amount.
    :param amount: The amount
    :return: Formatted amount
    """

    sign = "-" if amount < 0 else ""
    return "{}฿{}".format(sign, get_belly_formatted(abs(amount)))


def get_missing_group_amount_text(command: Command.Command) -> str:
    """
    Get missing amount text for group commands.
    :param command: The command
    :return: Missing amount text
    """

    if command.name is CommandName.ADD_BOUNTY:
        return "Please specify the bounty amount to add."

    return "Please specify the bounty amount to remove."


def get_target_user(identifier: str) -> User | None:
    """
    Resolve a user by Telegram user id or username.
    :param identifier: Telegram user id or username
    :return: User, if found
    """

    identifier = identifier.strip()
    if identifier.startswith("@"):
        identifier = identifier[1:]

    if identifier.isnumeric():
        user = User.get_or_none(User.tg_user_id == identifier)
        if user is not None:
            return user

    if identifier == "":
        return None

    return User.get_or_none(fn.LOWER(User.tg_username) == identifier.lower())
