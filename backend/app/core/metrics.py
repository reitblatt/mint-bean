"""Prometheus metrics for application monitoring."""

from prometheus_client import Counter, Gauge, Histogram

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
