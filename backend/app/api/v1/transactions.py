"""Transaction API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """
    List transactions with pagination and filters.

    Args:
        page: Page number
        page_size: Number of items per page
        account_id: Filter by account ID
        category_id: Filter by category ID
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        search: Search in description and payee
        db: Database session

    Returns:
        Paginated list of transactions
    """
    query = db.query(Transaction)

    # Apply filters
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Transaction.description.ilike(search_filter))
            | (Transaction.payee.ilike(search_filter))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    transactions = query.order_by(Transaction.date.desc()).offset(offset).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> Transaction:
    """
    Get a specific transaction by ID.

    Args:
        transaction_id: Transaction ID
        db: Database session

    Returns:
        Transaction details
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
) -> Transaction:
    """
    Create a new transaction.

    Args:
        transaction: Transaction data
        db: Database session

    Returns:
        Created transaction
    """
    # Validate account exists
    from app.models.account import Account

    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="Account not found")

    # Generate transaction ID
    import uuid

    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"

    db_transaction = Transaction(transaction_id=transaction_id, **transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: Session = Depends(get_db),
) -> Transaction:
    """
    Update a transaction.

    Args:
        transaction_id: Transaction ID
        transaction: Updated transaction data
        db: Database session

    Returns:
        Updated transaction
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = transaction.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a transaction.

    Args:
        transaction_id: Transaction ID
        db: Database session
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()
