#!/usr/bin/env python3
"""
Migration script to add environment-specific Plaid credentials.

This script migrates from the old single-credential model to the new
environment-specific credential model where we store separate credentials
for sandbox and production environments.

Changes:
- Adds plaid_sandbox_client_id and plaid_sandbox_secret columns
- Adds plaid_production_client_id and plaid_production_secret columns
- Migrates existing plaid_client_id and plaid_secret to the appropriate environment fields
- Removes old plaid_client_id and plaid_secret columns (kept for backward compatibility during transition)
"""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402


def migrate():
    """Run the migration."""
    print("=" * 70)
    print("Migration: Add Environment-Specific Plaid Credentials")
    print("=" * 70)

    db = SessionLocal()

    try:
        print("\n1. Adding new credential columns...")

        # Add new columns for environment-specific credentials
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("PRAGMA table_info(app_settings)")).fetchall()
            existing_columns = {row[1] for row in result}

            if "plaid_sandbox_client_id" not in existing_columns:
                conn.execute(
                    text("ALTER TABLE app_settings ADD COLUMN plaid_sandbox_client_id VARCHAR(255)")
                )
                print("   ✓ Added plaid_sandbox_client_id column")
            else:
                print("   • plaid_sandbox_client_id column already exists")

            if "plaid_sandbox_secret" not in existing_columns:
                conn.execute(
                    text("ALTER TABLE app_settings ADD COLUMN plaid_sandbox_secret VARCHAR(255)")
                )
                print("   ✓ Added plaid_sandbox_secret column")
            else:
                print("   • plaid_sandbox_secret column already exists")

            if "plaid_production_client_id" not in existing_columns:
                conn.execute(
                    text(
                        "ALTER TABLE app_settings ADD COLUMN plaid_production_client_id VARCHAR(255)"
                    )
                )
                print("   ✓ Added plaid_production_client_id column")
            else:
                print("   • plaid_production_client_id column already exists")

            if "plaid_production_secret" not in existing_columns:
                conn.execute(
                    text("ALTER TABLE app_settings ADD COLUMN plaid_production_secret VARCHAR(255)")
                )
                print("   ✓ Added plaid_production_secret column")
            else:
                print("   • plaid_production_secret column already exists")

            conn.commit()

        print("\n2. Migrating existing credentials...")

        # Migrate existing credentials to the appropriate environment
        with engine.connect() as conn:
            # Get existing settings
            result = conn.execute(
                text(
                    "SELECT id, plaid_client_id, plaid_secret, plaid_environment FROM app_settings"
                )
            ).fetchone()

            if result:
                settings_id, client_id, secret, environment = result

                if client_id or secret:
                    # Migrate to the appropriate environment
                    if environment == "production":
                        conn.execute(
                            text(
                                "UPDATE app_settings SET "
                                "plaid_production_client_id = :client_id, "
                                "plaid_production_secret = :secret "
                                "WHERE id = :id"
                            ),
                            {"client_id": client_id, "secret": secret, "id": settings_id},
                        )
                        print("   ✓ Migrated credentials to production environment")
                    else:  # sandbox or any other value defaults to sandbox
                        conn.execute(
                            text(
                                "UPDATE app_settings SET "
                                "plaid_sandbox_client_id = :client_id, "
                                "plaid_sandbox_secret = :secret "
                                "WHERE id = :id"
                            ),
                            {"client_id": client_id, "secret": secret, "id": settings_id},
                        )
                        print("   ✓ Migrated credentials to sandbox environment")

                    conn.commit()
                else:
                    print("   • No existing credentials to migrate")
            else:
                print("   • No app_settings record found")

        print("\n3. Checking for old credential columns...")
        # Note: We keep old columns for now to maintain backward compatibility
        # They can be removed in a future migration after confirming everything works
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(app_settings)")).fetchall()
            existing_columns = {row[1] for row in result}

            if "plaid_client_id" in existing_columns:
                print(
                    "   • Old plaid_client_id column still exists (kept for backward compatibility)"
                )
            if "plaid_secret" in existing_columns:
                print("   • Old plaid_secret column still exists (kept for backward compatibility)")

        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        print("\nThe application now supports environment-specific Plaid credentials.")
        print("You can set different credentials for sandbox and production environments.")
        print("\nNote: Old credential columns are kept for backward compatibility.")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
