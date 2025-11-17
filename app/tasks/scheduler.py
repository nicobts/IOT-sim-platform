"""
Background task scheduler using APScheduler.
Manages automated synchronization and maintenance tasks.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """
    Get or create the global scheduler instance.

    Returns:
        AsyncIOScheduler instance
    """
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance per job
                'misfire_grace_time': 300,  # 5 minutes grace period
            }
        )
        logger.info("scheduler_created")

    return scheduler


async def start_scheduler():
    """
    Start the background task scheduler.
    Registers all scheduled jobs and starts the scheduler.
    """
    if not settings.ENABLE_SCHEDULER:
        logger.info("scheduler_disabled")
        return

    scheduler = get_scheduler()

    # Import jobs here to avoid circular imports
    from app.tasks.sync_jobs import (
        sync_all_sims_job,
        sync_usage_job,
        check_quotas_job,
        cleanup_old_data_job,
    )

    # Register scheduled jobs
    jobs = []

    # Sync all SIMs every X minutes
    if settings.SYNC_SIMS_INTERVAL_MINUTES > 0:
        scheduler.add_job(
            sync_all_sims_job,
            trigger=IntervalTrigger(minutes=settings.SYNC_SIMS_INTERVAL_MINUTES),
            id='sync_all_sims',
            name='Sync All SIMs from 1NCE',
            replace_existing=True,
        )
        jobs.append(f"sync_all_sims (every {settings.SYNC_SIMS_INTERVAL_MINUTES}m)")

    # Sync usage data every X minutes
    if settings.SYNC_USAGE_INTERVAL_MINUTES > 0:
        scheduler.add_job(
            sync_usage_job,
            trigger=IntervalTrigger(minutes=settings.SYNC_USAGE_INTERVAL_MINUTES),
            id='sync_usage',
            name='Sync Usage Data from 1NCE',
            replace_existing=True,
        )
        jobs.append(f"sync_usage (every {settings.SYNC_USAGE_INTERVAL_MINUTES}m)")

    # Check quotas every X minutes
    if settings.CHECK_QUOTAS_INTERVAL_MINUTES > 0:
        scheduler.add_job(
            check_quotas_job,
            trigger=IntervalTrigger(minutes=settings.CHECK_QUOTAS_INTERVAL_MINUTES),
            id='check_quotas',
            name='Check SIM Quotas',
            replace_existing=True,
        )
        jobs.append(f"check_quotas (every {settings.CHECK_QUOTAS_INTERVAL_MINUTES}m)")

    # Cleanup old data daily at 2 AM UTC
    scheduler.add_job(
        cleanup_old_data_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='cleanup_old_data',
        name='Cleanup Old Data',
        replace_existing=True,
    )
    jobs.append("cleanup_old_data (daily at 2 AM UTC)")

    # Start the scheduler
    scheduler.start()

    logger.info(
        "scheduler_started",
        jobs_count=len(jobs),
        jobs=jobs,
    )


async def stop_scheduler():
    """
    Stop the background task scheduler gracefully.
    """
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("scheduler_stopped")
        scheduler = None


def get_job_stats() -> dict:
    """
    Get statistics about scheduled jobs.

    Returns:
        Dictionary with job statistics
    """
    scheduler = get_scheduler()

    if not scheduler:
        return {"status": "not_running", "jobs": []}

    jobs = scheduler.get_jobs()

    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs_count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ],
    }
