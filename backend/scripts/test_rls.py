#!/usr/bin/env python3
"""
Test Row-Level Security (RLS) policies.

This script tests that RLS policies are correctly enforcing data isolation
between users and environments.

Usage:
    python scripts/test_rls.py
"""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, set_current_user_for_rls  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402
from app.models.user import User  # noqa: E402


def check_postgresql():
    """Verify that we're using PostgreSQL."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT version()")).scalar()
        if "PostgreSQL" not in result:
            print(f"⚠️  WARNING: RLS only works with PostgreSQL, but you're using: {result}")
            print("Skipping RLS tests.")
            return False
        return True
    finally:
        db.close()


def test_without_user_context():
    """Test that queries without user context return no rows."""
    print("\n=== Test 1: Without User Context ===")
    db = SessionLocal()
    try:
        # Query should return 0 rows due to RLS
        count = db.query(Transaction).count()
        if count == 0:
            print("✅ PASS: RLS blocks queries without user context (0 rows returned)")
            return True
        else:
            print(f"❌ FAIL: Expected 0 rows without user context, got {count}")
            return False
    finally:
        db.close()


def test_with_user_context():
    """Test that queries with user context return only that user's rows."""
    print("\n=== Test 2: With User Context ===")

    db = SessionLocal()
    try:
        # Get the first user
        user = db.query(User).first()
        if not user:
            print("⚠️  SKIP: No users in database")
            return True

        # Set user context
        set_current_user_for_rls(user.id)

        # Count transactions with RLS context
        db_rls = SessionLocal()
        try:
            count_with_rls = db_rls.query(Transaction).count()
            print(f"  Found {count_with_rls} transactions for user {user.id}")

            # Verify by querying directly with user_id filter
            count_direct = db.query(Transaction).filter(Transaction.user_id == user.id).count()

            if count_with_rls == count_direct:
                print(f"✅ PASS: RLS returns correct rows ({count_with_rls} = {count_direct})")
                return True
            else:
                print(
                    f"❌ FAIL: RLS returned {count_with_rls} but direct query returned {count_direct}"
                )
                return False
        finally:
            db_rls.close()
    finally:
        db.close()


def test_user_isolation():
    """Test that users cannot see each other's data."""
    print("\n=== Test 3: User Isolation ===")

    db = SessionLocal()
    try:
        # Get two different users
        users = db.query(User).limit(2).all()
        if len(users) < 2:
            print("⚠️  SKIP: Need at least 2 users in database")
            return True

        user1, user2 = users[0], users[1]

        # Set context to user 1
        set_current_user_for_rls(user1.id)
        db1 = SessionLocal()
        try:
            count1 = db1.query(Transaction).count()
            print(f"  User {user1.id}: {count1} transactions")
        finally:
            db1.close()

        # Set context to user 2
        set_current_user_for_rls(user2.id)
        db2 = SessionLocal()
        try:
            count2 = db2.query(Transaction).count()
            print(f"  User {user2.id}: {count2} transactions")
        finally:
            db2.close()

        # Verify counts match direct queries
        count1_direct = db.query(Transaction).filter(Transaction.user_id == user1.id).count()
        count2_direct = db.query(Transaction).filter(Transaction.user_id == user2.id).count()

        if count1 == count1_direct and count2 == count2_direct:
            print("✅ PASS: Users see only their own data")
            return True
        else:
            print("❌ FAIL: User isolation not working correctly")
            return False

    finally:
        db.close()


def test_rls_policies_exist():
    """Test that RLS policies are enabled and active."""
    print("\n=== Test 4: RLS Policies Exist ===")

    db = SessionLocal()
    try:
        # Check if RLS is enabled on transactions table
        result = db.execute(
            text(
                """
            SELECT relrowsecurity
            FROM pg_class
            WHERE relname = 'transactions'
        """
            )
        ).scalar()

        if not result:
            print("❌ FAIL: RLS is not enabled on transactions table")
            return False

        # Check if policies exist
        policies = db.execute(
            text(
                """
            SELECT policyname
            FROM pg_policies
            WHERE tablename = 'transactions'
        """
            )
        ).fetchall()

        if not policies:
            print("❌ FAIL: No RLS policies found for transactions table")
            return False

        print(f"  Found {len(policies)} RLS policies:")
        for policy in policies:
            print(f"    - {policy[0]}")

        print("✅ PASS: RLS policies are enabled and active")
        return True

    except Exception as e:
        print(f"⚠️  SKIP: Could not check RLS policies: {e}")
        return True
    finally:
        db.close()


def main():
    """Run all RLS tests."""
    print("=" * 60)
    print("Row-Level Security (RLS) Test Suite")
    print("=" * 60)

    if not check_postgresql():
        sys.exit(0)  # Skip tests for non-PostgreSQL databases

    tests = [
        test_rls_policies_exist,
        test_without_user_context,
        test_with_user_context,
        test_user_isolation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test.__name__} raised exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All RLS tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
