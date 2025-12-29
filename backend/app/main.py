"""Main FastAPI application entry point."""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.error_tracking import init_error_tracking
from app.core.limiter import limiter
from app.core.metrics import (
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
    update_pool_metrics,
)
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.startup import run_startup_checks

# Run startup validation checks
run_startup_checks()

# Initialize error tracking (optional, only if SENTRY_DSN is set)
init_error_tracking()

# Create database tables
Base.metadata.create_all(bind=engine)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        """Track request metrics."""
        # Skip metrics for /metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            # Update pool metrics before serving /metrics endpoint
            update_pool_metrics(engine)
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()

        # Track request duration
        start_time = time.time()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise e
        finally:
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(method=method, endpoint=path, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
            http_requests_in_progress.labels(method=method, endpoint=path).dec()

        return response


app = FastAPI(
    title="MintBean API",
    description="A Mint.com clone for beancount accounting",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add rate limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure security headers middleware (first, so it applies to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# Configure metrics middleware (before CORS so we track all requests)
app.add_middleware(MetricsMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health/live")
async def liveness_check() -> dict:
    """
    Liveness probe - checks if the application is running.

    This is a lightweight check that doesn't verify dependencies.
    Used by Kubernetes/orchestrators to know if the pod should be restarted.
    """
    return {"status": "alive", "version": "0.1.0"}


@app.get("/health/ready")
async def readiness_check() -> dict:
    """
    Readiness probe - checks if the application is ready to serve traffic.

    Verifies database connectivity and other critical dependencies.
    Used by load balancers to know if traffic should be routed to this instance.
    """
    from sqlalchemy import text

    from app.core.database import SessionLocal

    checks = {
        "status": "ready",
        "version": "0.1.0",
        "checks": {},
    }

    # Check database connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["checks"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        checks["status"] = "not_ready"
        checks["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }

    # Check encryption key is configured
    import os

    if os.getenv("ENCRYPTION_KEY"):
        checks["checks"]["encryption"] = {"status": "healthy", "message": "Key configured"}
    else:
        checks["status"] = "not_ready"
        checks["checks"]["encryption"] = {
            "status": "unhealthy",
            "message": "ENCRYPTION_KEY not set",
        }

    return checks


@app.get("/health")
async def health_check() -> dict:
    """
    Legacy health check endpoint.

    Deprecated: Use /health/live for liveness and /health/ready for readiness.
    """
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "MintBean API",
        "docs": "/api/docs",
        "version": "0.1.0",
    }
