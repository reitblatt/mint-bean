"""Category service for managing expense categories."""

from sqlalchemy.orm import Session

from app.models.category import Category


def create_category(
    db: Session,
    user_id: int,
    name: str,
    display_name: str,
    category_type: str = "expense",
    parent_id: int | None = None,
) -> Category:
    """
    Create a category if it doesn't already exist.

    Args:
        db: Database session
        user_id: User ID
        name: Category name (Beancount-style)
        display_name: Human-readable display name
        category_type: Category type (expense, income, transfer)
        parent_id: Parent category ID for hierarchy

    Returns:
        Created or existing category
    """
    # Check if category already exists for this user
    existing = db.query(Category).filter(Category.user_id == user_id, Category.name == name).first()

    if existing:
        return existing

    category = Category(
        user_id=user_id,
        name=name,
        display_name=display_name,
        beancount_account=name,
        category_type=category_type,
        parent_id=parent_id,
        is_active=True,
    )

    db.add(category)
    db.flush()
    return category


def seed_default_categories(db: Session, user_id: int) -> None:
    """
    Seed default expense categories for a new user.

    Args:
        db: Database session
        user_id: User ID to create categories for
    """
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
        db, user_id, "Expenses:Auto-and-Transport:Auto-Payment", "Auto Payment", parent_id=auto.id
    )
    create_category(
        db, user_id, "Expenses:Auto-and-Transport:Car-Wash", "Car Wash", parent_id=auto.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Auto-and-Transport:License-and-Registration",
        "License & Registration",
        parent_id=auto.id,
    )
    create_category(
        db, user_id, "Expenses:Auto-and-Transport:Gas-and-Fuel", "Gas & Fuel", parent_id=auto.id
    )
    create_category(
        db, user_id, "Expenses:Auto-and-Transport:Parking", "Parking", parent_id=auto.id
    )
    parking = (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.name == "Expenses:Auto-and-Transport:Parking")
        .first()
    )
    create_category(
        db,
        user_id,
        "Expenses:Auto-and-Transport:Parking:Ticket",
        "Parking Ticket",
        parent_id=parking.id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Auto-and-Transport:Public-Transportation",
        "Public Transportation",
        parent_id=auto.id,
    )
    create_category(
        db, user_id, "Expenses:Auto-and-Transport:Ride-Share", "Ride Share", parent_id=auto.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Auto-and-Transport:Service-and-Parts",
        "Service & Parts",
        parent_id=auto.id,
    )
    create_category(db, user_id, "Expenses:Auto-and-Transport:Taxi", "Taxi", parent_id=auto.id)
    create_category(db, user_id, "Expenses:Auto-and-Transport:Tolls", "Tolls", parent_id=auto.id)

    # Bills & Utilities
    bills = create_category(db, user_id, "Expenses:Bills-and-Utilities", "Bills & Utilities")
    create_category(
        db, user_id, "Expenses:Bills-and-Utilities:Home-Phone", "Home Phone", parent_id=bills.id
    )
    create_category(
        db, user_id, "Expenses:Bills-and-Utilities:Internet", "Internet", parent_id=bills.id
    )
    create_category(
        db, user_id, "Expenses:Bills-and-Utilities:Mobile-Phone", "Mobile Phone", parent_id=bills.id
    )
    create_category(
        db, user_id, "Expenses:Bills-and-Utilities:Television", "Television", parent_id=bills.id
    )
    create_category(
        db, user_id, "Expenses:Bills-and-Utilities:Utilities", "Utilities", parent_id=bills.id
    )
    create_category(
        db, user_id, "Expenses:Bills-and-Utilities:Membership", "Membership", parent_id=bills.id
    )

    # Business Services
    business = create_category(db, user_id, "Expenses:Business-Services", "Business Services")
    create_category(
        db, user_id, "Expenses:Business-Services:Advertising", "Advertising", parent_id=business.id
    )
    create_category(db, user_id, "Expenses:Business-Services:Legal", "Legal", parent_id=business.id)
    create_category(
        db,
        user_id,
        "Expenses:Business-Services:Office-Supplies",
        "Office Supplies",
        parent_id=business.id,
    )
    create_category(
        db, user_id, "Expenses:Business-Services:Printing", "Printing", parent_id=business.id
    )
    create_category(
        db, user_id, "Expenses:Business-Services:Shipping", "Shipping", parent_id=business.id
    )

    # Child
    child = create_category(db, user_id, "Expenses:Child", "Child")
    create_category(db, user_id, "Expenses:Child:Allowance", "Allowance", parent_id=child.id)
    create_category(
        db, user_id, "Expenses:Child:Baby-Supplies", "Baby Supplies", parent_id=child.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Child:Babysitter-and-Daycare",
        "Babysitter & Daycare",
        parent_id=child.id,
    )

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
        db, user_id, "Expenses:Education:Student-Loan", "Student Loan", parent_id=education.id
    )
    create_category(db, user_id, "Expenses:Education:Tuition", "Tuition", parent_id=education.id)
    create_category(
        db, user_id, "Expenses:Education:Online-Services", "Online Services", parent_id=education.id
    )
    create_category(
        db, user_id, "Expenses:Education:Subscriptions", "Subscriptions", parent_id=education.id
    )

    # Entertainment
    entertainment = create_category(db, user_id, "Expenses:Entertainment", "Entertainment")
    create_category(
        db, user_id, "Expenses:Entertainment:Amusement", "Amusement", parent_id=entertainment.id
    )
    create_category(db, user_id, "Expenses:Entertainment:Arts", "Arts", parent_id=entertainment.id)
    create_category(
        db, user_id, "Expenses:Entertainment:Books", "Books", parent_id=entertainment.id
    )
    create_category(
        db, user_id, "Expenses:Entertainment:Concerts", "Concerts", parent_id=entertainment.id
    )
    create_category(
        db, user_id, "Expenses:Entertainment:Games", "Games", parent_id=entertainment.id
    )
    create_category(
        db, user_id, "Expenses:Entertainment:Hobbies", "Hobbies", parent_id=entertainment.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Entertainment:Movies-and-DVDs",
        "Movies & DVDs",
        parent_id=entertainment.id,
    )
    create_category(
        db, user_id, "Expenses:Entertainment:Music", "Music", parent_id=entertainment.id
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
        "Expenses:Entertainment:Sporting-Events",
        "Sporting Events",
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
        "Expenses:Entertainment:Subscriptions:Streaming",
        "Streaming",
        parent_id=db.query(Category)
        .filter(
            Category.user_id == user_id, Category.name == "Expenses:Entertainment:Subscriptions"
        )
        .first()
        .id,
    )
    create_category(
        db, user_id, "Expenses:Entertainment:Tobacco", "Tobacco", parent_id=entertainment.id
    )
    create_category(db, user_id, "Expenses:Entertainment:Toys", "Toys", parent_id=entertainment.id)

    # Fees & Charges
    fees = create_category(db, user_id, "Expenses:Fees-and-Charges", "Fees & Charges")
    create_category(db, user_id, "Expenses:Fees-and-Charges:ATM-Fee", "ATM Fee", parent_id=fees.id)
    create_category(
        db, user_id, "Expenses:Fees-and-Charges:Bank-Fee", "Bank Fee", parent_id=fees.id
    )
    create_category(
        db, user_id, "Expenses:Fees-and-Charges:Finance-Charge", "Finance Charge", parent_id=fees.id
    )
    create_category(
        db, user_id, "Expenses:Fees-and-Charges:Late-Fee", "Late Fee", parent_id=fees.id
    )
    create_category(
        db, user_id, "Expenses:Fees-and-Charges:Service-Fee", "Service Fee", parent_id=fees.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Fees-and-Charges:Trade-Commissions",
        "Trade Commissions",
        parent_id=fees.id,
    )
    create_category(
        db, user_id, "Expenses:Fees-and-Charges:Interest", "Interest", parent_id=fees.id
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
        db, user_id, "Expenses:Food-and-Dining:Coffee-Shops", "Coffee Shops", parent_id=food.id
    )
    create_category(
        db, user_id, "Expenses:Food-and-Dining:Fast-Food", "Fast Food", parent_id=food.id
    )
    create_category(
        db, user_id, "Expenses:Food-and-Dining:Food-Delivery", "Food Delivery", parent_id=food.id
    )
    create_category(
        db, user_id, "Expenses:Food-and-Dining:Groceries", "Groceries", parent_id=food.id
    )
    create_category(
        db, user_id, "Expenses:Food-and-Dining:Restaurants", "Restaurants", parent_id=food.id
    )
    create_category(db, user_id, "Expenses:Food-and-Dining:Snacks", "Snacks", parent_id=food.id)
    create_category(db, user_id, "Expenses:Food-and-Dining:Takeout", "Takeout", parent_id=food.id)

    # Gifts & Donations
    gifts = create_category(db, user_id, "Expenses:Gifts-and-Donations", "Gifts & Donations")
    create_category(
        db, user_id, "Expenses:Gifts-and-Donations:Charity", "Charity", parent_id=gifts.id
    )
    charity = (
        db.query(Category)
        .filter(
            Category.user_id == user_id, Category.name == "Expenses:Gifts-and-Donations:Charity"
        )
        .first()
    )
    create_category(
        db,
        user_id,
        "Expenses:Gifts-and-Donations:Charity:Anthropic",
        "Anthropic",
        parent_id=charity.id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Gifts-and-Donations:Charity:GiveWell",
        "GiveWell",
        parent_id=charity.id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Gifts-and-Donations:Charity:GiveDirectly",
        "GiveDirectly",
        parent_id=charity.id,
    )
    create_category(
        db, user_id, "Expenses:Gifts-and-Donations:Charity:MIRI", "MIRI", parent_id=charity.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Gifts-and-Donations:Charity:OpenPhil",
        "OpenPhil",
        parent_id=charity.id,
    )
    create_category(db, user_id, "Expenses:Gifts-and-Donations:Gifts", "Gifts", parent_id=gifts.id)
    create_category(
        db, user_id, "Expenses:Gifts-and-Donations:Political", "Political", parent_id=gifts.id
    )
    create_category(
        db, user_id, "Expenses:Gifts-and-Donations:Religious", "Religious", parent_id=gifts.id
    )

    # Health & Fitness
    health = create_category(db, user_id, "Expenses:Health-and-Fitness", "Health & Fitness")
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Dentist", "Dentist", parent_id=health.id
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Doctor", "Doctor", parent_id=health.id
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Eye-Care", "Eye Care", parent_id=health.id
    )
    create_category(db, user_id, "Expenses:Health-and-Fitness:Gym", "Gym", parent_id=health.id)
    create_category(
        db,
        user_id,
        "Expenses:Health-and-Fitness:Health-Insurance",
        "Health Insurance",
        parent_id=health.id,
    )
    health_insurance = (
        db.query(Category)
        .filter(
            Category.user_id == user_id,
            Category.name == "Expenses:Health-and-Fitness:Health-Insurance",
        )
        .first()
    )
    create_category(
        db,
        user_id,
        "Expenses:Health-and-Fitness:Health-Insurance:Dental",
        "Dental",
        parent_id=health_insurance.id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Health-and-Fitness:Health-Insurance:Medical",
        "Medical",
        parent_id=health_insurance.id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Health-and-Fitness:Health-Insurance:Vision",
        "Vision",
        parent_id=health_insurance.id,
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Massage", "Massage", parent_id=health.id
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Pharmacy", "Pharmacy", parent_id=health.id
    )
    create_category(
        db,
        user_id,
        "Expenses:Health-and-Fitness:Physical-Therapy",
        "Physical Therapy",
        parent_id=health.id,
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Sports", "Sports", parent_id=health.id
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Supplements", "Supplements", parent_id=health.id
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Therapy", "Therapy", parent_id=health.id
    )
    create_category(
        db, user_id, "Expenses:Health-and-Fitness:Vision", "Vision", parent_id=health.id
    )
    create_category(db, user_id, "Expenses:Health-and-Fitness:Yoga", "Yoga", parent_id=health.id)

    # Home
    home = create_category(db, user_id, "Expenses:Home", "Home")
    create_category(db, user_id, "Expenses:Home:Furniture", "Furniture", parent_id=home.id)
    create_category(
        db, user_id, "Expenses:Home:Home-Improvement", "Home Improvement", parent_id=home.id
    )
    create_category(
        db, user_id, "Expenses:Home:Home-Insurance", "Home Insurance", parent_id=home.id
    )
    create_category(db, user_id, "Expenses:Home:Home-Services", "Home Services", parent_id=home.id)
    create_category(db, user_id, "Expenses:Home:Home-Supplies", "Home Supplies", parent_id=home.id)
    create_category(db, user_id, "Expenses:Home:Household", "Household", parent_id=home.id)
    create_category(
        db, user_id, "Expenses:Home:Lawn-and-Garden", "Lawn & Garden", parent_id=home.id
    )
    create_category(
        db, user_id, "Expenses:Home:Mortgage-and-Rent", "Mortgage & Rent", parent_id=home.id
    )
    create_category(db, user_id, "Expenses:Home:Property-Tax", "Property Tax", parent_id=home.id)
    create_category(db, user_id, "Expenses:Home:Rent", "Rent", parent_id=home.id)
    create_category(db, user_id, "Expenses:Home:Security", "Security", parent_id=home.id)

    # Personal Care
    personal = create_category(db, user_id, "Expenses:Personal-Care", "Personal Care")
    create_category(db, user_id, "Expenses:Personal-Care:Hair", "Hair", parent_id=personal.id)
    create_category(db, user_id, "Expenses:Personal-Care:Laundry", "Laundry", parent_id=personal.id)
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
        db, user_id, "Expenses:Pets:Pet-Food-and-Supplies", "Pet Food & Supplies", parent_id=pets.id
    )
    create_category(db, user_id, "Expenses:Pets:Pet-Grooming", "Pet Grooming", parent_id=pets.id)
    create_category(db, user_id, "Expenses:Pets:Veterinary", "Veterinary", parent_id=pets.id)

    # Shopping
    shopping = create_category(db, user_id, "Expenses:Shopping", "Shopping")
    create_category(db, user_id, "Expenses:Shopping:Books", "Books", parent_id=shopping.id)
    create_category(db, user_id, "Expenses:Shopping:Clothing", "Clothing", parent_id=shopping.id)
    create_category(
        db,
        user_id,
        "Expenses:Shopping:Electronics-and-Software",
        "Electronics & Software",
        parent_id=shopping.id,
    )
    create_category(db, user_id, "Expenses:Shopping:Home", "Home", parent_id=shopping.id)
    create_category(db, user_id, "Expenses:Shopping:Hobbies", "Hobbies", parent_id=shopping.id)
    create_category(db, user_id, "Expenses:Shopping:Kids", "Kids", parent_id=shopping.id)
    create_category(db, user_id, "Expenses:Shopping:Online", "Online", parent_id=shopping.id)
    create_category(db, user_id, "Expenses:Shopping:Other", "Other", parent_id=shopping.id)
    create_category(
        db, user_id, "Expenses:Shopping:Sporting-Goods", "Sporting Goods", parent_id=shopping.id
    )
    create_category(db, user_id, "Expenses:Shopping:Target", "Target", parent_id=shopping.id)

    # Taxes
    taxes = create_category(db, user_id, "Expenses:Taxes", "Taxes")
    create_category(db, user_id, "Expenses:Taxes:Federal", "Federal", parent_id=taxes.id)
    create_category(db, user_id, "Expenses:Taxes:Local", "Local", parent_id=taxes.id)
    create_category(db, user_id, "Expenses:Taxes:Property", "Property", parent_id=taxes.id)
    create_category(db, user_id, "Expenses:Taxes:Sales", "Sales", parent_id=taxes.id)
    create_category(db, user_id, "Expenses:Taxes:State", "State", parent_id=taxes.id)
    create_category(
        db,
        user_id,
        "Expenses:Taxes:State:CA",
        "CA",
        parent_id=db.query(Category)
        .filter(Category.user_id == user_id, Category.name == "Expenses:Taxes:State")
        .first()
        .id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Taxes:State:NY",
        "NY",
        parent_id=db.query(Category)
        .filter(Category.user_id == user_id, Category.name == "Expenses:Taxes:State")
        .first()
        .id,
    )
    create_category(
        db,
        user_id,
        "Expenses:Taxes:State:WA",
        "WA",
        parent_id=db.query(Category)
        .filter(Category.user_id == user_id, Category.name == "Expenses:Taxes:State")
        .first()
        .id,
    )
    create_category(
        db, user_id, "Expenses:Taxes:Tax-Preparation", "Tax Preparation", parent_id=taxes.id
    )

    # Travel
    travel = create_category(db, user_id, "Expenses:Travel", "Travel")
    create_category(db, user_id, "Expenses:Travel:Air-Travel", "Air Travel", parent_id=travel.id)
    create_category(db, user_id, "Expenses:Travel:Hotel", "Hotel", parent_id=travel.id)
    create_category(
        db, user_id, "Expenses:Travel:Rental-Car-and-Taxi", "Rental Car & Taxi", parent_id=travel.id
    )
    create_category(db, user_id, "Expenses:Travel:Vacation", "Vacation", parent_id=travel.id)
    create_category(db, user_id, "Expenses:Travel:Visa", "Visa", parent_id=travel.id)
    create_category(db, user_id, "Expenses:Travel:Luggage", "Luggage", parent_id=travel.id)

    # Wedding
    wedding = create_category(db, user_id, "Expenses:Wedding", "Wedding")
    create_category(db, user_id, "Expenses:Wedding:Wedding", "Wedding", parent_id=wedding.id)

    # Uncategorized
    uncategorized = create_category(db, user_id, "Expenses:Uncategorized", "Uncategorized")
    create_category(
        db, user_id, "Expenses:Uncategorized:Cash-and-ATM", "Cash & ATM", parent_id=uncategorized.id
    )
    create_category(
        db, user_id, "Expenses:Uncategorized:Check", "Check", parent_id=uncategorized.id
    )
    create_category(db, user_id, "Expenses:Uncategorized:Misc", "Misc", parent_id=uncategorized.id)

    db.commit()
