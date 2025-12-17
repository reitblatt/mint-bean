#!/usr/bin/env python3
"""
Migration script to consolidate Plaid client_id fields.

This script consolidates the separate sandbox and production client_id fields
into a single plaid_client_id field, since the client_id is the same across
all environments.

Changes:
- Keeps/uses plaid_client_id column (already exists)
- Migrates data from plaid_sandbox_client_id or plaid_production_client_id to plaid_client_id
- Removes plaid_sandbox_client_id and plaid_production_client_id columns
- Keeps plaid_sandbox_secret and plaid_production_secret (these differ by environment)
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
    print("Migration: Consolidate Plaid Client ID")
    print("=" * 70)

    db = SessionLocal()

    try:
        print("\n1. Checking existing data...")

        with engine.connect() as conn:
            # Get existing settings
            result = conn.execute(
                text(
                    "SELECT plaid_client_id, plaid_sandbox_client_id, plaid_production_client_id FROM app_settings"
                )
            ).fetchone()

            if result:
                current_client_id, sandbox_client_id, production_client_id = result

                # Determine which client_id to use (prefer existing plaid_client_id, then sandbox, then production)
                final_client_id = current_client_id or sandbox_client_id or production_client_id

                if final_client_id:
                    print(
                        f"   Found client_id: {final_client_id[:20]}..."
                        if len(final_client_id) > 20
                        else f"   Found client_id: {final_client_id}"
                    )

                    # Update plaid_client_id if needed
                    if current_client_id != final_client_id:
                        conn.execute(
                            text(
                                "UPDATE app_settings SET plaid_client_id = :client_id WHERE id = 1"
                            ),
                            {"client_id": final_client_id},
                        )
                        print("   ✓ Updated plaid_client_id")
                        conn.commit()
                else:
                    print("   • No client_id found in any field")
            else:
                print("   • No app_settings record found")

        print("\n2. Removing redundant client_id columns...")

        with engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(text("PRAGMA table_info(app_settings)")).fetchall()
            existing_columns = {row[1] for row in result}

            # SQLite doesn't support DROP COLUMN directly, so we need to:
            # 1. Create a new table without those columns
            # 2. Copy data
            # 3. Drop old table
            # 4. Rename new table

            if (
                "plaid_sandbox_client_id" in existing_columns
                or "plaid_production_client_id" in existing_columns
            ):
                print("   Creating new table schema...")

                # Create temporary table with new schema
                conn.execute(
                    text(
                        """
                    CREATE TABLE app_settings_new (
                        id INTEGER PRIMARY KEY,
                        plaid_client_id VARCHAR(255),
                        plaid_sandbox_secret VARCHAR(255),
                        plaid_production_secret VARCHAR(255),
                        plaid_environment VARCHAR(20) NOT NULL DEFAULT 'sandbox',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        plaid_secret VARCHAR(255)
                    )
                """
                    )
                )
                print("   ✓ Created new table schema")

                # Copy data to new table
                conn.execute(
                    text(
                        """
                    INSERT INTO app_settings_new
                    (id, plaid_client_id, plaid_sandbox_secret, plaid_production_secret,
                     plaid_environment, created_at, updated_at, plaid_secret)
                    SELECT id, plaid_client_id, plaid_sandbox_secret, plaid_production_secret,
                           plaid_environment, created_at, updated_at, plaid_secret
                    FROM app_settings
                """
                    )
                )
                print("   ✓ Copied data to new table")

                # Drop old table
                conn.execute(text("DROP TABLE app_settings"))
                print("   ✓ Dropped old table")

                # Rename new table
                conn.execute(text("ALTER TABLE app_settings_new RENAME TO app_settings"))
                print("   ✓ Renamed new table")

                conn.commit()
            else:
                print("   • Redundant columns already removed")

        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        print("\nThe application now uses a single plaid_client_id for all environments.")
        print("Separate secrets are maintained for sandbox and production.")
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
