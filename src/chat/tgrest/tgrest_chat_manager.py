import json

from src.tg_compat import Update
from src.tg_compat.ext import ContextTypes

from src.chat.tgrest.screens.screen_prediction import manage as manage_screen_prediction
from src.chat.tgrest.screens.screen_send_private_message import (
    manage as manage_screen_send_private_message,
)
from src.model.ImpelDownLog import ImpelDownLog
from src.model.enums.Notification import (
    ImpelDownNotificationRestrictionPlaced,
    DevilFruitAwardedNotification,
    WarlordAppointmentNotification,
    WarlordRevocationNotification,
    LegendaryPirateAppointmentNotification,
    LegendaryPirateRevocationNotification,
)
from src.model.enums.Notification import ImpelDownNotificationRestrictionRemoved
from src.model.enums.devil_fruit.DevilFruitSource import DevilFruitSource
from src.model.error.CustomException import DevilFruitValidationException
from src.model.tgrest.TgRest import TgRest, TgRestException
from src.model.tgrest.TgRestDevilFruitAward import TgRestDevilFruitAward
from src.model.tgrest.TgRestDevilFruitForceSchedule import TgRestDevilFruitForceSchedule
from src.model.tgrest.TgRestImpelDownNotification import TgRestImpelDownNotification
from src.model.tgrest.TgRestObjectType import TgRestObjectType
from src.model.tgrest.TgRestPrediction import TgRestPrediction
from src.model.tgrest.TgRestPrivateMessage import TgRestPrivateMessage
from src.model.tgrest.TgRestWarlordAppointment import TgRestWarlordAppointment
from src.model.tgrest.TgRestWarlordRevocation import TgRestWarlordRevocation
from src.model.tgrest.TgRestLegendaryPirateAppointment import TgRestLegendaryPirateAppointment
from src.model.tgrest.TgRestLegendaryPirateRevocation import TgRestLegendaryPirateRevocation
from src.service.devil_fruit_service import give_devil_fruit_to_user, force_schedule_devil_fruit
from src.service.leaderboard_service import (
    reset_expired_special_rank_for_user,
    schedule_special_rank_expiry_job,
)
from src.service.message_service import full_message_send, escape_valid_markdown_chars
from src.service.notification_service import send_notification


