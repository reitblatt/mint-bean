#!/usr/bin/env python3
"""
Enable Row-Level Security (RLS) on PostgreSQL.

This script enables PostgreSQL Row-Level Security policies to enforce
data isolation at the database level. This provides defense-in-depth
protection against data leakage bugs in application code.

IMPORTANT: This script only works with PostgreSQL. It will error if run
against SQLite or other databases.

Usage:
    python migrate_enable_rls.py

The script will:
1. Check that you're using PostgreSQL
2. Enable RLS on all user-scoped tables
3. Create RLS policies for user isolation
4. Create RLS policies for environment isolation
5. Test that RLS is working correctly
"""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))  # noqa: E402

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402


def check_postgresql():
    """Verify that we're using PostgreSQL."""
    print("\n=== Checking Database Type ===")
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT version()")).scalar()
        if "PostgreSQL" not in result:
            print(f"❌ ERROR: This script requires PostgreSQL, but you're using: {result}")
            print("\nPlease migrate to PostgreSQL first. See POSTGRESQL_MIGRATION.md")
            return False
        print(f"✅ PostgreSQL detected: {result.split(',')[0]}")
        return True
    except Exception as e:
        print(f"❌ ERROR: Could not check database version: {e}")
        return False
    finally:
        db.close()


def enable_rls_on_table(db, table_name: str):
    """Enable RLS on a specific table."""
    try:
        db.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
        print(f"  ✅ Enabled RLS on {table_name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to enable RLS on {table_name}: {e}")
        return False


def create_user_isolation_policy(db, table_name: str):
    """Create RLS policy for user isolation."""
    policy_name = f"{table_name}_user_isolation"

    try:
        # Drop existing policy if it exists
        db.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name}"))

        # Create policy that filters by user_id
        sql = text(
            f"""
            CREATE POLICY {policy_name} ON {table_name}
            USING (user_id = current_setting('app.current_user_id', true)::integer)
        """
        )
        db.execute(sql)
        db.commit()
        print(f"  ✅ Created user isolation policy on {table_name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create user isolation policy on {table_name}: {e}")
        db.rollback()
        return False


def create_environment_isolation_policy(db, table_name: str):
    """Create RLS policy for environment isolation (sandbox vs production)."""
    policy_name = f"{table_name}_environment_isolation"

    # Only create for tables that have an environment column
    tables_with_environment = ["transactions", "accounts", "plaid_items"]

    if table_name not in tables_with_environment:
        return True  # Skip tables without environment column

    try:
        # Drop existing policy if it exists
        db.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name}"))

        # Create policy that filters by environment
        sql = text(
            f"""
            CREATE POLICY {policy_name} ON {table_name}
            USING (
                environment = current_setting('app.current_environment', true)
                OR current_setting('app.current_environment', true) IS NULL
            )
        """
        )
        db.execute(sql)
        db.commit()
        print(f"  ✅ Created environment isolation policy on {table_name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create environment isolation policy on {table_name}: {e}")
        db.rollback()
        return False


def test_rls(db):
    """Test that RLS is working correctly."""
    print("\n=== Testing RLS ===")

    try:
        # Test 1: Without user context, should return no rows
        result = db.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        if result == 0:
            print("  ✅ RLS blocks queries without user context")
        else:
            print(f"  ⚠️  WARNING: Found {result} rows without user context (expected 0)")

        # Test 2: With user context, should return rows for that user
        # Note: This test will fail if there's no user with id=1 or no transactions
        db.execute(text("SET LOCAL app.current_user_id = '1'"))
        result = db.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        print(f"  ✅ With user context: found {result} rows for user 1")

        # Reset session
        db.rollback()

        return True
    except Exception as e:
        print(f"  ❌ RLS test failed: {e}")
        db.rollback()
        return False


def main():
    """Main migration function."""
    print("=" * 60)
    print("PostgreSQL Row-Level Security (RLS) Migration")
    print("=" * 60)

    # Step 1: Check that we're using PostgreSQL
    if not check_postgresql():
        sys.exit(1)

    # Step 2: Enable RLS on all user-scoped tables
    print("\n=== Enabling RLS on Tables ===")

    tables = [
        "accounts",
        "transactions",
        "categories",
        "dashboard_tabs",
        "dashboard_widgets",
        "plaid_items",
        "plaid_category_mappings",
        "rules",
    ]

    db = SessionLocal()
    try:
        success_count = 0
        for table in tables:
            if enable_rls_on_table(db, table):
                success_count += 1

        db.commit()
        print(f"\n✅ Enabled RLS on {success_count}/{len(tables)} tables")

        # Step 3: Create user isolation policies
        print("\n=== Creating User Isolation Policies ===")
        success_count = 0
        for table in tables:
            if create_user_isolation_policy(db, table):
                success_count += 1

        print(f"\n✅ Created user isolation policies on {success_count}/{len(tables)} tables")

        # Step 4: Create environment isolation policies
        print("\n=== Creating Environment Isolation Policies ===")
        success_count = 0
        for table in tables:
            if create_environment_isolation_policy(db, table):
                success_count += 1

        # Step 5: Test RLS
        test_rls(db)

        print("\n" + "=" * 60)
        print("✅ RLS Migration Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update app.core.database.get_db() to set user context")
        print("2. Run data isolation tests: pytest tests/test_data_isolation.py")
        print("3. Test the application thoroughly")
        print("\nSee SECURITY.md for more information on RLS.")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
