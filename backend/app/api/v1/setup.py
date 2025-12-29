"""Interactive setup wizard API for first-time deployment configuration."""

import os
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

router = APIRouter()


class SetupStatusResponse(BaseModel):
    """Response schema for setup status check."""

    needs_setup: bool
    has_admin_user: bool
    has_database: bool
    has_encryption_key: bool
    has_secret_key: bool
    has_plaid_credentials: bool
    database_type: str | None = None
    setup_steps_remaining: list[str]


class DatabaseTestRequest(BaseModel):
    """Request schema for testing database connection."""

    database_url: str = Field(..., description="PostgreSQL connection string")


class DatabaseTestResponse(BaseModel):
    """Response schema for database connection test."""

    success: bool
    message: str
    details: dict[str, Any] | None = None


class EncryptionKeyGenerateResponse(BaseModel):
    """Response schema for generating encryption key."""

    encryption_key: str
    instructions: str


@router.get("/status", response_model=SetupStatusResponse)
def get_setup_status(db: Session = Depends(get_db)) -> SetupStatusResponse:
    """
    Get current setup status and determine which steps remain.

    This endpoint helps guide users through the initial setup process by
    checking what configuration is complete and what still needs to be done.

    Returns:
        SetupStatusResponse: Current setup status and remaining steps
    """
    # Check if admin user exists
    has_admin_user = db.query(User).filter(User.is_admin == True).count() > 0  # noqa: E712

    # Check environment variables
    has_encryption_key = bool(os.getenv("ENCRYPTION_KEY"))
    has_secret_key = bool(os.getenv("SECRET_KEY"))
    has_plaid_client = bool(os.getenv("PLAID_CLIENT_ID"))
    has_plaid_secret = bool(os.getenv("PLAID_SECRET"))
    has_plaid_credentials = has_plaid_client and has_plaid_secret

    # Determine database type
    database_url = os.getenv("DATABASE_URL", "")
    if "postgresql" in database_url:
        database_type = "postgresql"
        has_database = True
    elif "mysql" in database_url:
        database_type = "mysql"
        has_database = True
    elif "sqlite" in database_url:
        database_type = "sqlite"
        has_database = True
    else:
        database_type = None
        has_database = False

    # Determine remaining steps
    steps_remaining = []
    if not has_database:
        steps_remaining.append("Configure database connection")
    if not has_encryption_key:
        steps_remaining.append("Generate and set ENCRYPTION_KEY")
    if not has_secret_key:
        steps_remaining.append("Generate and set SECRET_KEY")
    if not has_admin_user:
        steps_remaining.append("Create admin user")
    if not has_plaid_credentials:
        steps_remaining.append("Configure Plaid credentials (optional)")

    needs_setup = len(steps_remaining) > 0

    return SetupStatusResponse(
        needs_setup=needs_setup,
        has_admin_user=has_admin_user,
        has_database=has_database,
        has_encryption_key=has_encryption_key,
        has_secret_key=has_secret_key,
        has_plaid_credentials=has_plaid_credentials,
        database_type=database_type,
        setup_steps_remaining=steps_remaining,
    )


@router.post("/test-database", response_model=DatabaseTestResponse)
def test_database_connection(request: DatabaseTestRequest) -> DatabaseTestResponse:
    """
    Test database connection with provided credentials.

    This endpoint allows users to verify their database configuration
    before saving it permanently. Useful for AWS RDS setup.

    Args:
        request: Database connection details

    Returns:
        DatabaseTestResponse: Connection test results
    """
    try:
        from sqlalchemy import create_engine

        # Create temporary engine with provided URL
        test_engine = create_engine(request.database_url, pool_pre_ping=True)

        # Test connection
        with test_engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.scalar()

            # Get additional info
            if "postgresql" in request.database_url:
                db_info = connection.execute(
                    text(
                        "SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"
                    )
                ).first()

                details = {
                    "database_type": "PostgreSQL",
                    "version": version,
                    "database": db_info[0] if db_info else None,
                    "user": db_info[1] if db_info else None,
                    "host": str(db_info[2]) if db_info and db_info[2] else None,
                    "port": db_info[3] if db_info else None,
                }
            else:
                details = {
                    "database_type": "MySQL/MariaDB",
                    "version": version,
                }

        test_engine.dispose()

        return DatabaseTestResponse(
            success=True,
            message="Database connection successful",
            details=details,
        )

    except Exception as e:
        error_message = str(e)

        # Provide helpful error messages for common issues
        if "could not connect" in error_message.lower():
            message = "Cannot reach database server. Check host and port, and ensure security groups allow connections."
        elif (
            "authentication failed" in error_message.lower() or "password" in error_message.lower()
        ):
            message = "Authentication failed. Check username and password."
        elif "database" in error_message.lower() and "does not exist" in error_message.lower():
            message = (
                "Database does not exist. Create the database first or check the database name."
            )
        elif "ssl" in error_message.lower():
            message = "SSL/TLS connection issue. You may need to configure SSL parameters."
        else:
            message = f"Connection failed: {error_message}"

        return DatabaseTestResponse(
            success=False,
            message=message,
            details={"error": error_message},
        )


