#!/usr/bin/env python3
"""
Script to create an admin user.

This script creates an admin user in the database.
Use this to create the first admin user after running the migration.
"""

import getpass
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session  # noqa: E402

from app.core.auth import get_password_hash  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.user import User  # noqa: E402


def create_admin():
    """Create an admin user."""
    print("=" * 60)
    print("Create Admin User")
    print("=" * 60)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Get user input
    print("\nEnter admin user details:")
    email = input("Email: ").strip()

    if not email:
        print("❌ Email cannot be empty")
        sys.exit(1)

    # Get password with confirmation
    while True:
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if not password:
            print("❌ Password cannot be empty")
            continue

        if password != password_confirm:
            print("❌ Passwords do not match. Please try again.")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            continue

        break

    # Create user
    db: Session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\n❌ User with email {email} already exists")
            sys.exit(1)

        # Create new admin user
        hashed_password = get_password_hash(password)
        now = datetime.now(UTC)

        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("\n" + "=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print(f"\nUser ID: {admin_user.id}")
        print(f"Email: {admin_user.email}")
        print(f"Admin: {admin_user.is_admin}")
        print(f"Active: {admin_user.is_active}")
        print("\nYou can now log in with these credentials.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to create admin user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
