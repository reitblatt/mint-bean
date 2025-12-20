"""Account API endpoints."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.settings_service import get_or_create_settings

router = APIRouter()


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Account]:
    """
    List all accounts for the current environment.

    Args:
        active_only: Only return active accounts
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of accounts
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    query = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.environment == settings.plaid_environment,
    )
    if active_only:
        query = query.filter(Account.is_active)
    return query.all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Account:
    """
    Get a specific account by ID for the current environment.

    Args:
        account_id: Account ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Account details
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,
            Account.environment == settings.plaid_environment,
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


.post("", response_model=AccountResponse, status_code=201)
def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Account:
    """
    Create a new account.

    Args:
        account: Account data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created account
    """
    # Generate account ID
    import uuid

    account_id = f"acc_{uuid.uuid4().hex[:12]}"

    db_account = Account(
        account_id=account_id,
        user_id=current_user.id,
        **account.model_dump(),
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Account:
    """
    Update an account in the current environment.

    Args:
        account_id: Account ID
        account: Updated account data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated account
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    db_account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,
            Account.environment == settings.plaid_environment,
        )
        .first()
    )
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = account.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)

    db.commit()
    db.refresh(db_account)
    return db_account


@router.delete("/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete an account in the current environment.

    Args:
        account_id: Account ID
        current_user: Current authenticated user
        db: Database session
    """
    # Get current environment from settings
    settings = get_or_create_settings(db)

    db_account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,
            Account.environment == settings.plaid_environment,
        )
        .first()
    )
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(db_account)
    db.commit()
