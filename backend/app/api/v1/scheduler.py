"""
Scheduler management endpoints.
Monitor and control background task scheduler.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps import get_current_superuser
from app.core.config import settings
from app.models.user import User
from app.tasks.scheduler import get_job_stats, scheduler

router = APIRouter()


@router.get("/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    Get scheduler status and job statistics.

    **Permissions**: Superuser only

    Returns:
        - enabled: Whether scheduler is enabled
        - running: Whether scheduler is currently running
        - jobs: List of scheduled jobs with their details
    """
    if not settings.ENABLE_SCHEDULER:
        return {
            "enabled": False,
            "running": False,
            "message": "Scheduler is disabled via configuration",
        }

    if scheduler is None:
        return {
            "enabled": True,
            "running": False,
            "message": "Scheduler not initialized",
        }

    # Get job statistics
    stats = get_job_stats()

    return {
        "enabled": True,
        "running": scheduler.running,
        "state": scheduler.state,
        "jobs": stats.get("jobs", []),
        "total_jobs": stats.get("total_jobs", 0),
    }


@router.get("/jobs/{job_id}")
async def get_job_details(
    job_id: str,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    Get details for a specific scheduled job.

    **Permissions**: Superuser only

    Args:
        job_id: Job identifier

    Returns:
        Job details including schedule and last run time

    Raises:
        404: Job not found
        503: Scheduler not running
    """
    if not settings.ENABLE_SCHEDULER or scheduler is None:
        raise HTTPException(
            status_code=503,
            detail="Scheduler is not running",
        )

    # Get job from scheduler
    job = scheduler.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found",
        )

    return {
        "id": job.id,
        "name": job.name,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "trigger": str(job.trigger),
    }
