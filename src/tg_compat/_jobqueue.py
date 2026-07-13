"""
Drop-in replacement for telegram.ext.JobQueue / telegram.ext.Job.

python-telegram-bot's own JobQueue is itself a thin wrapper around
APScheduler's AsyncIOScheduler, and APScheduler is already a direct
dependency of this project (see src/service/leaderboard_service.py's use of
CronTrigger), so this wrapper talks to it directly instead of going through
an intermediate Telegram-specific abstraction.
"""

import datetime
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)


def _as_timedelta(value) -> datetime.timedelta:
    if isinstance(value, datetime.timedelta):
        return value
    return datetime.timedelta(seconds=value)


class Job:
    """Mirrors telegram.ext.Job."""

    def __init__(self, aps_job, name, data, callback, application):
        self._aps_job = aps_job
        self.name = name
        self.data = data
        self._callback = callback
        self._application = application

    @property
    def next_t(self):
        return getattr(self._aps_job, "next_run_time", None) if self._aps_job else None

    def schedule_removal(self):
        try:
            self._aps_job.remove()
        except Exception:
            pass

    async def run(self, application):
        """Manually trigger this job's callback once, immediately. Mirrors
        telegram.ext.Job.run(), used by timer_service.py's should_run_on_startup."""
        context = application.new_context(job=self)
        try:
            await self._callback(context)
        except Exception:
            logger.exception(f"Error running job {self.name}")


class JobQueue:
    """Mirrors telegram.ext.JobQueue."""

    def __init__(self, application, timezone=None):
        self._application = application
        self._scheduler = AsyncIOScheduler(timezone=timezone)

    async def start(self):
        if not self._scheduler.running:
            self._scheduler.start()

    async def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def _make_runner(self, callback, job_holder):
        async def _runner():
            context = self._application.new_context(job=job_holder[0])
            try:
                await callback(context)
            except Exception:
                name = job_holder[0].name if job_holder[0] else "<unknown>"
                logger.exception(f"Error running job {name}")

        return _runner

    def run_repeating(self, callback, interval, first=None, name=None, data=None):
        job_holder = [None]
        if first is None:
            next_run_time = None
        else:
            next_run_time = datetime.datetime.now(self._scheduler.timezone) + _as_timedelta(first)
        aps_job = self._scheduler.add_job(
            self._make_runner(callback, job_holder),
            trigger=IntervalTrigger(seconds=_as_timedelta(interval).total_seconds()),
            next_run_time=next_run_time,
            name=name,
        )
        job = Job(aps_job, name=name, data=data, callback=callback, application=self._application)
        job_holder[0] = job
        return job

    def run_once(self, callback, when, data=None, name=None):
        job_holder = [None]
        if isinstance(when, datetime.datetime):
            run_date = when
        else:
            run_date = datetime.datetime.now(self._scheduler.timezone) + _as_timedelta(when)
        aps_job = self._scheduler.add_job(
            self._make_runner(callback, job_holder),
            trigger=DateTrigger(run_date=run_date),
            name=name,
        )
        job = Job(aps_job, name=name, data=data, callback=callback, application=self._application)
        job_holder[0] = job
        return job

    def run_custom(self, callback, job_kwargs, name=None, data=None):
        job_holder = [None]
        kwargs = dict(job_kwargs)
        trigger = kwargs.pop("trigger")
        aps_job = self._scheduler.add_job(
            self._make_runner(callback, job_holder),
            trigger=trigger,
            name=name,
            **kwargs,
        )
        job = Job(aps_job, name=name, data=data, callback=callback, application=self._application)
        job_holder[0] = job
        return job
