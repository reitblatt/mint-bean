"""Analytics API endpoints for dashboard widgets."""

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.analytics import (
    CategoryBreakdown,
    CategoryBreakdownResponse,
    MerchantBreakdown,
    MerchantBreakdownResponse,
    SummaryMetrics,
    TimeSeriesDataPoint,
    TimeSeriesResponse,
)
from app.schemas.widget_config import (
    BreakdownConfig,
    SummaryCardConfig,
    TimeSeriesConfig,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary-metrics", response_model=SummaryMetrics)
def get_summary_metrics(
    start_date: date | None = Query(None, description="Start date for metrics"),
    end_date: date | None = Query(None, description="End date for metrics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryMetrics:
    """Get summary metrics for dashboard cards."""
    # Default to current month if no dates provided
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    if not end_date:
        end_date = date.today()

    # Total balance (sum of all account balances)
    total_balance = (
        db.query(func.sum(Account.current_balance))
        .filter(Account.user_id == current_user.id)
        .scalar()
        or 0.0
    )

    # Build transaction query for date range
    tx_query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date,
    )

    # Total spending (negative amounts)
    total_spending = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0,
        )
        .scalar()
        or 0.0
    )
    total_spending = abs(total_spending)  # Make positive for display

    # Total income (positive amounts)
    total_income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount > 0,
        )
        .scalar()
        or 0.0
    )

    # Transaction count
    transaction_count = tx_query.count()

    # Uncategorized count
    uncategorized_count = tx_query.filter(Transaction.category_id.is_(None)).count()

    # Account count
    account_count = db.query(Account).filter(Account.user_id == current_user.id).count()

    return SummaryMetrics(
        total_balance=total_balance,
        total_spending=total_spending,
        total_income=total_income,
        transaction_count=transaction_count,
        uncategorized_count=uncategorized_count,
        account_count=account_count,
    )


@router.get("/spending-over-time", response_model=TimeSeriesResponse)
def get_spending_over_time(
    start_date: date | None = Query(None, description="Start date for time series"),
    end_date: date | None = Query(None, description="End date for time series"),
    granularity: str = Query("daily", description="Granularity: daily, weekly, monthly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeSeriesResponse:
    """Get spending over time as a time series."""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Get all transactions in range (expenses only)
    transactions = (
        db.query(Transaction.date, func.sum(Transaction.amount).label("total"))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0,  # Expenses only
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
        .all()
    )

    # Convert to data points (make amounts positive)
    data_points = [
        TimeSeriesDataPoint(
            date=tx_date,
            value=abs(total),
            label=tx_date.strftime("%Y-%m-%d"),
        )
        for tx_date, total in transactions
    ]

    return TimeSeriesResponse(data=data_points, granularity=granularity)


@router.get("/spending-by-category", response_model=CategoryBreakdownResponse)
def get_spending_by_category(
    start_date: date | None = Query(None, description="Start date for breakdown"),
    end_date: date | None = Query(None, description="End date for breakdown"),
    limit: int = Query(10, ge=1, le=50, description="Max number of categories to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryBreakdownResponse:
    """Get spending breakdown by category."""
    # Default to current month if no dates provided
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    if not end_date:
        end_date = date.today()

    # Get category totals (expenses only)
    results = (
        db.query(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0,  # Expenses only
        )
        .group_by(Transaction.category_id)
        .order_by(func.sum(Transaction.amount).asc())  # Most negative (highest spending) first
        .limit(limit)
        .all()
    )

    # Calculate total for percentages
    total_amount = sum(abs(total) for _, total, _ in results)

    # Build breakdown with category names
    breakdown = []
    for category_id, total, count in results:
        if category_id:
            category = db.query(Category).filter(Category.id == category_id).first()
            category_name = category.display_name if category else "Unknown"
        else:
            category_name = "Uncategorized"

        amount = abs(total)
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0

        breakdown.append(
            CategoryBreakdown(
                category_id=category_id,
                category_name=category_name,
                amount=amount,
                transaction_count=count,
                percentage=percentage,
            )
        )

    return CategoryBreakdownResponse(data=breakdown, total_amount=total_amount)


@router.get("/spending-by-merchant", response_model=MerchantBreakdownResponse)
def get_spending_by_merchant(
    start_date: date | None = Query(None, description="Start date for breakdown"),
    end_date: date | None = Query(None, description="End date for breakdown"),
    limit: int = Query(10, ge=1, le=50, description="Max number of merchants to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MerchantBreakdownResponse:
    """Get spending breakdown by merchant."""
    # Default to current month if no dates provided
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    if not end_date:
        end_date = date.today()

    # Get merchant totals (expenses only)
    results = (
        db.query(
            Transaction.merchant_name,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0,  # Expenses only
            Transaction.merchant_name.isnot(None),
        )
        .group_by(Transaction.merchant_name)
        .order_by(func.sum(Transaction.amount).asc())  # Most negative (highest spending) first
        .limit(limit)
        .all()
    )

    # Calculate total for percentages
    total_amount = sum(abs(total) for _, total, _ in results)

    # Build breakdown
    breakdown = []
    for merchant_name, total, count in results:
        amount = abs(total)
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0

        breakdown.append(
            MerchantBreakdown(
                merchant_name=merchant_name,
                amount=amount,
                transaction_count=count,
                percentage=percentage,
            )
        )

    return MerchantBreakdownResponse(data=breakdown, total_amount=total_amount)


# Flexible widget query endpoints


@router.post("/query/metric")
def query_metric(
    config: SummaryCardConfig = Body(...),
    start_date: date | None = Query(None, description="Start date for metric"),
    end_date: date | None = Query(None, description="End date for metric"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Query a single metric with filters."""
    service = AnalyticsService(db, current_user)
    value = service.calculate_metric(
        metric=config.metric,
        start_date=start_date,
        end_date=end_date,
        filters=config.filters,
    )
    return {"metric": config.metric.value, "value": value}


@router.post("/query/time-series")
def query_time_series(
    config: TimeSeriesConfig = Body(...),
    start_date: date = Query(..., description="Start date for time series"),
    end_date: date = Query(..., description="End date for time series"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Query time series data with filters."""
    service = AnalyticsService(db, current_user)
    data = service.get_time_series(
        metric=config.metric,
        start_date=start_date,
        end_date=end_date,
        granularity=config.granularity,
        filters=config.filters,
    )
    return {
        "metric": config.metric.value,
        "granularity": config.granularity.value,
        "chart_type": config.chart_type.value,
        "data": data,
    }


@router.post("/query/breakdown")
def query_breakdown(
    config: BreakdownConfig = Body(...),
    start_date: date | None = Query(None, description="Start date for breakdown"),
    end_date: date | None = Query(None, description="End date for breakdown"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Query breakdown data with filters."""
    service = AnalyticsService(db, current_user)
    data = service.get_breakdown(
        metric=config.metric,
        group_by=config.group_by,
        start_date=start_date,
        end_date=end_date,
        limit=config.limit,
        filters=config.filters,
    )
    return {
        "metric": config.metric.value,
        "group_by": config.group_by.value,
        "chart_type": config.chart_type.value,
        "data": data,
    }
