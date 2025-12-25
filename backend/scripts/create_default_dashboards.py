#!/usr/bin/env python3
"""Script to create default dashboards for existing users who don't have one.

This script should be run once after deploying the dashboard feature
to ensure all existing users get a default dashboard.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# ruff: noqa: E402
from app.core.database import SessionLocal
from app.models.dashboard_tab import DashboardTab
from app.models.user import User
from app.services.dashboard_service import create_default_dashboard


def main():
    """Create default dashboards for users without any dashboards."""
    db = SessionLocal()

    try:
        # Get all users
        users = db.query(User).filter(User.is_active).all()
        print(f"Found {len(users)} active users")

        created_count = 0
        skipped_count = 0

        for user in users:
            # Check if user already has dashboards
            existing_tabs = db.query(DashboardTab).filter(DashboardTab.user_id == user.id).count()

            if existing_tabs > 0:
                print(f"✓ User {user.email} already has {existing_tabs} dashboard(s), skipping")
                skipped_count += 1
                continue

            # Create default dashboard
            print(f"Creating default dashboard for user {user.email}...")
            create_default_dashboard(db, user)
            created_count += 1
            print(f"✓ Default dashboard created for {user.email}")

        print("\n✓ Script completed!")
        print(f"  Created: {created_count} default dashboards")
        print(f"  Skipped: {skipped_count} users (already have dashboards)")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
