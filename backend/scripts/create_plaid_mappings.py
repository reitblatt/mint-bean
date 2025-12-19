#!/usr/bin/env python3
"""
Create default Plaid category mappings.

This script creates mappings between Plaid's detailed categories and
beancount categories for automatic transaction categorization.
"""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.plaid_category_mapping import PlaidCategoryMapping  # noqa: E402
from app.models.user import User  # noqa: E402

# Mapping of Plaid detailed categories to beancount account names
# Format: detailed_category -> beancount_account
PLAID_CATEGORY_MAPPINGS = {
    # Auto & Transport
    "TRANSPORTATION_GAS": "Expenses:Auto-and-Transport:Gas-and-Fuel",
    "TRANSPORTATION_PARKING": "Expenses:Auto-and-Transport:Parking",
    "TRANSPORTATION_PUBLIC_TRANSIT": "Expenses:Auto-and-Transport:Public-Transportation",
    "TRANSPORTATION_TAXIS_AND_RIDE_SHARES": "Expenses:Auto-and-Transport:Ride-Share",
    "GENERAL_SERVICES_AUTOMOTIVE": "Expenses:Auto-and-Transport:Service-and-Parts",
    "TRANSPORTATION_TOLLS": "Expenses:Auto-and-Transport:Tolls",
    # Bills & Utilities
    "RENT_AND_UTILITIES_INTERNET_AND_CABLE": "Expenses:Bills-and-Utilities:Internet",
    "RENT_AND_UTILITIES_TELEPHONE": "Expenses:Bills-and-Utilities:Mobile-Phone",
    "RENT_AND_UTILITIES_WATER": "Expenses:Bills-and-Utilities:Utilities",
    "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY": "Expenses:Bills-and-Utilities:Utilities:Electricity",
    # Business Services
    "GENERAL_SERVICES_POSTAGE_AND_SHIPPING": "Expenses:Business-Services:Shipping",
    # Entertainment
    "ENTERTAINMENT_TV_AND_MOVIES": "Expenses:Entertainment:Movies-and-DVDs",
    "ENTERTAINMENT_MUSIC_AND_AUDIO": "Expenses:Entertainment:Music",
    "GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS": "Expenses:Entertainment:Newspapers-and-Magazines",
    "ENTERTAINMENT_VIDEO_GAMES": "Expenses:Entertainment:Games",
    # Fees & Charges
    "BANK_FEES_ATM_FEES": "Expenses:Fees-and-Charges:ATM-Fee",
    "BANK_FEES_OTHER_BANK_FEES": "Expenses:Fees-and-Charges:Service-Fee",
    "BANK_FEES_INTEREST_CHARGE": "Expenses:Fees-and-Charges:Credit-Card-Interest",
    # Food & Dining
    "FOOD_AND_DRINK_COFFEE": "Expenses:Food-and-Dining:Coffee-Shops",
    "FOOD_AND_DRINK_FAST_FOOD": "Expenses:Food-and-Dining:Fast-Food",
    "FOOD_AND_DRINK_GROCERIES": "Expenses:Food-and-Dining:Groceries",
    "FOOD_AND_DRINK_RESTAURANT": "Expenses:Food-and-Dining:Restaurants",
    "FOOD_AND_DRINK_BEER_WINE_AND_LIQUOR": "Expenses:Food-and-Dining:Wine-and-Spirits",
    # Gifts & Donations
    "GOVERNMENT_AND_NON_PROFIT_DONATIONS": "Expenses:Gifts-and-Donations:Charity",
    "GENERAL_MERCHANDISE_GIFTS_AND_NOVELTIES": "Expenses:Gifts-and-Donations:Gift",
    # Health & Fitness
    "MEDICAL_DENTAL_CARE": "Expenses:Health-and-Fitness:Dentist",
    "MEDICAL_PRIMARY_CARE": "Expenses:Health-and-Fitness:Doctor",
    "MEDICAL_EYE_CARE": "Expenses:Health-and-Fitness:Eyecare",
    "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS": "Expenses:Health-and-Fitness:Gym",
    "GENERAL_SERVICES_INSURANCE": "Expenses:Health-and-Fitness:Health-Insurance",
    "MEDICAL_PHARMACIES_AND_SUPPLEMENTS": "Expenses:Health-and-Fitness:Pharmacy",
    # Home
    "HOME_IMPROVEMENT_FURNITURE": "Expenses:Home:Furnishings",
    "HOME_IMPROVEMENT_HARDWARE": "Expenses:Home:Home-Improvement",
    "HOME_IMPROVEMENT_SECURITY": "Expenses:Home:Home-Services",
    "LOAN_PAYMENTS_MORTGAGE_PAYMENT": "Expenses:Home:Mortgage-Interest",
    # Personal Care
    "PERSONAL_CARE_HAIR_AND_BEAUTY": "Expenses:Personal-Care:Hair",
    # Pets
    "GENERAL_MERCHANDISE_PET_SUPPLIES": "Expenses:Pets:Pet-Food-and-Supplies",
    # Shopping
    "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES": "Expenses:Shopping",
    "GENERAL_MERCHANDISE_SUPERSTORES": "Expenses:Shopping",
    "GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES": "Expenses:Shopping:Clothing",
    "GENERAL_MERCHANDISE_ELECTRONICS": "Expenses:Shopping:Electronics-and-Software",
    "GENERAL_MERCHANDISE_OTHER_GENERAL_MERCHANDISE": "Expenses:Shopping:Hobbies",
    # Taxes
    "GOVERNMENT_AND_NON_PROFIT_TAX_PAYMENT": "Expenses:Taxes:Federal-Tax",
    # Travel
    "TRAVEL_OTHER_TRAVEL": "Expenses:Travel",
    "TRAVEL_FLIGHTS": "Expenses:Travel:Air-Travel",
    "TRAVEL_LODGING": "Expenses:Travel:Hotel",
    "TRAVEL_RENTAL_CARS": "Expenses:Travel:Rental-Car-and-Taxi",
}


