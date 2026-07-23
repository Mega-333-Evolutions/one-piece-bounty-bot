"""
This is where the rubber meets the road: real Telethon events get converted
into the compat Update/Context objects the rest of the codebase (unchanged)
expects, mirroring how python-telegram-bot's Application dispatched updates.

main.py constructs one Application and calls .run(...) on it - see that file
for the top-level wiring.
"""

import asyncio
import logging
import signal

from telethon import TelegramClient, events

from ._bot import Bot
from ._message import Message, CallbackQuery, InlineQuery, Update
from ._types import TelegramUser
from ._jobqueue import JobQueue

logger = logging.getLogger(__name__)


class Context:
    """Mirrors telegram.ext.CallbackContext / ContextTypes.DEFAULT_TYPE."""

    def __init__(self, bot, bot_data, user_data, application, job=None):
        self.bot = bot
        self.bot_data = bot_data
        self.user_data = user_data
        self.application = application
        self.job = job

    @property
    def job_queue(self):
        return self.application.job_queue


class ContextTypes:
    """Mirrors telegram.ext.ContextTypes."""

    DEFAULT_TYPE = Context


# Alias, mirrors telegram.ext.CallbackContext being importable directly too.
CallbackContext = Context


def _is_chatid_command(text: str) -> bool:
    if not text:
        return False
    first_word = text.split()[0] if text.split() else ""
    command = first_word.split("@")[0]
    return command.lower() == "/chatid"


