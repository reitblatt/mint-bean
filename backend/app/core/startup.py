"""Startup validation and initialization."""

import logging
import os
import sys

logger = logging.getLogger(__name__)


def validate_environment() -> None:
    """
    Validate required environment variables on startup.

    Exits with error code 1 if any required variables are missing.
    This prevents the application from starting in a misconfigured state.
    """
    required_vars = {
        "ENCRYPTION_KEY": "Required for encrypting secrets in database",
        "SECRET_KEY": "Required for JWT token signing",
    }

    optional_vars = {
        "DATABASE_URL": "Database connection string (defaults to SQLite)",
        "POSTGRES_DB": "PostgreSQL database name (if using PostgreSQL)",
        "POSTGRES_USER": "PostgreSQL username (if using PostgreSQL)",
        "POSTGRES_PASSWORD": "PostgreSQL password (if using PostgreSQL)",
        "ALLOWED_ORIGINS": "CORS allowed origins (defaults to localhost)",
    }

    missing_required = []
    warnings = []

    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_required.append(f"  - {var}: {description}")
        else:
            logger.info(f"✓ {var} is configured")

    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value:
            warnings.append(f"  - {var}: {description} (using default)")
        else:
            logger.info(f"✓ {var} is configured")

    # Report results
    if missing_required:
        logger.error("=" * 70)
        logger.error("STARTUP VALIDATION FAILED")
        logger.error("=" * 70)
        logger.error("\nMissing required environment variables:\n")
        for msg in missing_required:
            logger.error(msg)
        logger.error("\nPlease set these variables in your .env file or environment.")
        logger.error("See .env.example for reference.\n")
        logger.error("=" * 70)
        sys.exit(1)

    if warnings:
        logger.warning("\nOptional environment variables not set:")
        for msg in warnings:
            logger.warning(msg)

    logger.info("\n✅ Environment validation passed")


def validate_encryption_key() -> None:
    """
    Validate that the encryption key is a valid Fernet key.

    Exits with error code 1 if the key is invalid.
    """
    from cryptography.fernet import Fernet

    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        return  # Already caught by validate_environment()

    try:
        # Try to create a Fernet instance to validate the key
        Fernet(encryption_key.encode())
        logger.info("✓ Encryption key is valid")
    except Exception as e:
        logger.error("=" * 70)
        logger.error("INVALID ENCRYPTION KEY")
        logger.error("=" * 70)
        logger.error(f"\nThe ENCRYPTION_KEY environment variable is invalid: {e}")
        logger.error("\nGenerate a new key with:")
        logger.error(
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
        logger.error("\nThen update your .env file with the new key.")
        logger.error("=" * 70)
        sys.exit(1)


def run_startup_checks() -> None:
    """
    Run all startup validation checks.

    Call this function before starting the FastAPI application.
    """
    logger.info("=" * 70)
    logger.info("Running startup validation checks...")
    logger.info("=" * 70)

    validate_environment()
    validate_encryption_key()

    logger.info("=" * 70)
    logger.info("✅ All startup checks passed - application ready to start")
    logger.info("=" * 70)
