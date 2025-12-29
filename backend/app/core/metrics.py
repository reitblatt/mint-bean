"""Prometheus metrics for application monitoring."""

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import Engine

# HTTP Metrics
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
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Database Metrics
db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["operation"],  # select, insert, update, delete
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# Database Connection Pool Metrics
db_pool_size = Gauge(
    "db_pool_size",
    "Database connection pool size (configured maximum)",
)

db_pool_checked_out = Gauge(
    "db_pool_checked_out",
    "Number of connections currently checked out from the pool",
)

db_pool_overflow = Gauge(
    "db_pool_overflow",
    "Number of overflow connections (beyond pool_size)",
)

db_pool_checked_in = Gauge(
    "db_pool_checked_in",
    "Number of connections checked in to the pool (available)",
)

# Application Metrics
users_total = Gauge(
    "users_total",
    "Total number of users",
)

transactions_total = Gauge(
    "transactions_total",
    "Total number of transactions",
)

accounts_total = Gauge(
    "accounts_total",
    "Total number of accounts",
)

plaid_sync_duration_seconds = Histogram(
    "plaid_sync_duration_seconds",
    "Plaid sync operation duration in seconds",
)

plaid_sync_errors_total = Counter(
    "plaid_sync_errors_total",
    "Total number of Plaid sync errors",
    ["error_type"],
)

# Authentication Metrics
auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["result"],  # success, failure
)

auth_rate_limit_hits_total = Counter(
    "auth_rate_limit_hits_total",
    "Total number of rate limit hits on auth endpoints",
    ["endpoint"],
)


def update_pool_metrics(engine: Engine) -> None:
    """
    Update database connection pool metrics from SQLAlchemy engine.

    This function collects current pool statistics and updates Prometheus gauges.
    Should be called periodically (e.g., every 15 seconds) or on-demand.

    Args:
        engine: SQLAlchemy engine with connection pool
    """
    try:
        pool = engine.pool

        # Only update metrics if we have a real pool (not NullPool for SQLite)
        if hasattr(pool, "size"):
            # Pool size configuration
            db_pool_size.set(pool.size())

            # Checked out connections (currently in use)
            if hasattr(pool, "checkedout"):
                db_pool_checked_out.set(pool.checkedout())

            # Overflow connections (beyond pool_size)
            if hasattr(pool, "overflow"):
                db_pool_overflow.set(pool.overflow())

            # Checked in connections (available in pool)
            # This is: size - checkedout (available connections)
            if hasattr(pool, "checkedout"):
                checked_in = pool.size() - pool.checkedout()
                db_pool_checked_in.set(checked_in if checked_in >= 0 else 0)

    except Exception:
        # Silently ignore errors (pool might not support all attributes)
        pass
