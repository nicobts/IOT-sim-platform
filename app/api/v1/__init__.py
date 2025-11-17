"""
API version 1 routes aggregation.
"""

from fastapi import APIRouter

from app.api.v1 import auth, metrics, scheduler, sims

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(sims.router, prefix="/sims", tags=["SIM Management"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])
api_router.include_router(metrics.router, tags=["Metrics"])
