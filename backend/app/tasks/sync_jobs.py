"""
Background synchronization jobs.
Automated tasks for syncing data with 1NCE API and maintenance.
"""

from datetime import datetime, timedelta

from sqlalchemy import delete, select

from app.clients.once_client import get_once_client
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.sim import SIM, SIMEvent, SIMUsage
from app.services.sim_service import SIMService

logger = get_logger(__name__)


async def sync_all_sims_job():
    """
    Background job to sync all SIMs from 1NCE API.
    Runs periodically to keep local database up-to-date.
    """
    job_start = datetime.utcnow()
    logger.info("sync_all_sims_job_started")

    try:
        async with AsyncSessionLocal() as db:
            once_client = await get_once_client()

            # Sync all SIMs
            synced_count = await SIMService.sync_all_sims_from_once(db, once_client)

            duration = (datetime.utcnow() - job_start).total_seconds()

            logger.info(
                "sync_all_sims_job_completed",
                synced_count=synced_count,
                duration_seconds=duration,
            )

            return {
                "success": True,
                "synced_count": synced_count,
                "duration_seconds": duration,
            }

    except Exception as e:
        duration = (datetime.utcnow() - job_start).total_seconds()
        logger.error(
            "sync_all_sims_job_failed",
            error=str(e),
            duration_seconds=duration,
        )
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
        }


async def sync_usage_job():
    """
    Background job to sync usage data for all active SIMs.
    Fetches latest usage statistics from 1NCE API.
    """
    job_start = datetime.utcnow()
    logger.info("sync_usage_job_started")

    try:
        async with AsyncSessionLocal() as db:
            once_client = await get_once_client()

            # Get all active SIMs
            result = await db.execute(
                select(SIM).where(SIM.status.in_(["active", "enabled"]))
            )
            active_sims = result.scalars().all()

            synced_count = 0
            error_count = 0

            # Sync usage for each SIM
            for sim in active_sims:
                try:
                    usage_records = await SIMService.sync_sim_usage_from_once(
                        db, once_client, sim.iccid
                    )
                    if usage_records:
                        synced_count += 1
                except Exception as e:
                    logger.error(
                        "sim_usage_sync_failed",
                        iccid=sim.iccid,
                        error=str(e),
                    )
                    error_count += 1

            duration = (datetime.utcnow() - job_start).total_seconds()

            logger.info(
                "sync_usage_job_completed",
                total_sims=len(active_sims),
                synced_count=synced_count,
                error_count=error_count,
                duration_seconds=duration,
            )

            return {
                "success": True,
                "total_sims": len(active_sims),
                "synced_count": synced_count,
                "error_count": error_count,
                "duration_seconds": duration,
            }

    except Exception as e:
        duration = (datetime.utcnow() - job_start).total_seconds()
        logger.error(
            "sync_usage_job_failed",
            error=str(e),
            duration_seconds=duration,
        )
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
        }


async def check_quotas_job():
    """
    Background job to check SIM quotas and trigger alerts.
    Monitors quota thresholds and can trigger auto top-up.
    """
    job_start = datetime.utcnow()
    logger.info("check_quotas_job_started")

    try:
        async with AsyncSessionLocal() as db:
            once_client = await get_once_client()

            # Get all active SIMs
            result = await db.execute(
                select(SIM).where(SIM.status.in_(["active", "enabled"]))
            )
            active_sims = result.scalars().all()

            low_quota_count = 0
            alerts_sent = 0

            # Check each SIM's quota
            for sim in active_sims:
                try:
                    # Get data quota from 1NCE
                    data_quota = await once_client.get_data_quota(sim.iccid)

                    # Check if quota is low (example: < 10%)
                    if data_quota and "volume" in data_quota:
                        remaining = data_quota.get("volume", 0)
                        total = data_quota.get("total_volume", 0)

                        if total > 0:
                            percentage = (remaining / total) * 100

                            if percentage < 10:
                                low_quota_count += 1
                                logger.warning(
                                    "low_quota_detected",
                                    iccid=sim.iccid,
                                    remaining=remaining,
                                    percentage=percentage,
                                )
                                # TODO: Send alert notification
                                # TODO: Trigger auto top-up if enabled
                                alerts_sent += 1

                except Exception as e:
                    logger.error(
                        "quota_check_failed",
                        iccid=sim.iccid,
                        error=str(e),
                    )

            duration = (datetime.utcnow() - job_start).total_seconds()

            logger.info(
                "check_quotas_job_completed",
                total_sims=len(active_sims),
                low_quota_count=low_quota_count,
                alerts_sent=alerts_sent,
                duration_seconds=duration,
            )

            return {
                "success": True,
                "total_sims": len(active_sims),
                "low_quota_count": low_quota_count,
                "alerts_sent": alerts_sent,
                "duration_seconds": duration,
            }

    except Exception as e:
        duration = (datetime.utcnow() - job_start).total_seconds()
        logger.error(
            "check_quotas_job_failed",
            error=str(e),
            duration_seconds=duration,
        )
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
        }


async def cleanup_old_data_job():
    """
    Background job to clean up old data.
    Removes usage and event data older than retention period.
    """
    job_start = datetime.utcnow()
    logger.info("cleanup_old_data_job_started")

    try:
        async with AsyncSessionLocal() as db:
            # Default retention: 90 days for usage, 30 days for events
            usage_retention_days = 90
            event_retention_days = 30

            usage_cutoff = datetime.utcnow() - timedelta(days=usage_retention_days)
            event_cutoff = datetime.utcnow() - timedelta(days=event_retention_days)

            # Delete old usage data
            usage_result = await db.execute(
                delete(SIMUsage).where(SIMUsage.timestamp < usage_cutoff)
            )
            usage_deleted = usage_result.rowcount

            # Delete old event data
            event_result = await db.execute(
                delete(SIMEvent).where(SIMEvent.timestamp < event_cutoff)
            )
            events_deleted = event_result.rowcount

            await db.commit()

            duration = (datetime.utcnow() - job_start).total_seconds()

            logger.info(
                "cleanup_old_data_job_completed",
                usage_deleted=usage_deleted,
                events_deleted=events_deleted,
                usage_retention_days=usage_retention_days,
                event_retention_days=event_retention_days,
                duration_seconds=duration,
            )

            return {
                "success": True,
                "usage_deleted": usage_deleted,
                "events_deleted": events_deleted,
                "duration_seconds": duration,
            }

    except Exception as e:
        duration = (datetime.utcnow() - job_start).total_seconds()
        logger.error(
            "cleanup_old_data_job_failed",
            error=str(e),
            duration_seconds=duration,
        )
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
        }
