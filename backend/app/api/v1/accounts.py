"""Account API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
def list_accounts(
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> List[Account]:
    """
    List all accounts.

    Args:
        active_only: Only return active accounts
        db: Database session

    Returns:
        List of accounts
    """
    query = db.query(Account)
    if active_only:
        query = query.filter(Account.active == True)
    return query.all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
) -> Account:
    """
    Get a specific account by ID.

    Args:
        account_id: Account ID
        db: Database session

    Returns:
        Account details
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=AccountResponse, status_code=201)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
) -> Account:
    """
    Create a new account.

    Args:
        account: Account data
        db: Database session

    Returns:
        Created account
    """
    # Generate account ID
    import uuid
    account_id = f"acc_{uuid.uuid4().hex[:12]}"

    db_account = Account(
        account_id=account_id,
        **account.model_dump()
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account: AccountUpdate,
    db: Session = Depends(get_db),
) -> Account:
    """
    Update an account.

    Args:
        account_id: Account ID
        account: Updated account data
        db: Database session

    Returns:
        Updated account
    """
    db_account = db.query(Account).filter(Account.id == account_id).first()
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
    db: Session = Depends(get_db),
) -> None:
    """
    Delete an account.

    Args:
        account_id: Account ID
        db: Database session
    """
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(db_account)
    db.commit()
