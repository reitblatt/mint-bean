"""Plaid API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.plaid_item import PlaidItem
from app.models.user import User
from app.schemas.plaid_item import (
    LinkTokenCreateRequest,
    LinkTokenCreateResponse,
    PlaidItemResponse,
    PublicTokenExchangeRequest,
    PublicTokenExchangeResponse,
    TransactionsSyncResponse,
)
from app.services.plaid_service import create_plaid_service
from app.services.settings_service import get_or_create_settings

router = APIRouter()

# Plaid Personal Finance Categories
# Source: https://plaid.com/documents/transactions-personal-finance-category-taxonomy.csv
PLAID_CATEGORIES = {
    "INCOME": [
        "INCOME_DIVIDENDS",
        "INCOME_INTEREST_EARNED",
        "INCOME_RETIREMENT_PENSION",
        "INCOME_TAX_REFUND",
        "INCOME_UNEMPLOYMENT",
        "INCOME_WAGES",
        "INCOME_OTHER_INCOME",
    ],
    "TRANSFER_IN": [
        "TRANSFER_IN_CASH_DEPOSITS_AND_TRANSFERS",
        "TRANSFER_IN_DEPOSIT",
        "TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS",
        "TRANSFER_IN_SAVINGS",
        "TRANSFER_IN_ACCOUNT_TRANSFER",
        "TRANSFER_IN_OTHER_TRANSFER_IN",
    ],
    "TRANSFER_OUT": [
        "TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS",
        "TRANSFER_OUT_SAVINGS",
        "TRANSFER_OUT_WITHDRAWAL",
        "TRANSFER_OUT_ACCOUNT_TRANSFER",
        "TRANSFER_OUT_OTHER_TRANSFER_OUT",
    ],
    "LOAN_PAYMENTS": [
        "LOAN_PAYMENTS_CAR_PAYMENT",
        "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT",
        "LOAN_PAYMENTS_PERSONAL_LOAN_PAYMENT",
        "LOAN_PAYMENTS_MORTGAGE_PAYMENT",
        "LOAN_PAYMENTS_STUDENT_LOAN_PAYMENT",
        "LOAN_PAYMENTS_OTHER_PAYMENT",
    ],
    "BANK_FEES": [
        "BANK_FEES_ATM_FEES",
        "BANK_FEES_FOREIGN_TRANSACTION_FEES",
        "BANK_FEES_INSUFFICIENT_FUNDS",
        "BANK_FEES_INTEREST_CHARGE",
        "BANK_FEES_OVERDRAFT_FEES",
        "BANK_FEES_OTHER_BANK_FEES",
    ],
    "ENTERTAINMENT": [
        "ENTERTAINMENT_CASINOS_AND_GAMBLING",
        "ENTERTAINMENT_MUSIC_AND_AUDIO",
        "ENTERTAINMENT_SPORTING_EVENTS_AMUSEMENT_PARKS_AND_MUSEUMS",
        "ENTERTAINMENT_TV_AND_MOVIES",
        "ENTERTAINMENT_VIDEO_GAMES",
        "ENTERTAINMENT_OTHER_ENTERTAINMENT",
    ],
    "FOOD_AND_DRINK": [
        "FOOD_AND_DRINK_BEER_WINE_AND_LIQUOR",
        "FOOD_AND_DRINK_COFFEE",
        "FOOD_AND_DRINK_FAST_FOOD",
        "FOOD_AND_DRINK_GROCERIES",
        "FOOD_AND_DRINK_RESTAURANT",
        "FOOD_AND_DRINK_VENDING_MACHINES",
        "FOOD_AND_DRINK_OTHER_FOOD_AND_DRINK",
    ],
    "GENERAL_MERCHANDISE": [
        "GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS",
        "GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES",
        "GENERAL_MERCHANDISE_CONVENIENCE_STORES",
        "GENERAL_MERCHANDISE_DEPARTMENT_STORES",
        "GENERAL_MERCHANDISE_DISCOUNT_STORES",
        "GENERAL_MERCHANDISE_ELECTRONICS",
        "GENERAL_MERCHANDISE_GIFTS_AND_NOVELTIES",
        "GENERAL_MERCHANDISE_OFFICE_SUPPLIES",
        "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES",
        "GENERAL_MERCHANDISE_PET_SUPPLIES",
        "GENERAL_MERCHANDISE_SPORTING_GOODS",
        "GENERAL_MERCHANDISE_SUPERSTORES",
        "GENERAL_MERCHANDISE_TOBACCO_AND_VAPE",
        "GENERAL_MERCHANDISE_OTHER_GENERAL_MERCHANDISE",
    ],
    "HOME_IMPROVEMENT": [
        "HOME_IMPROVEMENT_FURNITURE",
        "HOME_IMPROVEMENT_HARDWARE",
        "HOME_IMPROVEMENT_REPAIR_AND_MAINTENANCE",
        "HOME_IMPROVEMENT_SECURITY",
        "HOME_IMPROVEMENT_OTHER_HOME_IMPROVEMENT",
    ],
    "MEDICAL": [
        "MEDICAL_DENTAL_CARE",
        "MEDICAL_EYE_CARE",
        "MEDICAL_NURSING_CARE",
        "MEDICAL_PHARMACIES_AND_SUPPLEMENTS",
        "MEDICAL_PRIMARY_CARE",
        "MEDICAL_VETERINARY_SERVICES",
        "MEDICAL_OTHER_MEDICAL",
    ],
    "PERSONAL_CARE": [
        "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS",
        "PERSONAL_CARE_HAIR_AND_BEAUTY",
        "PERSONAL_CARE_LAUNDRY_AND_DRY_CLEANING",
        "PERSONAL_CARE_OTHER_PERSONAL_CARE",
    ],
    "GENERAL_SERVICES": [
        "GENERAL_SERVICES_ACCOUNTING_AND_FINANCIAL_PLANNING",
        "GENERAL_SERVICES_AUTOMOTIVE",
        "GENERAL_SERVICES_CHILDCARE",
        "GENERAL_SERVICES_CONSULTING_AND_LEGAL",
        "GENERAL_SERVICES_EDUCATION",
        "GENERAL_SERVICES_INSURANCE",
        "GENERAL_SERVICES_POSTAGE_AND_SHIPPING",
        "GENERAL_SERVICES_STORAGE",
        "GENERAL_SERVICES_OTHER_GENERAL_SERVICES",
    ],
    "GOVERNMENT_AND_NON_PROFIT": [
        "GOVERNMENT_AND_NON_PROFIT_DONATIONS",
        "GOVERNMENT_AND_NON_PROFIT_GOVERNMENT_DEPARTMENTS_AND_AGENCIES",
        "GOVERNMENT_AND_NON_PROFIT_TAX_PAYMENT",
        "GOVERNMENT_AND_NON_PROFIT_OTHER_GOVERNMENT_AND_NON_PROFIT",
    ],
    "TRANSPORTATION": [
        "TRANSPORTATION_BIKES_AND_SCOOTERS",
        "TRANSPORTATION_GAS",
        "TRANSPORTATION_PARKING",
        "TRANSPORTATION_PUBLIC_TRANSIT",
        "TRANSPORTATION_TAXIS_AND_RIDE_SHARES",
        "TRANSPORTATION_TOLLS",
        "TRANSPORTATION_OTHER_TRANSPORTATION",
    ],
    "TRAVEL": [
        "TRAVEL_FLIGHTS",
        "TRAVEL_LODGING",
        "TRAVEL_RENTAL_CARS",
        "TRAVEL_OTHER_TRAVEL",
    ],
    "RENT_AND_UTILITIES": [
        "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY",
        "RENT_AND_UTILITIES_INTERNET_AND_CABLE",
        "RENT_AND_UTILITIES_RENT",
        "RENT_AND_UTILITIES_SEWAGE_AND_WASTE_MANAGEMENT",
        "RENT_AND_UTILITIES_TELEPHONE",
        "RENT_AND_UTILITIES_WATER",
        "RENT_AND_UTILITIES_OTHER_UTILITIES",
    ],
}


@router.get("/categories")
def get_plaid_categories(
    current_user: User = Depends(get_current_user),
) -> dict[str, list[str]]:
    """
    Get list of Plaid personal finance categories.

    Args:
        current_user: Current authenticated user

    Returns:
        Dictionary mapping primary categories to their detailed categories
    """
    return PLAID_CATEGORIES


@router.post("/link/token/create", response_model=LinkTokenCreateResponse)
def create_link_token(
    request: LinkTokenCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LinkTokenCreateResponse:
    """
    Create a link token for Plaid Link.

    Args:
        request: Link token create request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Link token response with token and expiration
    """
    try:
        # Get settings from database
        settings = get_or_create_settings(db)

        # Create service with database credentials
        service = create_plaid_service(
            client_id=settings.plaid_client_id,
            secret=settings.plaid_secret,
            environment=settings.plaid_environment,
        )

        result = service.create_link_token(user_id=str(current_user.id))
        return LinkTokenCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create link token: {str(e)}") from e


@router.post("/item/public_token/exchange", response_model=PublicTokenExchangeResponse)
def exchange_public_token(
    request: PublicTokenExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PublicTokenExchangeResponse:
    """
    Exchange public token for access token.

    Args:
        request: Public token exchange request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Item information
    """
    try:
        # Get settings from database
        settings = get_or_create_settings(db)

        # Create service with database credentials
        service = create_plaid_service(
            client_id=settings.plaid_client_id,
            secret=settings.plaid_secret,
            environment=settings.plaid_environment,
        )

        plaid_item = service.exchange_public_token(
            request.public_token, db, user_id=current_user.id
        )
        return PublicTokenExchangeResponse(
            item_id=plaid_item.item_id,
            institution_id=plaid_item.institution_id,
            institution_name=plaid_item.institution_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to exchange public token: {str(e)}"
        ) from e


@router.get("/items", response_model=list[PlaidItemResponse])
def list_plaid_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlaidItem]:
    """
    List all Plaid items for the current environment.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of Plaid items
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    items = (
        db.query(PlaidItem)
        .filter(
            PlaidItem.user_id == current_user.id,
            PlaidItem.is_active,
            PlaidItem.environment == settings.plaid_environment,
        )
        .all()
    )
    return items


