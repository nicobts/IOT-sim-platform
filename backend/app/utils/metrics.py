"""
Prometheus metrics utilities for monitoring and observability.
"""

from typing import Callable

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# HTTP Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
)

db_errors_total = Counter(
    "db_errors_total",
    "Total database errors",
    ["error_type"],
)

# SIM management metrics
sims_total = Gauge(
    "sims_total",
    "Total number of SIMs",
    ["status"],
)

sim_sync_duration_seconds = Histogram(
    "sim_sync_duration_seconds",
    "SIM synchronization duration in seconds",
    ["sync_type"],
)

sim_sync_errors_total = Counter(
    "sim_sync_errors_total",
    "Total SIM synchronization errors",
    ["error_type"],
)

# 1NCE API metrics
once_api_requests_total = Counter(
    "once_api_requests_total",
    "Total 1NCE API requests",
    ["endpoint", "status"],
)

once_api_request_duration_seconds = Histogram(
    "once_api_request_duration_seconds",
    "1NCE API request duration in seconds",
    ["endpoint"],
)

once_api_errors_total = Counter(
    "once_api_errors_total",
    "Total 1NCE API errors",
    ["error_type"],
)

# Authentication metrics
auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["method", "result"],
)

active_sessions = Gauge(
    "active_sessions",
    "Number of active user sessions",
)

api_keys_active = Gauge(
    "api_keys_active",
    "Number of active API keys",
)

# Background job metrics
background_jobs_total = Counter(
    "background_jobs_total",
    "Total background job executions",
    ["job_name", "status"],
)

background_job_duration_seconds = Histogram(
    "background_job_duration_seconds",
    "Background job duration in seconds",
    ["job_name"],
)

background_job_errors_total = Counter(
    "background_job_errors_total",
    "Total background job errors",
    ["job_name"],
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

cache_size_bytes = Gauge(
    "cache_size_bytes",
    "Cache size in bytes",
    ["cache_type"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and collect metrics.
        """
        # Skip metrics collection for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Increment in-progress requests
        http_requests_in_progress.inc()

        # Start timer
        with http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
        ).time():
            try:
                # Process request
                response = await call_next(request)

                # Record metrics
                http_requests_total.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code,
                ).inc()

                return response

            finally:
                # Decrement in-progress requests
                http_requests_in_progress.dec()
