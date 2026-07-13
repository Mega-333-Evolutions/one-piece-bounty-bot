import asyncio
import logging
import os
import sys
import time
from zoneinfo import ZoneInfo

import resources.Environment as Env
from src.tg_compat.ext import Application, ContextTypes
from src.chat.manage_message import (
    manage_regular as manage_regular_message,
    manage_callback as manage_callback_message,
)
from src.service.message_service import full_message_send
from src.service.leaderboard_service import schedule_pending_special_rank_expiry_jobs
from src.service.timer_service import set_timers


async def chat_id(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send chat id of current chat
    :param update: Telegram update
    :param context: Telegram context
    :return: None
    """
    await full_message_send(context, str(update.effective_chat.id), update)


def pre_init():
    """
    Pre init checks
    :return: None, raises Exception if something is wrong
    """

    # Check that all the required environment variables are set
    for env in Env.Environment.instances:
        env.get()


async def post_init(application: Application) -> None:
    """
    Post init
    :param application: the application
    :return: None
    """
    await application.job_queue.start()
    await set_timers(application)
    await schedule_pending_special_rank_expiry_jobs(application)


async def async_main() -> None:
    """
    Builds the Telethon-backed application, wires up handlers and runs until
    disconnected.
    :return: None
    """
    application = Application(
        api_id=Env.API_ID.get_int(),
        api_hash=Env.API_HASH.get(),
        bot_token=Env.BOT_TOKEN.get(),
        session="one_piece_bot",
        timezone=ZoneInfo(Env.TZ.get()),
        connect_timeout=20,
    )

    # Chat id handler, regular message handler (incl. inline queries) and
    # callback query handler - mirrors the four handlers the original
    # python-telegram-bot Application registered.
    application.set_handlers(
        regular_handler=manage_regular_message,
        callback_handler=manage_callback_message,
        chatid_handler=chat_id,
    )

    logging.getLogger("apscheduler.executors.default").propagate = False

    await application.run(
        post_init=post_init,
        drop_pending_updates=Env.BOT_DROP_PENDING_UPDATES.get_bool(),
    )


def main() -> None:
    """
    Main function. Starts the bot
    :return: None
    """
    # Set timezone: Only on linux
    os.environ["TZ"] = Env.TZ.get()
    try:
        time.tzset()
    except AttributeError:
        pass

    # Pre init checks
    pre_init()

    if Env.DB_LOG_QUERIES.get_bool():
        # Set Peewee logger
        logger = logging.getLogger("peewee")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)

    # Disable noisy library logging
    logging.getLogger("telethon").setLevel(logging.WARNING)

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.getLevelName(Env.LOG_LEVEL.get()),
        stream=sys.stdout,
    )

    # Sentry
    if Env.SENTRY_ENABLED.get_bool():
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=Env.SENTRY_DSN.get(),
            environment=Env.SENTRY_ENVIRONMENT.get(),
            enable_tracing=Env.SENTRY_ENABLE_TRACING.get_bool(),
            traces_sample_rate=Env.SENTRY_TRACES_SAMPLE_RATE.get_float(),
            profiles_sample_rate=Env.SENTRY_PROFILES_SAMPLE_RATE.get_float(),
            integrations=[
                LoggingIntegration(
                    level=logging.getLevelName(Env.SENTRY_LOG_LEVEL.get()),
                    event_level=logging.getLevelName(Env.SENTRY_LOG_EVENT_LEVEL.get()),
                ),
            ],
        )

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
