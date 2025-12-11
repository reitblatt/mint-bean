"""Plaid API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plaid_item import PlaidItem
from app.schemas.plaid_item import (
    LinkTokenCreateRequest,
    LinkTokenCreateResponse,
    PlaidItemResponse,
    PublicTokenExchangeRequest,
    PublicTokenExchangeResponse,
    TransactionsSyncResponse,
)
from app.services.plaid_service import plaid_service

router = APIRouter()


@router.post("/link/token/create", response_model=LinkTokenCreateResponse)
def create_link_token(
    request: LinkTokenCreateRequest,
) -> LinkTokenCreateResponse:
    """
    Create a link token for Plaid Link.

    Args:
        request: Link token create request

    Returns:
        Link token response with token and expiration
    """
    try:
        result = plaid_service.create_link_token(user_id=request.user_id)
        return LinkTokenCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create link token: {str(e)}")


@router.post("/item/public_token/exchange", response_model=PublicTokenExchangeResponse)
def exchange_public_token(
    request: PublicTokenExchangeRequest,
    db: Session = Depends(get_db),
) -> PublicTokenExchangeResponse:
    """
    Exchange public token for access token.

    Args:
        request: Public token exchange request
        db: Database session

    Returns:
        Item information
    """
    try:
        plaid_item = plaid_service.exchange_public_token(request.public_token, db)
        return PublicTokenExchangeResponse(
            item_id=plaid_item.item_id,
            institution_id=plaid_item.institution_id,
            institution_name=plaid_item.institution_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to exchange public token: {str(e)}"
        )


@router.get("/items", response_model=list[PlaidItemResponse])
def list_plaid_items(
    db: Session = Depends(get_db),
) -> list[PlaidItem]:
    """
    List all Plaid items.

    Args:
        db: Database session

    Returns:
        List of Plaid items
    """
    items = db.query(PlaidItem).filter(PlaidItem.is_active == True).all()
    return items


@router.get("/items/{item_id}", response_model=PlaidItemResponse)
def get_plaid_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> PlaidItem:
    """
    Get a specific Plaid item.

    Args:
        item_id: Plaid item ID
        db: Database session

    Returns:
        Plaid item details
    """
    item = db.query(PlaidItem).filter(PlaidItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plaid item not found")
    return item


@router.post("/items/{item_id}/sync", response_model=TransactionsSyncResponse)
def sync_transactions(
    item_id: int,
    db: Session = Depends(get_db),
) -> TransactionsSyncResponse:
    """
    Sync transactions for a Plaid item.

    Args:
        item_id: Plaid item ID
        db: Database session

    Returns:
        Sync results with counts
    """
    # Get plaid item
    plaid_item = db.query(PlaidItem).filter(PlaidItem.id == item_id).first()
    if not plaid_item:
        raise HTTPException(status_code=404, detail="Plaid item not found")

    if not plaid_item.is_active:
        raise HTTPException(status_code=400, detail="Plaid item is not active")

    try:
        added, modified, removed, cursor = plaid_service.sync_transactions(plaid_item, db)
        return TransactionsSyncResponse(
            added=added,
            modified=modified,
            removed=removed,
            cursor=cursor,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync transactions: {str(e)}")


@router.delete("/items/{item_id}", status_code=204)
def delete_plaid_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Deactivate a Plaid item.

    Args:
        item_id: Plaid item ID
        db: Database session
    """
    plaid_item = db.query(PlaidItem).filter(PlaidItem.id == item_id).first()
    if not plaid_item:
        raise HTTPException(status_code=404, detail="Plaid item not found")

    plaid_item.is_active = False
    db.commit()
