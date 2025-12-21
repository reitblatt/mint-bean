"""Database configuration and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


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


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
