"""
Migration script to fix category unique constraint.

Changes the unique constraint on categories.name from global to (user_id, name).
This allows different users to have categories with the same names.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def migrate_database(db_path: str) -> None:
    """Migrate the database to use composite unique constraint."""
    print(f"Migrating database at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Step 1: Create new table with correct schema
        print("Creating new categories table with composite unique constraint...")
        cursor.execute(
            """
            CREATE TABLE categories_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
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
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(parent_id) REFERENCES categories_new(id),
                UNIQUE(user_id, name)
            )
        """
        )

        # Step 2: Copy data from old table (assigning NULL user_id to user 1)
        print("Copying data from old table...")
        cursor.execute(
            """
            INSERT INTO categories_new (
                id, user_id, name, display_name, parent_id, beancount_account,
                category_type, icon, color, display_order, is_active, is_system,
                transaction_count, last_used_at, description, created_at, updated_at
            )
            SELECT
                id,
                COALESCE(user_id, 1) as user_id,  -- Assign NULL user_id to user 1
                name, display_name, parent_id, beancount_account,
                category_type, icon, color, display_order, is_active, is_system,
                transaction_count, last_used_at, description, created_at, updated_at
            FROM categories
        """
        )

        # Step 3: Drop old table
        print("Dropping old table...")
        cursor.execute("DROP TABLE categories")

        # Step 4: Rename new table
        print("Renaming new table...")
        cursor.execute("ALTER TABLE categories_new RENAME TO categories")

        # Step 5: Recreate indexes
        print("Recreating indexes...")
        cursor.execute("CREATE INDEX ix_categories_id ON categories(id)")
        cursor.execute("CREATE INDEX ix_categories_user_id ON categories(user_id)")
        cursor.execute("CREATE INDEX ix_categories_name ON categories(name)")
        cursor.execute("CREATE INDEX ix_categories_parent_id ON categories(parent_id)")

        # Commit transaction
        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Default database path
    db_path = str(backend_dir / "mint_bean.db")

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print("=" * 60)
    print("Category Unique Constraint Migration")
    print("=" * 60)
    print()

    # Confirm before proceeding
    response = input(f"This will modify the database at {db_path}. Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Migration cancelled.")
        sys.exit(0)

    migrate_database(db_path)