class Application:
    """Mirrors telegram.ext.Application. Owns the single TelegramClient for
    the process, plus the in-memory bot_data/user_data stores PTB would
    otherwise manage (this project uses no persistence backend, so plain
    dicts that live for the process lifetime are an exact match)."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: str,
        session: str = "bot_session",
        timezone=None,
        connect_timeout: int = 20,
        connection_retries: int = 5,
    ):
        self._bot_token = bot_token
        self._client = TelegramClient(
            session,
            api_id,
            api_hash,
            timeout=connect_timeout,
            connection_retries=connection_retries,
            # We do our own RetryAfter-based retry/backoff (matching the
            # original code's explicit `except RetryAfter` handling in e.g.
            # group_service.py's pin-retry logic and broadcast_service.py),
            # so we don't want Telethon silently sleeping through flood
            # waits before that code ever sees them.
            flood_sleep_threshold=0,
        )
        self.bot_data = {}
        self._user_data_store = {}
        self.bot = Bot(self._client)
        self.job_queue = JobQueue(self, timezone=timezone)
        # Python's event loop only holds a *weak* reference to tasks created
        # via asyncio.ensure_future/create_task - anything not referenced
        # elsewhere can be garbage collected mid-execution, before it's done
        # (see https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task,
        # worse from Python 3.12 on). Every call site in this codebase does
        # `context.application.create_task(...)` and discards the return
        # value, which is exactly the pattern that's vulnerable - especially
        # for anything that awaits a long asyncio.sleep() (game hint loops
        # sleeping 30-60s between messages), since a longer suspension means
        # a much bigger window for this to happen. This set holds a strong
        # reference to every task until it finishes, matching the standard
        # asyncio idiom (and what PTB's own Application.create_task does
        # internally).
        self._background_tasks = set()

        self._regular_handler = None
        self._callback_handler = None
        self._chatid_handler = None

    def new_context(self, update: Update = None, job=None) -> Context:
        user_id = None
        if update is not None and update.effective_user is not None:
            user_id = update.effective_user.id
        user_data = self._user_data_store.setdefault(user_id, {}) if user_id is not None else {}
        return Context(bot=self.bot, bot_data=self.bot_data, user_data=user_data, application=self, job=job)

    def create_task(self, coro, name: str = None):
        async def _wrapped():
            try:
                await coro
            except Exception:
                logger.exception(f"Unhandled exception in background task {name or '<unnamed>'}")

        task = asyncio.ensure_future(_wrapped())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    # -- wiring ---------------------------------------------------------

    def set_handlers(self, regular_handler, callback_handler, chatid_handler):
        self._regular_handler = regular_handler
        self._callback_handler = callback_handler
        self._chatid_handler = chatid_handler

    def _register_event_handlers(self):
        client = self._client

        @client.on(events.NewMessage())
        async def _on_new_message(event):
            if event.out:
                # A bot never receives its own sends back as an "update" to
                # react to via Bot API's getUpdates/webhook; skip them here
                # too so we don't reprocess our own game messages.
                return
            try:
                message = await Message.from_telethon(event.message, client, self.bot)
            except Exception:
                logger.exception("tg_compat: failed to build Message from NewMessage event")
                return

            update = Update(message=message, _bot=self.bot)
            context = self.new_context(update=update)

            if _is_chatid_command(message.text):
                await self._chatid_handler(update, context)
                return

            await self._regular_handler(update, context)

        @client.on(events.ChatAction())
        async def _on_chat_action(event):
            if event.action_message is None:
                return
            try:
                message = await Message.from_chat_action(event, client, self.bot)
            except Exception:
                logger.exception("tg_compat: failed to build Message from ChatAction event")
                return
            update = Update(message=message, _bot=self.bot)
            context = self.new_context(update=update)
            await self._regular_handler(update, context)

        @client.on(events.CallbackQuery())
        async def _on_callback_query(event):
            try:
                data = event.data.decode("utf-8") if isinstance(event.data, (bytes, bytearray)) else event.data
            except Exception:
                data = None

            tl_message = None
            try:
                tl_message = await event.get_message()
            except Exception:
                logger.warning("tg_compat: could not fetch message for callback query", exc_info=True)

            message = None
            if tl_message is not None:
                try:
                    message = await Message.from_telethon(tl_message, client, self.bot, fetch_reply=False)
                except Exception:
                    logger.exception("tg_compat: failed to build Message for callback query")

            sender = await event.get_sender()
            from_user = TelegramUser.from_entity(sender, client)

            callback_query = CallbackQuery(
                id=str(event.query.query_id),
                data=data,
                message=message,
                from_user=from_user,
                _client=client,
            )
            update = Update(callback_query=callback_query, _bot=self.bot)
            context = self.new_context(update=update)
            await self._callback_handler(update, context)

        @client.on(events.InlineQuery())
        async def _on_inline_query(event):
            sender = await event.get_sender()
            from_user = TelegramUser.from_entity(sender, client)
            inline_query = InlineQuery(id=str(event.id), query=event.text, from_user=from_user, _event=event)
            update = Update(inline_query=inline_query, _bot=self.bot)
            context = self.new_context(update=update)
            await self._regular_handler(update, context)

    async def run(self, post_init=None, drop_pending_updates: bool = True):
        await self._client.start(bot_token=self._bot_token)

        me = await self._client.get_me()
        self.bot.id = me.id
        self.bot.username = me.username

        self._register_event_handlers()

        if post_init is not None:
            await post_init(self)

        if not drop_pending_updates:
            await self._client.catch_up()

        logger.info(f"Bot connected as @{me.username} (id={me.id})")

        # python-telegram-bot's own run_polling()/run_webhook() install signal
        # handlers - by default for SIGINT, SIGTERM, and SIGABRT on non-Windows
        # platforms - that stop the Application cleanly (log a message and
        # return) rather than letting the interpreter's default
        # SIGINT-to-KeyboardInterrupt behavior run its course. Without an
        # equivalent here, any of those three signals - from Ctrl+C, or from
        # whatever is supervising this process (a plain `systemctl stop` on a
        # VPS, a container runtime stopping/restarting the container, a
        # process manager, etc. - the mechanism is the same regardless of
        # where this is hosted) - instead hit asyncio.run()'s own default
        # handling: cancel the running task, wait for the CancelledError to
        # propagate up through run_until_disconnected() and this coroutine,
        # then re-raise the original KeyboardInterrupt - which is exactly the
        # "CancelledError, then during handling of that, KeyboardInterrupt"
        # traceback this produced.
        #
        # Handling the signal directly avoids that path entirely: disconnect()
        # resolves client.disconnected on its own, so run_until_disconnected()
        # below returns normally - no cancellation, no traceback.
        loop = asyncio.get_running_loop()

        def _request_shutdown(sig_name: str):
            logger.info(f"Received {sig_name}, shutting down...")
            self.create_task(self._client.disconnect(), name="shutdown-disconnect")

        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
            try:
                loop.add_signal_handler(sig, _request_shutdown, sig.name)
            except NotImplementedError:
                # add_signal_handler is POSIX-only (e.g. unavailable on the
                # default Windows event loop, which is the same limitation
                # PTB itself documents for its own stop_signals) - falls back
                # to the interpreter's default KeyboardInterrupt behavior
                # there, same as before this change.
                pass

        await self._client.run_until_disconnected()
        logger.info("Bot stopped.")