@router.post("/generate-encryption-key", response_model=EncryptionKeyGenerateResponse)
def generate_encryption_key() -> EncryptionKeyGenerateResponse:
    """
    Generate a new Fernet encryption key.

    This key is used to encrypt sensitive data like Plaid access tokens
    in the database.

    CRITICAL: Save this key securely! If lost, encrypted data cannot be recovered.

    Returns:
        EncryptionKeyGenerateResponse: Generated key and storage instructions
    """
    from cryptography.fernet import Fernet

    encryption_key = Fernet.generate_key().decode()

    instructions = """
IMPORTANT: Save this encryption key securely!

For AWS Secrets Manager:
  aws secretsmanager create-secret \\
    --name mintbean/encryption-key \\
    --description "MintBean Fernet encryption key" \\
    --secret-string "YOUR_KEY_HERE"

For .env file (development only):
  echo "ENCRYPTION_KEY=YOUR_KEY_HERE" >> .env

WARNING: If you lose this key, you will NOT be able to decrypt your data!
Store it securely in AWS Secrets Manager, AWS Systems Manager Parameter Store,
or another secure secrets management system.
"""

    return EncryptionKeyGenerateResponse(
        encryption_key=encryption_key,
        instructions=instructions,
    )


@router.post("/generate-secret-key")
def generate_secret_key() -> dict[str, str]:
    """
    Generate a new secret key for JWT token signing.

    This key is used to sign authentication tokens.

    Returns:
        dict: Generated secret key and storage instructions
    """
    import secrets

    secret_key = secrets.token_hex(32)

    instructions = """
Save this secret key securely!

For AWS Secrets Manager:
  aws secretsmanager create-secret \\
    --name mintbean/secret-key \\
    --description "MintBean JWT secret key" \\
    --secret-string "YOUR_KEY_HERE"

For .env file (development only):
  echo "SECRET_KEY=YOUR_KEY_HERE" >> .env
"""

    return {
        "secret_key": secret_key,
        "instructions": instructions,
    }


