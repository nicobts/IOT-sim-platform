"""
API version 1 routes aggregation.
"""

from fastapi import APIRouter

from app.api.v1 import auth, sims

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(sims.router, prefix="/sims", tags=["SIM Management"])
