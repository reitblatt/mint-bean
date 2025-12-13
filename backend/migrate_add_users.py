#!/usr/bin/env python3
"""
Migration script for user authentication system.

Creates users table and adds user_id foreign keys to all existing tables.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "mintbean.db"


def migrate():
    """Apply user authentication database schema migrations."""
    print("=" * 60)
    print("User Authentication Schema Migration")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table_exists = cursor.fetchone() is not None

        # Create users table
        if not users_table_exists:
            print("\n📊 Creating users table...")
            cursor.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT 0 NOT NULL,
                    is_active BOOLEAN DEFAULT 1 NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX ix_users_id ON users (id)")
            cursor.execute("CREATE INDEX ix_users_email ON users (email)")
            print("  ✅ Users table created")
        else:
            print("\n✅ Users table already exists")

        # Add user_id to transactions table
        print("\n📊 Migrating transactions table...")
        cursor.execute("PRAGMA table_info(transactions)")
        transaction_columns = {row[1] for row in cursor.fetchall()}

        if "user_id" not in transaction_columns:
            print("  ➕ Adding user_id column...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
            cursor.execute("CREATE INDEX ix_transactions_user_id ON transactions (user_id)")
            print("  ✅ user_id column added to transactions")
        else:
            print("  ✅ user_id column already exists in transactions")

        # Add user_id to accounts table
        print("\n📊 Migrating accounts table...")
        cursor.execute("PRAGMA table_info(accounts)")
        account_columns = {row[1] for row in cursor.fetchall()}

        if "user_id" not in account_columns:
            print("  ➕ Adding user_id column...")
            cursor.execute("ALTER TABLE accounts ADD COLUMN user_id INTEGER")
            cursor.execute("CREATE INDEX ix_accounts_user_id ON accounts (user_id)")
            print("  ✅ user_id column added to accounts")
        else:
            print("  ✅ user_id column already exists in accounts")

        # Add user_id to categories table
        print("\n📊 Migrating categories table...")
        cursor.execute("PRAGMA table_info(categories)")
        category_columns = {row[1] for row in cursor.fetchall()}

        if "user_id" not in category_columns:
            print("  ➕ Adding user_id column...")
            cursor.execute("ALTER TABLE categories ADD COLUMN user_id INTEGER")
            cursor.execute("CREATE INDEX ix_categories_user_id ON categories (user_id)")
            print("  ✅ user_id column added to categories")
        else:
            print("  ✅ user_id column already exists in categories")

        # Add user_id to rules table
        print("\n📊 Migrating rules table...")
        cursor.execute("PRAGMA table_info(rules)")
        rule_columns = {row[1] for row in cursor.fetchall()}

        if "user_id" not in rule_columns:
            print("  ➕ Adding user_id column...")
            cursor.execute("ALTER TABLE rules ADD COLUMN user_id INTEGER")
            cursor.execute("CREATE INDEX ix_rules_user_id ON rules (user_id)")
            print("  ✅ user_id column added to rules")
        else:
            print("  ✅ user_id column already exists in rules")

        # Check if plaid_items table exists and add user_id if it does
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plaid_items'")
        plaid_items_exists = cursor.fetchone() is not None

        if plaid_items_exists:
            print("\n📊 Migrating plaid_items table...")
            cursor.execute("PRAGMA table_info(plaid_items)")
            plaid_item_columns = {row[1] for row in cursor.fetchall()}

            if "user_id" not in plaid_item_columns:
                print("  ➕ Adding user_id column...")
                cursor.execute("ALTER TABLE plaid_items ADD COLUMN user_id INTEGER")
                cursor.execute("CREATE INDEX ix_plaid_items_user_id ON plaid_items (user_id)")
                print("  ✅ user_id column added to plaid_items")
            else:
                print("  ✅ user_id column already exists in plaid_items")

        # Check if plaid_category_mappings table exists and add user_id if it does
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='plaid_category_mappings'"
        )
        plaid_mappings_exists = cursor.fetchone() is not None

        if plaid_mappings_exists:
            print("\n📊 Migrating plaid_category_mappings table...")
            cursor.execute("PRAGMA table_info(plaid_category_mappings)")
            mapping_columns = {row[1] for row in cursor.fetchall()}

            if "user_id" not in mapping_columns:
                print("  ➕ Adding user_id column...")
                cursor.execute("ALTER TABLE plaid_category_mappings ADD COLUMN user_id INTEGER")
                cursor.execute(
                    "CREATE INDEX ix_plaid_category_mappings_user_id ON plaid_category_mappings (user_id)"
                )
                print("  ✅ user_id column added to plaid_category_mappings")
            else:
                print("  ✅ user_id column already exists in plaid_category_mappings")

        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run create_admin_user.py to create your first admin user")
        print("2. Restart the backend server")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