@router.get("/aws-checklist")
def get_aws_setup_checklist() -> dict[str, Any]:
    """
    Get AWS deployment checklist with current status.

    Provides a comprehensive checklist for AWS deployment including
    RDS, Secrets Manager, ECS, and other AWS services.

    Returns:
        dict: Checklist with status and instructions
    """
    # Get current status
    has_encryption_key = bool(os.getenv("ENCRYPTION_KEY"))
    has_secret_key = bool(os.getenv("SECRET_KEY"))
    database_url = os.getenv("DATABASE_URL", "")
    has_rds = "amazonaws.com" in database_url or "rds" in database_url

    # Check if running in AWS (basic detection)
    ecs_metadata = os.getenv("ECS_CONTAINER_METADATA_URI")
    running_on_ecs = bool(ecs_metadata)

    checklist = {
        "infrastructure": {
            "title": "AWS Infrastructure Setup",
            "steps": [
                {
                    "name": "Create VPC and subnets",
                    "status": "unknown",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 1.1",
                },
                {
                    "name": "Create security groups",
                    "status": "unknown",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 1.2",
                },
                {
                    "name": "Create RDS PostgreSQL instance",
                    "status": "complete" if has_rds else "pending",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 1.3",
                },
                {
                    "name": "Create Secrets Manager secrets",
                    "status": "complete" if (has_encryption_key and has_secret_key) else "pending",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 1.4",
                },
                {
                    "name": "Create S3 bucket for beancount files",
                    "status": "unknown",
                    "required": False,
                    "instructions": "See DEPLOYMENT_AWS.md Step 1.5",
                },
            ],
        },
        "application": {
            "title": "Application Deployment",
            "steps": [
                {
                    "name": "Build and push Docker images to ECR",
                    "status": "unknown",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 2",
                },
                {
                    "name": "Create ECS cluster and services",
                    "status": "complete" if running_on_ecs else "pending",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 3",
                },
                {
                    "name": "Configure Application Load Balancer",
                    "status": "unknown",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 3.5",
                },
                {
                    "name": "Set up DNS and SSL certificate",
                    "status": "unknown",
                    "required": True,
                    "instructions": "See DEPLOYMENT_AWS.md Step 4",
                },
            ],
        },
        "configuration": {
            "title": "Application Configuration",
            "steps": [
                {
                    "name": "Set ENCRYPTION_KEY in Secrets Manager",
                    "status": "complete" if has_encryption_key else "pending",
                    "required": True,
                    "instructions": "Use /setup/generate-encryption-key endpoint",
                },
                {
                    "name": "Set SECRET_KEY in Secrets Manager",
                    "status": "complete" if has_secret_key else "pending",
                    "required": True,
                    "instructions": "Use /setup/generate-secret-key endpoint",
                },
                {
                    "name": "Configure DATABASE_URL",
                    "status": "complete" if has_rds else "pending",
                    "required": True,
                    "instructions": "Use /setup/test-database endpoint to verify",
                },
                {
                    "name": "Create admin user",
                    "status": "unknown",
                    "required": True,
                    "instructions": "Use /onboarding/complete endpoint after setup",
                },
                {
                    "name": "Configure Plaid credentials",
                    "status": "unknown",
                    "required": False,
                    "instructions": "Set via application settings after onboarding",
                },
            ],
        },
        "monitoring": {
            "title": "Monitoring and Observability (Optional)",
            "steps": [
                {
                    "name": "Set up CloudWatch alarms",
                    "status": "unknown",
                    "required": False,
                    "instructions": "Configure alarms for ECS, RDS, ALB health",
                },
                {
                    "name": "Configure error tracking (Sentry/GlitchTip)",
                    "status": "unknown",
                    "required": False,
                    "instructions": "Set SENTRY_DSN environment variable",
                },
                {
                    "name": "Enable RDS enhanced monitoring",
                    "status": "unknown",
                    "required": False,
                    "instructions": "Enable in RDS console",
                },
            ],
        },
    }

    # Calculate overall progress
    total_required = 0
    completed_required = 0

    for section in checklist.values():
        for step in section["steps"]:
            if step["required"]:
                total_required += 1
                if step["status"] == "complete":
                    completed_required += 1

    progress = {
        "total_required_steps": total_required,
        "completed_required_steps": completed_required,
        "completion_percentage": round((completed_required / total_required) * 100)
        if total_required > 0
        else 0,
        "ready_for_onboarding": completed_required == total_required,
    }

    return {
        "checklist": checklist,
        "progress": progress,
        "environment": {
            "running_on_ecs": running_on_ecs,
            "has_rds": has_rds,
            "database_url_configured": bool(database_url),
        },
    }


@router.get("/rds-connection-string-help")
def get_rds_connection_string_help() -> dict[str, Any]:
    """
    Get help for constructing RDS PostgreSQL connection string.

    Provides template and examples for AWS RDS connection strings.

    Returns:
        dict: Connection string templates and examples
    """
    return {
        "template": "postgresql://{username}:{password}@{endpoint}:{port}/{database}",
        "example": "postgresql://mintbean_admin:YOUR_PASSWORD@mintbean-db.xxxxx.us-east-1.rds.amazonaws.com:5432/postgres",
        "parameters": {
            "username": {
                "description": "Database master username",
                "example": "mintbean_admin",
                "from": "Specified when creating RDS instance",
            },
            "password": {
                "description": "Database master password",
                "example": "your-secure-password",
                "from": "Specified when creating RDS instance",
            },
            "endpoint": {
                "description": "RDS instance endpoint",
                "example": "mintbean-db.xxxxx.us-east-1.rds.amazonaws.com",
                "from": "RDS console or: aws rds describe-db-instances --db-instance-identifier mintbean-db",
            },
            "port": {
                "description": "Database port",
                "example": "5432",
                "default": "5432 for PostgreSQL",
            },
            "database": {
                "description": "Database name",
                "example": "postgres",
                "default": "postgres (initial database created by RDS)",
            },
        },
        "aws_cli_command": "aws rds describe-db-instances --db-instance-identifier mintbean-db --query 'DBInstances[0].Endpoint.Address' --output text",
        "ssl_parameters": {
            "recommended": True,
            "connection_string": "postgresql://{username}:{password}@{endpoint}:{port}/{database}?sslmode=require",
            "note": "AWS RDS supports SSL by default. Use sslmode=require for encrypted connections.",
        },
        "testing": {
            "endpoint": "/api/v1/setup/test-database",
            "method": "POST",
            "body": {"database_url": "postgresql://..."},
        },
    }