async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main function for the group chat manager
    :param update: Telegram update
    :param context: Telegram context
    :return: None
    """

    try:
        # Try parsing object
        try:
            # Try parsing object
            try:
                # If starts with "Error" or "Request", ignore
                if update.effective_message.text.startswith(
                    "Error"
                ) or update.effective_message.text.startswith("Request"):
                    return
            except AttributeError:
                return

            tg_rest_dict = json.loads(update.effective_message.text)
            tg_rest = TgRest(**tg_rest_dict)
        except Exception as tgre:
            raise TgRestException(str(tgre))

        # If not intended recipient, ignore
        if int(tg_rest.bot_id) != int(update.effective_message.get_bot().id):
            return

        match tg_rest.object_type:
            case TgRestObjectType.PREDICTION:
                tg_rest_prediction = TgRestPrediction(**tg_rest_dict)
                await manage_screen_prediction(context, tg_rest_prediction)

            case TgRestObjectType.PRIVATE_MESSAGE:
                tg_rest_private_message = TgRestPrivateMessage(**tg_rest_dict)
                await manage_screen_send_private_message(context, tg_rest_private_message)

            case TgRestObjectType.IMPEL_DOWN_NOTIFICATION:
                tg_rest_impel_down_notification = TgRestImpelDownNotification(**tg_rest_dict)
                if tg_rest_impel_down_notification.restriction_removed():
                    notification = ImpelDownNotificationRestrictionRemoved()
                else:
                    impel_down_log = None
                    if tg_rest_impel_down_notification.log_id is not None:
                        impel_down_log = ImpelDownLog.get_by_id(
                            tg_rest_impel_down_notification.log_id
                        )

                    notification = ImpelDownNotificationRestrictionPlaced(
                        tg_rest_impel_down_notification.sentence_type,
                        tg_rest_impel_down_notification.release_date_time,
                        tg_rest_impel_down_notification.bounty_action,
                        tg_rest_impel_down_notification.reason,
                        impel_down_log,
                    )

                await send_notification(
                    context, tg_rest_impel_down_notification.user, notification
                )

            case TgRestObjectType.DEVIL_FRUIT_AWARD:
                tg_rest_dfa = TgRestDevilFruitAward(**tg_rest_dict)

                # Give devil fruit to user
                try:
                    give_devil_fruit_to_user(
                        tg_rest_dfa.devil_fruit,
                        tg_rest_dfa.user,
                        DevilFruitSource.ADMIN,
                        reason=tg_rest_dfa.reason,
                    )
                except DevilFruitValidationException as e:
                    raise TgRestException(str(e))

                # Send notification
                notification = DevilFruitAwardedNotification(
                    tg_rest_dfa.devil_fruit, tg_rest_dfa.reason
                )
                await send_notification(context, tg_rest_dfa.user, notification)

            case TgRestObjectType.DEVIL_FRUIT_FORCE_SCHEDULE:
                tg_rest_dfs = TgRestDevilFruitForceSchedule(**tg_rest_dict)

                try:
                    force_schedule_devil_fruit(tg_rest_dfs.devil_fruit)
                except DevilFruitValidationException as e:
                    raise TgRestException(str(e))

            case TgRestObjectType.WARLORD_APPOINTMENT:
                tg_rest_wa = TgRestWarlordAppointment(**tg_rest_dict)

                # Send notification
                notification = WarlordAppointmentNotification(tg_rest_wa.warlord, tg_rest_wa.days)
                await send_notification(context, tg_rest_wa.user, notification)

                # Schedule rank reset for the exact moment this Warlord term ends, so the
                # leaderboard rank doesn't stay stale until the next leaderboard
                schedule_special_rank_expiry_job(
                    context.job_queue, tg_rest_wa.user, tg_rest_wa.warlord.end_date
                )

            case TgRestObjectType.WARLORD_REVOCATION:
                tg_rest_wr = TgRestWarlordRevocation(**tg_rest_dict)

                # Send notification
                notification = WarlordRevocationNotification(tg_rest_wr.warlord)
                await send_notification(context, tg_rest_wr.user, notification)

                # Reset rank immediately rather than waiting for the next leaderboard
                reset_expired_special_rank_for_user(tg_rest_wr.user)

            case TgRestObjectType.LEGENDARY_PIRATE_APPOINTMENT:
                tg_rest_lpa = TgRestLegendaryPirateAppointment(**tg_rest_dict)

                notification = LegendaryPirateAppointmentNotification(
                    tg_rest_lpa.legendary_pirate,
                    tg_rest_lpa.days,
                    tg_rest_lpa.is_permanent,
                )
                await send_notification(context, tg_rest_lpa.user, notification)

                # Only temporary appointments have an end date to schedule a reset for;
                # permanent ones never expire on their own
                if tg_rest_lpa.legendary_pirate.end_date is not None:
                    schedule_special_rank_expiry_job(
                        context.job_queue,
                        tg_rest_lpa.user,
                        tg_rest_lpa.legendary_pirate.end_date,
                    )

            case TgRestObjectType.LEGENDARY_PIRATE_REVOCATION:
                tg_rest_lpr = TgRestLegendaryPirateRevocation(**tg_rest_dict)

                notification = LegendaryPirateRevocationNotification(tg_rest_lpr.legendary_pirate)
                await send_notification(context, tg_rest_lpr.user, notification)

                # Reset rank immediately rather than waiting for the next leaderboard
                reset_expired_special_rank_for_user(tg_rest_lpr.user)

            case _:
                raise TgRestException("Unknown object type")
        await full_message_send(context, "Request received", update=update, quote=True)
    except TgRestException as e:
        await full_message_send(
            context, "Error: " + escape_valid_markdown_chars(e.message), update=update, quote=True
        )
        return
