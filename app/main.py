"""
FastAPI application entry point.
IOT SIM Management and Monitoring Server with 1NCE Integration.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.api.v1 import api_router
from app.clients.once_client import close_once_client
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import close_db
from app.tasks.scheduler import start_scheduler, stop_scheduler
from app.utils.metrics import MetricsMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_startup",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Initialize services here if needed
    # await init_db()  # Only in development, use Alembic in production

    # Start background task scheduler
    if settings.ENABLE_SCHEDULER:
        logger.info("starting_scheduler")
        await start_scheduler()
        logger.info("scheduler_started")
    else:
        logger.info("scheduler_disabled_via_config")

    yield

    # Shutdown
    logger.info("application_shutdown")

    # Stop scheduler
    if settings.ENABLE_SCHEDULER:
        logger.info("stopping_scheduler")
        await stop_scheduler()
        logger.info("scheduler_stopped")

    # Close connections
    await close_once_client()
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI server for 1NCE IoT SIM management and monitoring",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Metrics middleware
if settings.ENABLE_METRICS:
    app.add_middleware(MetricsMiddleware)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
        client_ip=request.client.host if request.client else None,
    )

    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 OK if the application is running.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Checks if the application is ready to serve traffic.
    """
    # TODO: Add checks for database, Redis, 1NCE API connectivity
    checks = {
        "database": "ok",  # Placeholder
        "redis": "ok",  # Placeholder
        "once_api": "ok",  # Placeholder
    }

    all_healthy = all(status == "ok" for status in checks.values())

    if not all_healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }


@app.get("/health/live", tags=["Health"])
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    Returns 200 OK if the application process is alive.
    """
    return {"status": "alive"}


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "FastAPI server for 1NCE IoT SIM management",
        "docs_url": "/docs" if settings.DEBUG else "Disabled in production",
        "health_check": "/health",
        "api_prefix": settings.API_V1_PREFIX,
    }


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
