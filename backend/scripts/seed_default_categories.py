"""Seed default expense categories based on common Beancount expense accounts."""

import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.models.category import Category

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_category(
    db,
    user_id: int,
    name: str,
    display_name: str,
    category_type: str = "expense",
    parent_id: int | None = None,
    plaid_category: str | None = None,
) -> Category:
    """Create a category if it doesn't already exist."""
    # Check if category already exists for this user
    existing = db.query(Category).filter(Category.user_id == user_id, Category.name == name).first()

    if existing:
        print(f"  Category already exists: {name}")
        return existing

    category = Category(
        user_id=user_id,
        name=name,
        display_name=display_name,
        beancount_account=name,  # Use the same Beancount-style name
        category_type=category_type,
        parent_id=parent_id,
        is_active=True,
    )

    db.add(category)
    db.flush()  # Get the ID without committing
    print(f"  Created: {name}")
    return category


def seed_categories(user_id: int):
    """Seed default expense categories for a user."""
    db = SessionLocal()

    try:
        print(f"\nSeeding default categories for user_id={user_id}...")

        # Auto & Transport
        auto = create_category(db, user_id, "Expenses:Auto-and-Transport", "Auto & Transport")
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Auto-Insurance",
            "Auto Insurance",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Auto-Payment",
            "Auto Payment",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Car-Wash",
            "Car Wash",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:License-and-Registration",
            "License & Registration",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Gas-and-Fuel",
            "Gas & Fuel",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Parking",
            "Parking",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Parking:Ticket",
            "Parking Ticket",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Public-Transportation",
            "Public Transportation",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Ride-Share",
            "Ride Share",
            parent_id=auto.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Auto-and-Transport:Service-and-Parts",
            "Service & Parts",
            parent_id=auto.id,
        )
        create_category(db, user_id, "Expenses:Auto-and-Transport:Taxi", "Taxi", parent_id=auto.id)
        create_category(
            db, user_id, "Expenses:Auto-and-Transport:Tolls", "Tolls", parent_id=auto.id
        )

        # Bills & Utilities
        bills = create_category(db, user_id, "Expenses:Bills-and-Utilities", "Bills & Utilities")
        create_category(
            db,
            user_id,
            "Expenses:Bills-and-Utilities:Home-Phone",
            "Home Phone",
            parent_id=bills.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Bills-and-Utilities:Internet",
            "Internet",
            parent_id=bills.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Bills-and-Utilities:Mobile-Phone",
            "Mobile Phone",
            parent_id=bills.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Bills-and-Utilities:Television",
            "Television",
            parent_id=bills.id,
        )
        utilities = create_category(
            db,
            user_id,
            "Expenses:Bills-and-Utilities:Utilities",
            "Utilities",
            parent_id=bills.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Bills-and-Utilities:Utilities:Electricity",
            "Electricity",
            parent_id=utilities.id,
        )

        # Business Services
        business = create_category(db, user_id, "Expenses:Business-Services", "Business Services")
        create_category(
            db,
            user_id,
            "Expenses:Business-Services:Advertising",
            "Advertising",
            parent_id=business.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Business-Services:Legal",
            "Legal",
            parent_id=business.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Business-Services:Office-Supplies",
            "Office Supplies",
            parent_id=business.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Business-Services:Printing",
            "Printing",
            parent_id=business.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Business-Services:Shipping",
            "Shipping",
            parent_id=business.id,
        )

        # Child
        child = create_category(db, user_id, "Expenses:Child", "Child")
        create_category(
            db,
            user_id,
            "Expenses:Child:Child-Care",
            "Child Care",
            parent_id=child.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Child:Entertainment",
            "Child Entertainment",
            parent_id=child.id,
        )
        create_category(db, user_id, "Expenses:Child:Hair", "Child Hair", parent_id=child.id)

        # Education
        education = create_category(db, user_id, "Expenses:Education", "Education")
        create_category(
            db,
            user_id,
            "Expenses:Education:Books-and-Supplies",
            "Books & Supplies",
            parent_id=education.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Education:Student-Loan",
            "Student Loan",
            parent_id=education.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Education:Tuition",
            "Tuition",
            parent_id=education.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Education:Conference-Registration",
            "Conference Registration",
            parent_id=education.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Education:Deposit",
            "Education Deposit",
            parent_id=education.id,
        )

        # Entertainment
        entertainment = create_category(db, user_id, "Expenses:Entertainment", "Entertainment")
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Amusement",
            "Amusement",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Arts",
            "Arts",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Movies-and-DVDs",
            "Movies & DVDs",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Music",
            "Music",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Newspapers-and-Magazines",
            "Newspapers & Magazines",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Homebrew",
            "Homebrew",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Plays-and-Musicals",
            "Plays & Musicals",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Poker-and-Gambling",
            "Poker & Gambling",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Sailing",
            "Sailing",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Streaming",
            "Streaming",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Subscriptions",
            "Subscriptions",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Games",
            "Games",
            parent_id=entertainment.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Entertainment:Wine-Tasting",
            "Wine Tasting",
            parent_id=entertainment.id,
        )

        # Fees & Charges
        fees = create_category(db, user_id, "Expenses:Fees-and-Charges", "Fees & Charges")
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:ATM-Fee",
            "ATM Fee",
            parent_id=fees.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:Bank-Fee",
            "Bank Fee",
            parent_id=fees.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:Finance-Charge",
            "Finance Charge",
            parent_id=fees.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:Late-Fee",
            "Late Fee",
            parent_id=fees.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:Service-Fee",
            "Service Fee",
            parent_id=fees.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:Credit-Card-Interest",
            "Credit Card Interest",
            parent_id=fees.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Fees-and-Charges:Trade-Commision",
            "Trade Commission",
            parent_id=fees.id,
        )

        # Food & Dining
        food = create_category(db, user_id, "Expenses:Food-and-Dining", "Food & Dining")
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Alcohol-and-Bars",
            "Alcohol & Bars",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Coffee-Shops",
            "Coffee Shops",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Fast-Food",
            "Fast Food",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Food-Delivery",
            "Food Delivery",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Take-out",
            "Take-out",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Groceries",
            "Groceries",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Restaurants",
            "Restaurants",
            parent_id=food.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Food-and-Dining:Wine-and-Spirits",
            "Wine & Spirits",
            parent_id=food.id,
        )

        # Gifts & Donations
        gifts = create_category(db, user_id, "Expenses:Gifts-and-Donations", "Gifts & Donations")
        charity = create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity",
            "Charity",
            parent_id=gifts.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity:LGBT-Rights",
            "LGBT Rights",
            parent_id=charity.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity:Refugees",
            "Refugees",
            parent_id=charity.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity:Journalism",
            "Journalism",
            parent_id=charity.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity:Civil-Rights",
            "Civil Rights",
            parent_id=charity.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity:Animal-Rights",
            "Animal Rights",
            parent_id=charity.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Charity:Community-Support",
            "Community Support",
            parent_id=charity.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Gift",
            "Gifts",
            parent_id=gifts.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Gifts-and-Donations:Feeding",
            "Feeding",
            parent_id=gifts.id,
        )

        # Health & Fitness
        health = create_category(db, user_id, "Expenses:Health-and-Fitness", "Health & Fitness")
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Dentist",
            "Dentist",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Doctor",
            "Doctor",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Eyecare",
            "Eyecare",
            parent_id=health.id,
        )
        create_category(db, user_id, "Expenses:Health-and-Fitness:Gym", "Gym", parent_id=health.id)
        health_ins = create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Health-Insurance",
            "Health Insurance",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Health-Insurance:Dental",
            "Dental Insurance",
            parent_id=health_ins.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Health-Insurance:Vision",
            "Vision Insurance",
            parent_id=health_ins.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Health-Insurance:Medical",
            "Medical Insurance",
            parent_id=health_ins.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Life-Insurance",
            "Life Insurance",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Pharmacy",
            "Pharmacy",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Sports",
            "Sports",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Fly-Fishing",
            "Fly Fishing",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Hiking-and-Camping",
            "Hiking & Camping",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Personal-Training",
            "Personal Training",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Pool-and-Hot-tub",
            "Pool & Hot Tub",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Race-Registration",
            "Race Registration",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Scuba-Diving",
            "Scuba Diving",
            parent_id=health.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Health-and-Fitness:Vitamins-and-Supplements",
            "Vitamins & Supplements",
            parent_id=health.id,
        )

        # Home
        home = create_category(db, user_id, "Expenses:Home", "Home")
        create_category(db, user_id, "Expenses:Home:Cleaning", "Cleaning", parent_id=home.id)
        create_category(db, user_id, "Expenses:Home:Furnishings", "Furnishings", parent_id=home.id)
        create_category(
            db,
            user_id,
            "Expenses:Home:Home-Improvement",
            "Home Improvement",
            parent_id=home.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Home:Home-Insurance",
            "Home Insurance",
            parent_id=home.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Home:Home-Services",
            "Home Services",
            parent_id=home.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Home:Home-Supplies",
            "Home Supplies",
            parent_id=home.id,
        )
        create_category(db, user_id, "Expenses:Home:Kitchen", "Kitchen", parent_id=home.id)
        create_category(
            db,
            user_id,
            "Expenses:Home:Lawn-and-Garden",
            "Lawn & Garden",
            parent_id=home.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Home:Mortgage-Interest",
            "Mortgage Interest",
            parent_id=home.id,
        )
        create_category(db, user_id, "Expenses:Home:Rent", "Mortgage & Rent", parent_id=home.id)
        create_category(
            db,
            user_id,
            "Expenses:Home:Closing-Costs",
            "Closing Costs",
            parent_id=home.id,
        )

        # Personal Care
        personal = create_category(db, user_id, "Expenses:Personal-Care", "Personal Care")
        create_category(db, user_id, "Expenses:Personal-Care:Hair", "Hair", parent_id=personal.id)
        create_category(
            db,
            user_id,
            "Expenses:Personal-Care:Laundry",
            "Laundry",
            parent_id=personal.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Personal-Care:Spa-and-Massage",
            "Spa & Massage",
            parent_id=personal.id,
        )

        # Pets
        pets = create_category(db, user_id, "Expenses:Pets", "Pets")
        create_category(
            db,
            user_id,
            "Expenses:Pets:Pet-Food-and-Supplies",
            "Pet Food & Supplies",
            parent_id=pets.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Pets:Pet-Grooming",
            "Pet Grooming",
            parent_id=pets.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Pets:Veterinary",
            "Veterinary",
            parent_id=pets.id,
        )

        # Shopping
        shopping = create_category(db, user_id, "Expenses:Shopping", "Shopping")
        create_category(
            db,
            user_id,
            "Expenses:Shopping:Baby-Stuff",
            "Baby Stuff",
            parent_id=shopping.id,
        )
        create_category(db, user_id, "Expenses:Shopping:Books", "Books", parent_id=shopping.id)
        create_category(
            db,
            user_id,
            "Expenses:Shopping:Costco-Delivery",
            "Costco Delivery",
            parent_id=shopping.id,
        )
        create_category(
            db, user_id, "Expenses:Shopping:Clothing", "Clothing", parent_id=shopping.id
        )
        create_category(
            db,
            user_id,
            "Expenses:Shopping:Electronics-and-Software",
            "Electronics & Software",
            parent_id=shopping.id,
        )
        create_category(db, user_id, "Expenses:Shopping:Hobbies", "Hobbies", parent_id=shopping.id)
        create_category(
            db,
            user_id,
            "Expenses:Shopping:Sporting-Goods",
            "Sporting Goods",
            parent_id=shopping.id,
        )
        create_category(db, user_id, "Expenses:Shopping:Cycling", "Cycling", parent_id=shopping.id)
        create_category(
            db,
            user_id,
            "Expenses:Shopping:Sailing-Gear",
            "Sailing Gear",
            parent_id=shopping.id,
        )
        create_category(db, user_id, "Expenses:Shopping:Toys", "Toys", parent_id=shopping.id)

        # Taxes
        taxes = create_category(db, user_id, "Expenses:Taxes", "Taxes")
        federal = create_category(
            db,
            user_id,
            "Expenses:Taxes:Federal-Tax",
            "Federal Tax",
            parent_id=taxes.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Federal-Tax:Income",
            "Federal Income Tax",
            parent_id=federal.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Federal-Tax:Medicare",
            "Medicare",
            parent_id=federal.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Federal-Tax:Medicare-Surcharge",
            "Medicare Surcharge",
            parent_id=federal.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Federal-Tax:OASDI",
            "OASDI",
            parent_id=federal.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Local-Tax",
            "Local Tax",
            parent_id=taxes.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Property-Tax",
            "Property Tax",
            parent_id=taxes.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:Sales-Tax",
            "Sales Tax",
            parent_id=taxes.id,
        )
        state = create_category(
            db, user_id, "Expenses:Taxes:State-Tax", "State Tax", parent_id=taxes.id
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:State-Tax:WA:Long-Term-Care",
            "WA Long-Term Care",
            parent_id=state.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:State-Tax:WA:PFL",
            "WA Paid Family Leave",
            parent_id=state.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:State-Tax:CA:Income-Tax",
            "CA Income Tax",
            parent_id=state.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Taxes:State-Tax:CA:VDI",
            "CA Voluntary Disability Insurance",
            parent_id=state.id,
        )

        # Travel
        travel = create_category(db, user_id, "Expenses:Travel", "Travel")
        create_category(
            db,
            user_id,
            "Expenses:Travel:Air-Travel",
            "Air Travel",
            parent_id=travel.id,
        )
        create_category(db, user_id, "Expenses:Travel:Hotel", "Hotel", parent_id=travel.id)
        create_category(
            db,
            user_id,
            "Expenses:Travel:Rental-Car-and-Taxi",
            "Rental Car & Taxi",
            parent_id=travel.id,
        )
        create_category(db, user_id, "Expenses:Travel:Vacation", "Vacation", parent_id=travel.id)
        create_category(
            db,
            user_id,
            "Expenses:Travel:Carbon-Credits",
            "Carbon Credits",
            parent_id=travel.id,
        )
        create_category(
            db,
            user_id,
            "Expenses:Travel:Passport-and-Visa-Fees",
            "Passport & Visa Fees",
            parent_id=travel.id,
        )

        # Wedding
        wedding = create_category(db, user_id, "Expenses:Wedding", "Wedding")
        create_category(
            db,
            user_id,
            "Expenses:Wedding:Wedding-Planner",
            "Wedding Planner",
            parent_id=wedding.id,
        )

        # Uncategorized/Misc
        create_category(db, user_id, "Expenses:Uncategorized", "Uncategorized")
        create_category(db, user_id, "Expenses:Unknown", "Unknown")
        uncat = create_category(db, user_id, "Expenses:Uncategorized", "Uncategorized")
        create_category(
            db,
            user_id,
            "Expenses:Uncategorized:Cash-and-ATM",
            "Cash & ATM",
            parent_id=uncat.id,
        )
        create_category(db, user_id, "Expenses:Uncategorized:Check", "Check", parent_id=uncat.id)
        create_category(db, user_id, "Expenses:Misc-Expenses", "Misc Expenses")

        # Commit all changes
        db.commit()
        print(f"\n✓ Successfully seeded categories for user_id={user_id}")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding categories: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_default_categories.py <user_id>")
        print("\nExample: python seed_default_categories.py 1")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        seed_categories(user_id)
    except ValueError:
        print("Error: user_id must be an integer")
        sys.exit(1)
