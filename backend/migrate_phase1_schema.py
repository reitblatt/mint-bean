#!/usr/bin/env python3
"""
Migration script for Phase 1 schema changes.

Adds new columns to transactions and categories tables,
and creates the plaid_category_mappings table.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "mintbean.db"


def migrate():
    """Apply Phase 1 database schema migrations."""
    print("=" * 60)
    print("Phase 1 Schema Migration")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if migrations are needed
        cursor.execute("PRAGMA table_info(transactions)")
        columns = {row[1] for row in cursor.fetchall()}

        # Migrate transactions table
        print("\n📊 Migrating transactions table...")

        if "plaid_category" not in columns:
            print("  ➕ Adding plaid_category column...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN plaid_category TEXT")

        if "plaid_primary_category" not in columns:
            print("  ➕ Adding plaid_primary_category column...")
            cursor.execute(
                "ALTER TABLE transactions ADD COLUMN plaid_primary_category VARCHAR(100)"
            )

        if "plaid_detailed_category" not in columns:
            print("  ➕ Adding plaid_detailed_category column...")
            cursor.execute(
                "ALTER TABLE transactions ADD COLUMN plaid_detailed_category VARCHAR(100)"
            )

        if "plaid_confidence_level" not in columns:
            print("  ➕ Adding plaid_confidence_level column...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN plaid_confidence_level VARCHAR(20)")

        if "merchant_name" not in columns:
            print("  ➕ Adding merchant_name column...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN merchant_name VARCHAR(255)")

        if "auto_categorized" not in columns:
            print("  ➕ Adding auto_categorized column...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN auto_categorized BOOLEAN DEFAULT 0")

        if "categorization_method" not in columns:
            print("  ➕ Adding categorization_method column...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN categorization_method VARCHAR(50)")

        # Migrate categories table
        print("\n📁 Migrating categories table...")

        cursor.execute("PRAGMA table_info(categories)")
        cat_columns = {row[1] for row in cursor.fetchall()}

        if "parent_id" not in cat_columns:
            print("  ➕ Adding parent_id column...")
            cursor.execute(
                "ALTER TABLE categories ADD COLUMN parent_id INTEGER REFERENCES categories(id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS ix_categories_parent_id ON categories (parent_id)"
            )

        if "display_order" not in cat_columns:
            print("  ➕ Adding display_order column...")
            cursor.execute("ALTER TABLE categories ADD COLUMN display_order INTEGER DEFAULT 0")

        if "is_active" not in cat_columns:
            print("  ➕ Adding is_active column...")
            cursor.execute("ALTER TABLE categories ADD COLUMN is_active BOOLEAN DEFAULT 1")

        if "is_system" not in cat_columns:
            print("  ➕ Adding is_system column...")
            cursor.execute("ALTER TABLE categories ADD COLUMN is_system BOOLEAN DEFAULT 0")

        if "transaction_count" not in cat_columns:
            print("  ➕ Adding transaction_count column...")
            cursor.execute("ALTER TABLE categories ADD COLUMN transaction_count INTEGER DEFAULT 0")

        if "last_used_at" not in cat_columns:
            print("  ➕ Adding last_used_at column...")
            cursor.execute("ALTER TABLE categories ADD COLUMN last_used_at DATETIME")

        # Create plaid_category_mappings table
        print("\n🗺️  Creating plaid_category_mappings table...")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plaid_category_mappings (
                id INTEGER PRIMARY KEY,
                plaid_primary_category VARCHAR(100) NOT NULL,
                plaid_detailed_category VARCHAR(100),
                category_id INTEGER NOT NULL,
                confidence FLOAT DEFAULT 1.0,
                auto_apply BOOLEAN DEFAULT 1,
                match_count INTEGER DEFAULT 0,
                last_matched_at DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                UNIQUE (plaid_primary_category, plaid_detailed_category)
            )
        """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_plaid_category_mappings_primary ON plaid_category_mappings (plaid_primary_category)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_plaid_category_mappings_detailed ON plaid_category_mappings (plaid_detailed_category)"
        )

        # Commit all changes
        conn.commit()

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\n📋 Summary:")
        print("  • transactions table: 7 new columns")
        print("  • categories table: 6 new columns")
        print("  • plaid_category_mappings table: created")
        print("\n")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