def extract_primary_category(detailed_category: str) -> str:
    """Extract primary category from detailed category."""
    # Primary category is the first part before underscore
    parts = detailed_category.split("_")
    if len(parts) >= 2:
        # For categories like FOOD_AND_DRINK_*, primary is FOOD_AND_DRINK
        # For BANK_FEES_*, primary is BANK_FEES
        # For TRANSPORTATION_*, primary is TRANSPORTATION
        if parts[0] in ["FOOD", "GENERAL", "RENT", "HOME", "PERSONAL", "BANK", "LOAN"]:
            return "_".join(parts[:3]) if len(parts) >= 3 else "_".join(parts[:2])
        return parts[0]
    return detailed_category


def create_plaid_mappings():
    """Create default Plaid category mappings for all users."""
    print("=" * 70)
    print("Creating Plaid Category Mappings")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Get all active users
        users = db.query(User).filter(User.is_active.is_(True)).all()

        if not users:
            print("\n❌ No active users found. Please create a user first.")
            sys.exit(1)

        print(f"\nFound {len(users)} active user(s)")
        print()

        total_created = 0
        total_skipped = 0
        missing_categories = []

        for user in users:
            print(f"Processing user: {user.email}")
            created_count = 0
            skipped_count = 0

            # Get categories for this specific user
            user_categories = {
                cat.beancount_account: cat
                for cat in db.query(Category).filter(Category.user_id == user.id).all()
            }

            for detailed_category, beancount_account in PLAID_CATEGORY_MAPPINGS.items():
                # Check if category exists for this user
                if beancount_account not in user_categories:
                    if beancount_account not in missing_categories:
                        missing_categories.append(beancount_account)
                    continue

                category = user_categories[beancount_account]
                primary_category = extract_primary_category(detailed_category)

                # Check if mapping already exists for this user
                existing_mapping = (
                    db.query(PlaidCategoryMapping)
                    .filter(
                        PlaidCategoryMapping.user_id == user.id,
                        PlaidCategoryMapping.plaid_primary_category == primary_category,
                        PlaidCategoryMapping.plaid_detailed_category == detailed_category,
                    )
                    .first()
                )

                if existing_mapping:
                    skipped_count += 1
                    continue

                # Create the mapping
                mapping = PlaidCategoryMapping(
                    user_id=user.id,
                    plaid_primary_category=primary_category,
                    plaid_detailed_category=detailed_category,
                    category_id=category.id,
                    confidence=1.0,
                    auto_apply=True,
                )

                db.add(mapping)
                created_count += 1

            total_created += created_count
            total_skipped += skipped_count

            if created_count > 0:
                print(f"  ✓ Created {created_count} mappings")
            if skipped_count > 0:
                print(f"  ⊘ Skipped {skipped_count} existing mappings")
            print()

        db.commit()

        print("=" * 70)
        print(f"✅ Created {total_created} total mappings across {len(users)} user(s)")
        if total_skipped > 0:
            print(f"⊘  Skipped {total_skipped} existing mappings")

        if missing_categories:
            print()
            print("⚠️  Warning: The following categories were not found:")
            for cat in missing_categories:
                print(f"   - {cat}")
            print()
            print("   These categories need to be created first before mappings can be added.")

        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to create mappings: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_plaid_mappings()
