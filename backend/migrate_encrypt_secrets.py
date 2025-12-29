#!/usr/bin/env python3
"""
Migration script to encrypt sensitive fields in app_settings table.

This script:
1. Expands column sizes to accommodate encrypted data (255 -> 500 chars)
2. Encrypts existing plaintext secrets in the database
3. Validates encryption/decryption works correctly

Usage:
    # Set encryption key first
    export ENCRYPTION_KEY="your-key-here"  # or add to .env

    # Run migration
    python migrate_encrypt_secrets.py

    # Or with docker-compose
    docker compose exec backend python migrate_encrypt_secrets.py
"""

import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.encryption import encrypt_value, is_encrypted
from app.models.app_settings import AppSettings


def expand_column_sizes(db):
    """Expand column sizes to accommodate encrypted data."""
    print("Expanding column sizes for encrypted data...")

    # Check if we're using PostgreSQL or SQLite
    result = db.execute(text("SELECT version()")).scalar_one_or_none()
    is_postgres = result and "PostgreSQL" in result

    if is_postgres:
        # PostgreSQL syntax
        db.execute(
            text(
                """
            ALTER TABLE app_settings
            ALTER COLUMN database_password TYPE VARCHAR(500),
            ALTER COLUMN plaid_sandbox_secret TYPE VARCHAR(500),
            ALTER COLUMN plaid_production_secret TYPE VARCHAR(500)
        """
            )
        )
    else:
        # SQLite doesn't support ALTER COLUMN TYPE
        # We'll handle this by creating new columns and migrating data
        print("  SQLite detected - columns will be recreated if needed")
        # For SQLite, the model update will handle this on next table creation

    db.commit()
    print("  ✓ Column sizes expanded")


def encrypt_existing_secrets(db):
    """Encrypt any existing plaintext secrets."""
    print("\nEncrypting existing secrets...")

    settings = db.query(AppSettings).first()
    if not settings:
        print("  ⚠️  No settings found in database")
        return

    encrypted_count = 0

    # Check and encrypt database_password
    if settings._database_password and not is_encrypted(settings._database_password):
        print("  Encrypting database_password...")
        plaintext = settings._database_password
        settings._database_password = encrypt_value(plaintext)
        encrypted_count += 1

    # Check and encrypt plaid_sandbox_secret
    if settings._plaid_sandbox_secret and not is_encrypted(settings._plaid_sandbox_secret):
        print("  Encrypting plaid_sandbox_secret...")
        plaintext = settings._plaid_sandbox_secret
        settings._plaid_sandbox_secret = encrypt_value(plaintext)
        encrypted_count += 1

    # Check and encrypt plaid_production_secret
    if settings._plaid_production_secret and not is_encrypted(settings._plaid_production_secret):
        print("  Encrypting plaid_production_secret...")
        plaintext = settings._plaid_production_secret
        settings._plaid_production_secret = encrypt_value(plaintext)
        encrypted_count += 1

    if encrypted_count > 0:
        db.commit()
        print(f"  ✓ Encrypted {encrypted_count} secret(s)")
    else:
        print("  ✓ All secrets already encrypted or empty")


def validate_encryption(db):
    """Validate that encryption/decryption works correctly."""
    print("\nValidating encryption...")

    settings = db.query(AppSettings).first()
    if not settings:
        print("  ⚠️  No settings to validate")
        return

    # Test by accessing hybrid properties (which decrypt automatically)
    try:
        # These should decrypt without errors
        _ = settings.database_password
        _ = settings.plaid_sandbox_secret
        _ = settings.plaid_production_secret
        print("  ✓ Encryption/decryption validated successfully")
    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        raise


def main():
    """Run the encryption migration."""
    print("=" * 60)
    print("Secrets Encryption Migration")
    print("=" * 60)

    # Check for encryption key
    import os

    if not os.getenv("ENCRYPTION_KEY"):
        print("\n❌ ERROR: ENCRYPTION_KEY environment variable not set")
        print("\nGenerate a key with:")
        print(
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
        print("\nThen set it:")
        print("  export ENCRYPTION_KEY='your-key-here'")
        print("  # or add to .env file")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Step 1: Expand column sizes
        expand_column_sizes(db)

        # Step 2: Encrypt existing secrets
        encrypt_existing_secrets(db)

        # Step 3: Validate encryption works
        validate_encryption(db)

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nIMPORTANT:")
        print("- Keep your ENCRYPTION_KEY secure and backed up")
        print("- Add ENCRYPTION_KEY to your .env file for production")
        print("- Never commit the encryption key to version control")
        print("- If you lose the key, encrypted data cannot be recovered")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
