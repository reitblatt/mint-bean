"""Database configuration and session management."""

from collections.abc import Generator
from contextvars import ContextVar

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Context variable to store current user ID for Row-Level Security
current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)
current_environment: ContextVar[str | None] = ContextVar("current_environment", default=None)


def get_database_url() -> str:
    """
    Get the database URL.

    Uses DATABASE_URL from environment/config.
    During onboarding, this will be the bootstrap SQLite database.
    After onboarding, the application will use the configured database.

    Returns:
        Database URL string
    """
    return settings.DATABASE_URL


def create_db_engine(database_url: str | None = None):
    """
    Create a SQLAlchemy engine with optimized connection pooling.

    Connection Pool Configuration:
    - PostgreSQL/MySQL: QueuePool with 5-20 connections, max overflow 10
    - SQLite: NullPool (no pooling, SQLite is file-based)

    Pool Settings:
    - pool_size: Number of permanent connections (default: 5)
    - max_overflow: Additional connections when pool exhausted (default: 10)
    - pool_timeout: Seconds to wait for connection (default: 30)
    - pool_recycle: Recycle connections after 1 hour (prevents stale connections)
    - pool_pre_ping: Test connection before using (ensures valid connections)

    Args:
        database_url: Optional database URL. If not provided, uses get_database_url()

    Returns:
        SQLAlchemy engine with optimized pooling
    """
    import os

    url = database_url or get_database_url()
    connect_args = {}
    engine_kwargs = {"echo": settings.DEBUG}

    # SQLite-specific configuration
    if "sqlite" in url:
        connect_args["check_same_thread"] = False
        # Use NullPool for SQLite (no connection pooling needed)
        from sqlalchemy.pool import NullPool

        engine_kwargs["poolclass"] = NullPool
    else:
        # PostgreSQL/MySQL production configuration
        # Pool size: number of permanent connections to maintain
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        # Max overflow: additional connections beyond pool_size
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        # Pool timeout: seconds to wait for a connection
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        # Pool recycle: recycle connections after this many seconds (prevents stale connections)
        pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

        engine_kwargs.update(
            {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": pool_timeout,
                "pool_recycle": pool_recycle,
                # Pre-ping: test connection before using (small overhead, ensures valid connections)
                "pool_pre_ping": True,
            }
        )

    return create_engine(url, connect_args=connect_args, **engine_kwargs)


# Create SQLAlchemy engine using bootstrap DATABASE_URL
engine = create_db_engine()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


@event.listens_for(Session, "after_begin")
def set_rls_context(session, transaction, connection):
    """
    Set PostgreSQL session variables for Row-Level Security.

    This event handler runs after every transaction begins and sets the
    current user ID and environment in PostgreSQL session variables.
    RLS policies use these variables to filter rows.

    Only runs on PostgreSQL (silently skips for SQLite).
    """
    # Only set RLS context for PostgreSQL
    if "postgresql" not in str(connection.engine.url):
        return

    user_id = current_user_id.get()
    environment = current_environment.get()

    try:
        # Set user context for RLS policies
        if user_id is not None:
            session.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))

        # Set environment context for RLS policies
        if environment is not None:
            session.execute(text(f"SET LOCAL app.current_environment = '{environment}'"))
    except Exception:
        # Silently ignore errors (e.g., if RLS is not enabled yet)
        pass


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    For PostgreSQL with RLS enabled, this automatically sets the user context
    from the current_user_id context variable.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_current_user_for_rls(user_id: int | None):
    """
    Set the current user ID for Row-Level Security.

    This should be called in authentication middleware or dependencies
    to set the user context for RLS policies.

    Args:
        user_id: The ID of the current user, or None to clear
    """
    current_user_id.set(user_id)


def set_current_environment_for_rls(environment: str | None):
    """
    Set the current environment for Row-Level Security.

    This should be called when the environment setting is loaded
    to set the environment context for RLS policies.

    Args:
        environment: The current environment ('sandbox' or 'production'), or None to clear
    """
    current_environment.set(environment)