@router.get("/items/{item_id}", response_model=PlaidItemResponse)
def get_plaid_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaidItem:
    """
    Get a specific Plaid item for the current environment.

    Args:
        item_id: Plaid item ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Plaid item details
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    item = (
        db.query(PlaidItem)
        .filter(
            PlaidItem.id == item_id,
            PlaidItem.user_id == current_user.id,
            PlaidItem.environment == settings.plaid_environment,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Plaid item not found")
    return item


@router.post("/items/{item_id}/sync", response_model=TransactionsSyncResponse)
def sync_transactions(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionsSyncResponse:
    """
    Sync transactions for a Plaid item in the current environment.

    Args:
        item_id: Plaid item ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Sync results with counts
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    # Get plaid item
    plaid_item = (
        db.query(PlaidItem)
        .filter(
            PlaidItem.id == item_id,
            PlaidItem.user_id == current_user.id,
            PlaidItem.environment == settings.plaid_environment,
        )
        .first()
    )
    if not plaid_item:
        raise HTTPException(status_code=404, detail="Plaid item not found")

    if not plaid_item.is_active:
        raise HTTPException(status_code=400, detail="Plaid item is not active")

    try:
        # Create service with database credentials
        service = create_plaid_service(
            client_id=settings.plaid_client_id,
            secret=settings.plaid_secret,
            environment=settings.plaid_environment,
        )

        added, modified, removed, cursor = service.sync_transactions(plaid_item, db)
        return TransactionsSyncResponse(
            added=added,
            modified=modified,
            removed=removed,
            cursor=cursor,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync transactions: {str(e)}") from e


@router.delete("/items/{item_id}", status_code=204)
def delete_plaid_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Deactivate a Plaid item in the current environment.

    Args:
        item_id: Plaid item ID
        current_user: Current authenticated user
        db: Database session
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    plaid_item = (
        db.query(PlaidItem)
        .filter(
            PlaidItem.id == item_id,
            PlaidItem.user_id == current_user.id,
            PlaidItem.environment == settings.plaid_environment,
        )
        .first()
    )
    if not plaid_item:
        raise HTTPException(status_code=404, detail="Plaid item not found")

    plaid_item.is_active = False
    db.commit()
