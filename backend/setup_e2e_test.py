#!/usr/bin/env python3
"""
Setup script for E2E testing with clean state.

This script:
1. Backs up existing database
2. Creates a fresh database
3. Sets up test beancount files
4. Initializes default categories
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.category import Category  # noqa: E402


def backup_existing_data():
    """Backup existing database and beancount files."""
    print("\n📦 Backing up existing data...")

    # Backup database
    db_path = Path("data/mintbean.db")
    if db_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"data/backups/mintbean_backup_{timestamp}.db")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, backup_path)
        print(f"   ✓ Database backed up to: {backup_path}")

    # Backup beancount files
    beancount_path = Path("data/test_ledger.beancount")
    if beancount_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"data/backups/test_ledger_backup_{timestamp}.beancount")
        shutil.copy2(beancount_path, backup_path)
        print(f"   ✓ Beancount file backed up to: {backup_path}")


def create_fresh_database():
    """Create a fresh database with schema."""
    print("\n🗄️  Creating fresh database...")

    db_path = Path("data/mintbean.db")

    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print("   ✓ Removed old database")

    # Create new database
    Base.metadata.create_all(bind=engine)
    print("   ✓ Created new database with schema")


def create_default_categories(db: Session):
    """Create default expense and income categories."""
    print("\n📁 Creating default categories...")

    categories = [
        # Expense categories
        {
            "name": "groceries",
            "display_name": "Groceries",
            "beancount_account": "Expenses:Food:Groceries",
            "category_type": "expense",
            "icon": "🛒",
            "color": "#4CAF50",
        },
        {
            "name": "restaurants",
            "display_name": "Restaurants",
            "beancount_account": "Expenses:Food:Restaurants",
            "category_type": "expense",
            "icon": "🍽️",
            "color": "#FF9800",
        },
        {
            "name": "transportation",
            "display_name": "Transportation",
            "beancount_account": "Expenses:Transportation",
            "category_type": "expense",
            "icon": "🚗",
            "color": "#2196F3",
        },
        {
            "name": "utilities",
            "display_name": "Utilities",
            "beancount_account": "Expenses:Utilities",
            "category_type": "expense",
            "icon": "💡",
            "color": "#FFC107",
        },
        {
            "name": "entertainment",
            "display_name": "Entertainment",
            "beancount_account": "Expenses:Entertainment",
            "category_type": "expense",
            "icon": "🎬",
            "color": "#E91E63",
        },
        {
            "name": "shopping",
            "display_name": "Shopping",
            "beancount_account": "Expenses:Shopping",
            "category_type": "expense",
            "icon": "🛍️",
            "color": "#9C27B0",
        },
        {
            "name": "healthcare",
            "display_name": "Healthcare",
            "beancount_account": "Expenses:Healthcare",
            "category_type": "expense",
            "icon": "🏥",
            "color": "#F44336",
        },
        # Income categories
        {
            "name": "salary",
            "display_name": "Salary",
            "beancount_account": "Income:Salary",
            "category_type": "income",
            "icon": "💰",
            "color": "#4CAF50",
        },
        {
            "name": "investment",
            "display_name": "Investment Income",
            "beancount_account": "Income:Investment",
            "category_type": "income",
            "icon": "📈",
            "color": "#00BCD4",
        },
    ]

    for cat_data in categories:
        category = Category(**cat_data)
        db.add(category)

    db.commit()
    print(f"   ✓ Created {len(categories)} default categories")


def setup_beancount_files():
    """Create initial beancount file structure."""
    print("\n📝 Setting up beancount files...")

    beancount_dir = Path("data")
    beancount_dir.mkdir(parents=True, exist_ok=True)

    # Create main ledger file
    ledger_path = beancount_dir / "test_ledger.beancount"
    ledger_content = f"""; MintBean Test Ledger
; Created: {datetime.now().strftime('%Y-%m-%d')}

option "title" "MintBean Test Ledger"
option "operating_currency" "USD"

; Opening balances
{datetime.now().strftime('%Y-%m-%d')} open Assets:Checking:Test USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Food:Groceries USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Food:Restaurants USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Transportation USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Utilities USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Entertainment USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Shopping USD
{datetime.now().strftime('%Y-%m-%d')} open Expenses:Healthcare USD
{datetime.now().strftime('%Y-%m-%d')} open Income:Salary USD
{datetime.now().strftime('%Y-%m-%d')} open Income:Investment USD

; Transactions will be synced here by MintBean
"""

    with open(ledger_path, "w") as f:
        f.write(ledger_content)

    print(f"   ✓ Created beancount ledger: {ledger_path}")


def create_env_template():
    """Create .env template if it doesn't exist."""
    print("\n⚙️  Checking environment configuration...")

    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if not env_path.exists():
        env_content = """# Database
DATABASE_URL=sqlite:///./data/mintbean.db

# Beancount
BEANCOUNT_FILE_PATH=./data/test_ledger.beancount
BEANCOUNT_REPO_PATH=./data

# Plaid (Sandbox)
# Get credentials from https://dashboard.plaid.com/
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_sandbox_secret_here
PLAID_ENV=sandbox

# API Settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
"""
        with open(env_path, "w") as f:
            f.write(env_content)
        print(f"   ✓ Created .env file: {env_path}")
        print("   ⚠️  Please update PLAID_CLIENT_ID and PLAID_SECRET in .env")

        # Also create example
        with open(env_example_path, "w") as f:
            f.write(env_content)
        print("   ✓ Created .env.example")
    else:
        print("   ✓ .env file already exists")


def main():
    """Run the setup process."""
    print("=" * 60)
    print("MintBean E2E Testing Setup")
    print("=" * 60)

    try:
        # Create necessary directories
        Path("data").mkdir(exist_ok=True)
        Path("data/backups").mkdir(exist_ok=True)

        # Backup existing data
        backup_existing_data()

        # Create fresh database
        create_fresh_database()

        # Create default categories
        db = SessionLocal()
        try:
            create_default_categories(db)
        finally:
            db.close()

        # Setup beancount files
        setup_beancount_files()

        # Create env template
        create_env_template()

        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("   1. Update .env with your Plaid sandbox credentials")
        print("      Get them from: https://dashboard.plaid.com/")
        print("   2. Start the backend: uvicorn app.main:app --reload")
        print("   3. Start the frontend: npm run dev")
        print("   4. Visit http://localhost:5173")
        print("   5. Go to Accounts page and click 'Connect Bank Account'")
        print("   6. Use Plaid sandbox credentials:")
        print("      Username: user_good")
        print("      Password: pass_good")
        print("   7. After connecting, sync transactions")
        print("   8. Review and categorize transactions")
        print("   9. Sync to beancount file\n")

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
