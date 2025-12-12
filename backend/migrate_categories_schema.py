"""
Migration script to update categories table schema.

Changes:
1. Rename parent_category (VARCHAR) to parent_id (INTEGER with FK)
2. Add display_order (INTEGER)
3. Add is_active (BOOLEAN)
4. Add is_system (BOOLEAN)
5. Add transaction_count (INTEGER)
6. Add last_used_at (DATETIME)
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "data" / "mintbean.db"
BACKUP_PATH = Path(__file__).parent / "data" / "mintbean_backup_pre_migration.db"


def migrate_categories_table():
    """Migrate categories table to new schema."""

    # Backup the database first
    print(f"Creating backup at {BACKUP_PATH}...")
    import shutil

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("Backup created successfully!")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")

        # Create new categories table with updated schema
        print("Creating new categories table...")
        cursor.execute(
            """
            CREATE TABLE categories_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                display_name VARCHAR(255) NOT NULL,
                parent_id INTEGER,
                beancount_account VARCHAR(255) NOT NULL,
                category_type VARCHAR(50) NOT NULL,
                icon VARCHAR(50),
                color VARCHAR(20),
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_system BOOLEAN DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                last_used_at DATETIME,
                description TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES categories_new (id)
            )
        """
        )

        # Copy data from old table to new table
        print("Copying data from old table...")
        cursor.execute(
            """
            INSERT INTO categories_new (
                id, name, display_name, parent_id, beancount_account,
                category_type, icon, color, display_order, is_active,
                is_system, transaction_count, last_used_at, description,
                created_at, updated_at
            )
            SELECT
                id,
                name,
                display_name,
                NULL as parent_id,  -- Will need manual mapping if there were parent_category strings
                beancount_account,
                category_type,
                icon,
                color,
                0 as display_order,
                1 as is_active,
                0 as is_system,
                0 as transaction_count,
                NULL as last_used_at,
                description,
                created_at,
                updated_at
            FROM categories
        """
        )

        # Count transactions for each category
        print("Calculating transaction counts...")
        cursor.execute(
            """
            UPDATE categories_new
            SET transaction_count = (
                SELECT COUNT(*)
                FROM transactions
                WHERE transactions.category_id = categories_new.id
            )
        """
        )

        # Calculate last_used_at for each category
        print("Calculating last used dates...")
        cursor.execute(
            """
            UPDATE categories_new
            SET last_used_at = (
                SELECT MAX(date)
                FROM transactions
                WHERE transactions.category_id = categories_new.id
            )
        """
        )

        # Drop old table
        print("Dropping old table...")
        cursor.execute("DROP TABLE categories")

        # Rename new table to categories
        print("Renaming new table...")
        cursor.execute("ALTER TABLE categories_new RENAME TO categories")

        # Recreate indexes
        print("Recreating indexes...")
        cursor.execute("CREATE INDEX ix_categories_id ON categories (id)")
        cursor.execute("CREATE UNIQUE INDEX ix_categories_name ON categories (name)")
        cursor.execute("CREATE INDEX ix_categories_parent_id ON categories (parent_id)")

        # Commit transaction
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"Backup saved at: {BACKUP_PATH}")

    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"Database restored from backup at: {BACKUP_PATH}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Category Table Migration")
    print("=" * 60)
    print()
    migrate_categories_table()
