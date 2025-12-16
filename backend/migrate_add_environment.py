"""Migration script to add environment fields to existing tables.

This script:
1. Adds the app_settings table
2. Adds environment column to plaid_items table
3. Adds environment column to accounts table
4. Adds environment column to transactions table
5. Sets default environment to 'sandbox' for all existing records
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
        print("Creating app_settings table...")
        cursor.execute(
            """
            CREATE TABLE app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plaid_client_id VARCHAR(255),
                plaid_secret VARCHAR(255),
                plaid_environment VARCHAR(20) NOT NULL DEFAULT 'sandbox',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """
        )
        print("✓ app_settings table created")
    else:
        print("✓ app_settings table already exists")

    # Check if environment column exists in plaid_items
    cursor.execute("PRAGMA table_info(plaid_items)")
    plaid_items_columns = [column[1] for column in cursor.fetchall()]

    if "environment" not in plaid_items_columns:
        print("Adding environment column to plaid_items...")
        cursor.execute(
            """
            ALTER TABLE plaid_items
            ADD COLUMN environment VARCHAR(20) NOT NULL DEFAULT 'sandbox'
        """
        )
        # Create index
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_plaid_items_environment ON plaid_items (environment)"
        )
        print("✓ environment column added to plaid_items")
    else:
        print("✓ environment column already exists in plaid_items")

    # Check if environment column exists in accounts
    cursor.execute("PRAGMA table_info(accounts)")
    accounts_columns = [column[1] for column in cursor.fetchall()]

    if "environment" not in accounts_columns:
        print("Adding environment column to accounts...")
        cursor.execute(
            """
            ALTER TABLE accounts
            ADD COLUMN environment VARCHAR(20) NOT NULL DEFAULT 'sandbox'
        """
        )
        # Create index
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_accounts_environment ON accounts (environment)"
        )
        print("✓ environment column added to accounts")
    else:
        print("✓ environment column already exists in accounts")

    # Check if environment column exists in transactions
    cursor.execute("PRAGMA table_info(transactions)")
    transactions_columns = [column[1] for column in cursor.fetchall()]

    if "environment" not in transactions_columns:
        print("Adding environment column to transactions...")
        cursor.execute(
            """
            ALTER TABLE transactions
            ADD COLUMN environment VARCHAR(20) NOT NULL DEFAULT 'sandbox'
        """
        )
        # Create index
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_transactions_environment ON transactions (environment)"
        )
        print("✓ environment column added to transactions")
    else:
        print("✓ environment column already exists in transactions")

    # Commit changes
    conn.commit()
    print("\n✓ Migration completed successfully!")

except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    conn.rollback()
    raise

finally:
    conn.close()
