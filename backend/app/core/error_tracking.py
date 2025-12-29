"""Error tracking configuration using Sentry SDK.

This module provides optional error tracking integration that works with:
- Self-hosted GlitchTip (recommended, lightweight Sentry alternative)
- Self-hosted Sentry
- Sentry SaaS (if desired)

Error tracking is disabled by default and only enabled when SENTRY_DSN is configured.

Configuration:
    Set the following environment variables to enable error tracking:
    - SENTRY_DSN: The Sentry/GlitchTip DSN URL
    - SENTRY_ENVIRONMENT: Environment name (production, staging, development)
    - SENTRY_TRACES_SAMPLE_RATE: Percentage of transactions to sample (0.0 to 1.0)
    - SENTRY_PROFILES_SAMPLE_RATE: Percentage of transactions to profile (0.0 to 1.0)

Example .env:
    SENTRY_DSN=http://your-glitchtip-instance/project-id
    SENTRY_ENVIRONMENT=production
    SENTRY_TRACES_SAMPLE_RATE=0.1
    SENTRY_PROFILES_SAMPLE_RATE=0.1
"""

import logging
import os

logger = logging.getLogger(__name__)


def init_error_tracking() -> None:
    """
    Initialize error tracking if SENTRY_DSN is configured.

    This function is idempotent and safe to call multiple times.
    If SENTRY_DSN is not set, error tracking is silently disabled.
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.info("Error tracking disabled (SENTRY_DSN not configured)")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        environment = os.getenv("SENTRY_ENVIRONMENT", "development")
        traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
        profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            # Performance monitoring
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",  # Group by endpoint, not URL
                    failed_request_status_codes=[500, 501, 502, 503, 504, 505],
                ),
                SqlalchemyIntegration(),
            ],
            # Release tracking
            release=os.getenv("APP_VERSION", "0.1.0"),
            # Additional configuration
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default
            # Request data
            max_request_body_size="medium",  # small, medium, large, or always
            # Breadcrumbs
            max_breadcrumbs=50,
        )

        logger.info(
            f"✓ Error tracking initialized (environment={environment}, "
            f"traces_sample_rate={traces_sample_rate})"
        )

    except ImportError:
        logger.warning("sentry-sdk not installed. Install with: pip install sentry-sdk[fastapi]")
    except Exception as e:
        logger.error(f"Failed to initialize error tracking: {e}")


def capture_exception(exception: Exception, context: dict | None = None) -> None:
    """
    Manually capture an exception to error tracking.

    Args:
        exception: The exception to capture
        context: Optional context dictionary to attach to the event
    """
    try:
        import sentry_sdk

        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                sentry_sdk.capture_exception(exception)
        else:
            sentry_sdk.capture_exception(exception)
    except ImportError:
        # Sentry not installed, just log
        logger.error(f"Exception: {exception}", exc_info=True)


def capture_message(message: str, level: str = "info", context: dict | None = None) -> None:
    """
    Manually capture a message to error tracking.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        context: Optional context dictionary to attach to the event
    """
    try:
        import sentry_sdk

        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                sentry_sdk.capture_message(message, level=level)
        else:
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        # Sentry not installed, just log
        log_func = getattr(logger, level, logger.info)
        log_func(message)
