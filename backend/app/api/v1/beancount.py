"""Beancount API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.beancount_service import BeancountService

router = APIRouter()


@router.get("/export")
def export_beancount_file(
    db: Session = Depends(get_db),
    reviewed_only: bool = True,
    exclude_pending: bool = True,
):
    """
    Export transactions to Beancount format for download.

    Args:
        reviewed_only: Only export reviewed transactions (default: True)
        exclude_pending: Exclude pending transactions (default: True)

    Returns:
        Beancount file content as plain text
    """
    service = BeancountService()

    try:
        content = service.generate_beancount_content(
            db, reviewed_only=reviewed_only, exclude_pending=exclude_pending
        )

        # Generate filename with current date
        filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.beancount"

        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}") from e


@router.get("/export-count")
def get_export_count(
    db: Session = Depends(get_db),
    reviewed_only: bool = True,
    exclude_pending: bool = True,
):
    """Get count of transactions that would be exported."""
    from app.models.transaction import Transaction

    query = db.query(Transaction)

    if reviewed_only:
        query = query.filter(Transaction.reviewed.is_(True))

    if exclude_pending:
        query = query.filter(Transaction.pending.is_(False))

    count = query.count()

    return {"count": count}
