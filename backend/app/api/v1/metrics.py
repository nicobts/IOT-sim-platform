"""
Prometheus metrics endpoint.
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.

    **Note**: Only enabled when ENABLE_METRICS is True in settings.
    """
    if not settings.ENABLE_METRICS:
        return Response(
            content="Metrics are disabled",
            status_code=404,
        )

    # Generate Prometheus metrics
    metrics_output = generate_latest()

    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST,
    )
