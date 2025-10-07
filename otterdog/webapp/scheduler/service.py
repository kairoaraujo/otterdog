#  *******************************************************************************
#  Copyright (c) 2024-2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

if TYPE_CHECKING:
    from quart import Quart

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Background scheduler service using APScheduler.
    Manages periodic tasks like permissions review checks.
    """

    def __init__(self):
        self.scheduler: AsyncIOScheduler | None = None
        self.app: Quart | None = None
        self._initialized = False

    def init_app(self, app: Quart) -> None:
        """Initialize the scheduler with the Quart app."""
        self.app = app

        # Configure scheduler
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 3600,  # TODO: make it configurable?
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc
        )

        self._register_jobs()
        self._initialized = True

    def _register_jobs(self) -> None:
        """Register all scheduled jobs."""
        if not self.scheduler:
            return

        from .tasks.permissions_review import run_permissions_review_check

        # TESTING IT for every 10 min
        self.scheduler.add_job(
            run_permissions_review_check,
            "cron",
            minute="*/10",
            id="permissions_review_check",
            name="Permissions Review Check",
            replace_existing=True,
            kwargs={"app": self.app},
        )

        logger.info("Registered permissions review daily check at 02:00 UTC")

    async def start(self) -> None:
        """Start the scheduler."""
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized. Call init_app first.")

        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler service started")

    async def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler service stopped")

    def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a scheduled job by its ID."""
        if not self.scheduler:
            return False

        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.add_job(
                job.func,
                trigger="date",
                id=f"{job_id}_manual_{datetime.now().timestamp()}",
                kwargs=job.kwargs,
            )
            logger.info(f"Manually triggered job: {job_id}")
            return True
        return False


scheduler_service = SchedulerService()
