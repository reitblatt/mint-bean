#!/usr/bin/env python3
"""Migration script to add dashboard_tabs and dashboard_widgets tables.

This script creates the necessary tables for the custom dashboard feature:
- dashboard_tabs: User-created dashboard tabs
- dashboard_widgets: Configurable widgets within tabs
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
    # Check if dashboard_tabs table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_tabs'")
    if not cursor.fetchone():
        print("Creating dashboard_tabs table...")
        cursor.execute(
            """
            CREATE TABLE dashboard_tabs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 0,
                is_default BOOLEAN NOT NULL DEFAULT 0,
                icon VARCHAR(50),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )
        # Create indexes
        cursor.execute("CREATE INDEX ix_dashboard_tabs_id ON dashboard_tabs (id)")
        cursor.execute("CREATE INDEX ix_dashboard_tabs_user_id ON dashboard_tabs (user_id)")
        print("✓ dashboard_tabs table created")
    else:
        print("✓ dashboard_tabs table already exists")

    # Check if dashboard_widgets table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_widgets'")
    if not cursor.fetchone():
        print("Creating dashboard_widgets table...")
        cursor.execute(
            """
            CREATE TABLE dashboard_widgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tab_id INTEGER NOT NULL,
                widget_type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                grid_row INTEGER NOT NULL DEFAULT 1,
                grid_col INTEGER NOT NULL DEFAULT 1,
                grid_width INTEGER NOT NULL DEFAULT 1,
                grid_height INTEGER NOT NULL DEFAULT 1,
                config TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (tab_id) REFERENCES dashboard_tabs (id)
            )
        """
        )
        # Create indexes
        cursor.execute("CREATE INDEX ix_dashboard_widgets_id ON dashboard_widgets (id)")
        cursor.execute("CREATE INDEX ix_dashboard_widgets_tab_id ON dashboard_widgets (tab_id)")
        cursor.execute(
            "CREATE INDEX ix_dashboard_widgets_widget_type ON dashboard_widgets (widget_type)"
        )
        print("✓ dashboard_widgets table created")
    else:
        print("✓ dashboard_widgets table already exists")

    # Commit changes
    conn.commit()
    print("\n✓ Migration completed successfully!")

except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    conn.rollback()
    raise

finally:
    conn.close()
