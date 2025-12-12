"""Beancount API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.beancount_service import BeancountService

router = APIRouter()


class SyncResponse(BaseModel):
    """Response model for sync operation."""

    synced: int
    failed: int
    message: str


@router.post("/sync-to-file", response_model=SyncResponse)
def sync_to_beancount_file(db: Session = Depends(get_db)):
    """
    Sync reviewed, non-pending transactions from database to Beancount file.

    This will:
    - Find all transactions that are reviewed, not pending, and not yet synced
    - Write them to the Beancount file in proper format
    - Mark them as synced in the database
    """
    service = BeancountService()

    try:
        result = service.sync_to_file(db)

        message = f"Successfully synced {result['synced']} transaction(s)"
        if result["failed"] > 0:
            message += f", {result['failed']} failed"

        return SyncResponse(synced=result["synced"], failed=result["failed"], message=message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}") from e


@router.get("/unsynced-count")
def get_unsynced_count(db: Session = Depends(get_db)):
    """Get count of transactions ready to be synced to Beancount."""
    from app.models.transaction import Transaction

    count = (
        db.query(Transaction)
        .filter(
            Transaction.synced_to_beancount.is_(False),
            Transaction.reviewed.is_(True),
            Transaction.pending.is_(False),
        )
        .count()
    )

    return {"count": count}
