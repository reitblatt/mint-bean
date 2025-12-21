"""Migration script to add database configuration fields to app_settings table.

This script adds new columns to the app_settings table for MySQL support:
- database_type (sqlite or mysql)
- database_host (MySQL only)
- database_port (MySQL only)
- database_name (MySQL only)
- database_user (MySQL only)
- database_password (MySQL only)
- sqlite_path (SQLite only)
"""

import sqlite3
from pathlib import Path

# Get database path
db_path = Path(__file__).parent / "data" / "mintbean.db"

if not db_path.exists():
    print(f"Database not found at {db_path}")
    print("Skipping migration - database will be created with new schema")
    exit(0)

print(f"Running migration on {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if app_settings table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'")
    if not cursor.fetchone():
        print("✗ app_settings table does not exist. Run migrate_add_environment.py first.")
        exit(1)

    # Check which columns exist
    cursor.execute("PRAGMA table_info(app_settings)")
    existing_columns = {column[1] for column in cursor.fetchall()}

    # Add database_type if it doesn't exist
    if "database_type" not in existing_columns:
        print("Adding database_type column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN database_type VARCHAR(20) NOT NULL DEFAULT 'sqlite'
        """
        )
        print("✓ database_type column added")
    else:
        print("✓ database_type column already exists")

    # Add database_host if it doesn't exist
    if "database_host" not in existing_columns:
        print("Adding database_host column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN database_host VARCHAR(255)
        """
        )
        print("✓ database_host column added")
    else:
        print("✓ database_host column already exists")

    # Add database_port if it doesn't exist
    if "database_port" not in existing_columns:
        print("Adding database_port column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN database_port INTEGER DEFAULT 3306
        """
        )
        print("✓ database_port column added")
    else:
        print("✓ database_port column already exists")

    # Add database_name if it doesn't exist
    if "database_name" not in existing_columns:
        print("Adding database_name column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN database_name VARCHAR(255)
        """
        )
        print("✓ database_name column added")
    else:
        print("✓ database_name column already exists")

    # Add database_user if it doesn't exist
    if "database_user" not in existing_columns:
        print("Adding database_user column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN database_user VARCHAR(255)
        """
        )
        print("✓ database_user column added")
    else:
        print("✓ database_user column already exists")

    # Add database_password if it doesn't exist
    if "database_password" not in existing_columns:
        print("Adding database_password column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN database_password VARCHAR(255)
        """
        )
        print("✓ database_password column added")
    else:
        print("✓ database_password column already exists")

    # Add sqlite_path if it doesn't exist
    if "sqlite_path" not in existing_columns:
        print("Adding sqlite_path column to app_settings...")
        cursor.execute(
            """
            ALTER TABLE app_settings
            ADD COLUMN sqlite_path VARCHAR(500) DEFAULT './data/mintbean.db'
        """
        )
        print("✓ sqlite_path column added")
    else:
        print("✓ sqlite_path column already exists")

    # Commit changes
    conn.commit()
    print("\n✓ Migration completed successfully!")

except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    conn.rollback()
    raise

finally:
    conn.close()
