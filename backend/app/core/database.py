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
    Create a SQLAlchemy engine.

    Args:
        database_url: Optional database URL. If not provided, uses get_database_url()

    Returns:
        SQLAlchemy engine
    """
    url = database_url or get_database_url()
    connect_args = {}

    # SQLite-specific connection args
    if "sqlite" in url:
        connect_args["check_same_thread"] = False

    return create_engine(url, connect_args=connect_args, echo=settings.DEBUG)


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
