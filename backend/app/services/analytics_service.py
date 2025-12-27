"""Analytics service for flexible widget queries."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TypedDict

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.widget_config import (
    FilterField,
    FilterOperator,
    Granularity,
    GroupByField,
    MetricType,
    TransactionFilter,
)


class TimeSeriesDataPoint(TypedDict):
    """Type-safe structure for time series data points."""

    date: str  # ISO format date string
    value: float


class BreakdownDataPoint(TypedDict):
    """Type-safe structure for breakdown data points."""

    label: str
    value: float
    percentage: float


class AnalyticsService:
    """Service for executing flexible analytics queries."""

    def __init__(self, db: Session, user: User):
        """Initialize service with database session and user."""
        self.db = db
        self.user = user

    @staticmethod
    def _normalize_date(dt: datetime | date) -> date:
        """Convert datetime to date for consistent key matching.

        This prevents bugs where datetime objects from SQLAlchemy queries
        are used as dictionary keys but looked up with date objects.

        Args:
            dt: A datetime or date object

        Returns:
            A date object (datetime.date() if input was datetime)
        """
        if isinstance(dt, datetime):
            return dt.date()
        return dt

    def apply_filters(self, query: Query, filters: list[TransactionFilter]) -> Query:
        """Apply filters to a transaction query."""
        for filter_spec in filters:
            field = filter_spec.field
            operator = filter_spec.operator
            value = filter_spec.value

            # Get the model field
            if field == FilterField.CATEGORY_ID:
                model_field = Transaction.category_id
            elif field == FilterField.ACCOUNT_ID:
                model_field = Transaction.account_id
            elif field == FilterField.MERCHANT_NAME:
                model_field = Transaction.merchant_name
            elif field == FilterField.AMOUNT:
                model_field = Transaction.amount
            elif field == FilterField.DESCRIPTION:
                model_field = Transaction.description
            elif field == FilterField.PENDING:
                model_field = Transaction.pending
            elif field == FilterField.REVIEWED:
                model_field = Transaction.reviewed
            elif field == FilterField.PLAID_PRIMARY_CATEGORY:
                model_field = Transaction.plaid_primary_category
            elif field == FilterField.PLAID_DETAILED_CATEGORY:
                model_field = Transaction.plaid_detailed_category
            else:
                continue  # Skip unknown fields

            # Apply operator
            if operator == FilterOperator.EQUALS:
                query = query.filter(model_field == value)
            elif operator == FilterOperator.NOT_EQUALS:
                query = query.filter(model_field != value)
            elif operator == FilterOperator.IN:
                if isinstance(value, list):
                    query = query.filter(model_field.in_(value))
            elif operator == FilterOperator.NOT_IN:
                if isinstance(value, list):
                    query = query.filter(~model_field.in_(value))
            elif operator == FilterOperator.GREATER_THAN:
                query = query.filter(model_field > value)
            elif operator == FilterOperator.LESS_THAN:
                query = query.filter(model_field < value)
            elif operator == FilterOperator.CONTAINS:
                if isinstance(value, str):
                    query = query.filter(model_field.contains(value))
            elif operator == FilterOperator.IS_NULL:
                query = query.filter(model_field.is_(None))
            elif operator == FilterOperator.IS_NOT_NULL:
                query = query.filter(model_field.isnot(None))

        return query

    def calculate_metric(
        self,
        metric: MetricType,
        start_date: date | None = None,
        end_date: date | None = None,
        filters: list[TransactionFilter] | None = None,
    ) -> float:
        """Calculate a single metric value."""
        filters = filters or []

        if metric == MetricType.TOTAL_BALANCE:
            # Total balance is sum of all account balances (no date filter)
            return (
                self.db.query(func.sum(Account.current_balance))
                .filter(Account.user_id == self.user.id)
                .scalar()
                or 0.0
            )

        elif metric == MetricType.NET_WORTH:
            # Net worth = total balance (for now, could include other assets)
            return (
                self.db.query(func.sum(Account.current_balance))
                .filter(Account.user_id == self.user.id)
                .scalar()
                or 0.0
            )

        elif metric == MetricType.TOTAL_SPENDING:
            query = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == self.user.id, Transaction.amount < 0
            )
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            query = self.apply_filters(query, filters)
            result = query.scalar() or 0.0
            return abs(result)

        elif metric == MetricType.TOTAL_INCOME:
            query = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == self.user.id, Transaction.amount > 0
            )
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            query = self.apply_filters(query, filters)
            return query.scalar() or 0.0

        elif metric == MetricType.NET_INCOME:
            # Net income = income - spending
            income = self.calculate_metric(MetricType.TOTAL_INCOME, start_date, end_date, filters)
            spending = self.calculate_metric(
                MetricType.TOTAL_SPENDING, start_date, end_date, filters
            )
            return income - spending

        elif metric == MetricType.TRANSACTION_COUNT:
            query = self.db.query(func.count(Transaction.id)).filter(
                Transaction.user_id == self.user.id
            )
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            query = self.apply_filters(query, filters)
            return float(query.scalar() or 0)

        elif metric == MetricType.UNCATEGORIZED_COUNT:
            query = self.db.query(func.count(Transaction.id)).filter(
                Transaction.user_id == self.user.id,
                Transaction.category_id.is_(None),
            )
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            query = self.apply_filters(query, filters)
            return float(query.scalar() or 0)

        elif metric == MetricType.ACCOUNT_COUNT:
            return float(
                self.db.query(func.count(Account.id))
                .filter(Account.user_id == self.user.id)
                .scalar()
                or 0
            )

        return 0.0

    def get_time_series(
        self,
        metric: MetricType,
        start_date: date,
        end_date: date,
        granularity: Granularity = Granularity.DAILY,
        filters: list[TransactionFilter] | None = None,
    ) -> list[TimeSeriesDataPoint]:
        """Get time series data for a metric.

        Returns:
            List of data points with ISO date strings and float values.
            Dates from SQLAlchemy are normalized to prevent datetime/date mismatches.
        """
        filters = filters or []
        data_points: list[TimeSeriesDataPoint] = []

        # For balance-based metrics, we need to calculate cumulative balance
        if metric in [MetricType.TOTAL_BALANCE, MetricType.NET_WORTH]:
            # Get starting balance
            current_balance = (
                self.db.query(func.sum(Account.current_balance))
                .filter(Account.user_id == self.user.id)
                .scalar()
                or 0.0
            )

            # Get all transactions since start_date to calculate historical balances
            # This is a simplified approach - for production, you'd want to store balance snapshots
            transactions = (
                self.db.query(Transaction.date, func.sum(Transaction.amount))
                .filter(
                    Transaction.user_id == self.user.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                )
                .group_by(Transaction.date)
                .order_by(Transaction.date.desc())
                .all()
            )

            # Calculate balance by working backwards from current
            balance_by_date = {}
            running_balance = current_balance
            for tx_date, total in transactions:
                running_balance -= total  # Subtract to go backwards
                balance_by_date[tx_date] = running_balance

            # Create data points
            current_date = start_date
            while current_date <= end_date:
                # Find balance for this date (or closest previous date)
                balance = current_balance
                temp_date = current_date
                while temp_date >= start_date:
                    if temp_date in balance_by_date:
                        balance = balance_by_date[temp_date]
                        break
                    temp_date -= timedelta(days=1)

                data_points.append({"date": current_date.isoformat(), "value": balance})

                # Increment based on granularity
                if granularity == Granularity.DAILY:
                    current_date += timedelta(days=1)
                elif granularity == Granularity.WEEKLY:
                    current_date += timedelta(weeks=1)
                elif granularity == Granularity.MONTHLY:
                    # Move to next month
                    if current_date.month == 12:
                        current_date = date(current_date.year + 1, 1, 1)
                    else:
                        current_date = date(current_date.year, current_date.month + 1, 1)
                elif granularity == Granularity.YEARLY:
                    current_date = date(current_date.year + 1, 1, 1)

        else:
            # For transaction-based metrics, aggregate by time period
            # Determine amount filter based on metric
            amount_filter = None
            if metric == MetricType.TOTAL_SPENDING:
                amount_filter = Transaction.amount < 0
            elif metric == MetricType.TOTAL_INCOME:
                amount_filter = Transaction.amount > 0

            query = self.db.query(
                Transaction.date, func.sum(Transaction.amount).label("total")
            ).filter(Transaction.user_id == self.user.id)

            if amount_filter is not None:
                query = query.filter(amount_filter)

            query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
            query = self.apply_filters(query, filters)
            query = query.group_by(Transaction.date).order_by(Transaction.date)

            transactions = query.all()

            # Convert to dict for easy lookup (normalize datetime to date for key matching)
            data_by_date: dict[date, float] = {
                self._normalize_date(tx_date): total for tx_date, total in transactions
            }

            # Create data points for each time period
            current_date = start_date
            while current_date <= end_date:
                value = data_by_date.get(current_date, 0.0)
                if metric == MetricType.TOTAL_SPENDING:
                    value = abs(value)

                data_points.append({"date": current_date.isoformat(), "value": value})

                # Increment based on granularity
                if granularity == Granularity.DAILY:
                    current_date += timedelta(days=1)
                elif granularity == Granularity.WEEKLY:
                    current_date += timedelta(weeks=1)
                elif granularity == Granularity.MONTHLY:
                    if current_date.month == 12:
                        current_date = date(current_date.year + 1, 1, 1)
                    else:
                        current_date = date(current_date.year, current_date.month + 1, 1)
                elif granularity == Granularity.YEARLY:
                    current_date = date(current_date.year + 1, 1, 1)

        return data_points

    def get_breakdown(
        self,
        metric: MetricType,
        group_by: GroupByField,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
        filters: list[TransactionFilter] | None = None,
    ) -> list[BreakdownDataPoint]:
        """Get breakdown data grouped by a field.

        Returns:
            List of breakdown data points with label, value, and percentage.
        """
        filters = filters or []

        # Determine amount filter based on metric
        amount_filter = None
        if metric == MetricType.TOTAL_SPENDING:
            amount_filter = Transaction.amount < 0
        elif metric == MetricType.TOTAL_INCOME:
            amount_filter = Transaction.amount > 0

        # Determine group by field
        if group_by == GroupByField.CATEGORY:
            group_field = Transaction.category_id
        elif group_by == GroupByField.MERCHANT:
            group_field = Transaction.merchant_name
        elif group_by == GroupByField.ACCOUNT:
            group_field = Transaction.account_id
        elif group_by == GroupByField.PLAID_PRIMARY_CATEGORY:
            group_field = Transaction.plaid_primary_category
        elif group_by == GroupByField.PLAID_DETAILED_CATEGORY:
            group_field = Transaction.plaid_detailed_category
        else:
            return []

        # Build query
        query = self.db.query(group_field, func.sum(Transaction.amount).label("total")).filter(
            Transaction.user_id == self.user.id
        )

        if amount_filter is not None:
            query = query.filter(amount_filter)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        query = self.apply_filters(query, filters)
        query = query.group_by(group_field)

        # Order by total (descending for spending, ascending for income)
        if metric == MetricType.TOTAL_SPENDING:
            query = query.order_by(func.sum(Transaction.amount).asc())
        else:
            query = query.order_by(func.sum(Transaction.amount).desc())

        query = query.limit(limit)
        results = query.all()

        # Calculate total for percentages
        total_amount = sum(abs(total) for _, total in results)

        # Build breakdown data
        breakdown: list[BreakdownDataPoint] = []
        for group_value, total in results:
            # Get label for the group
            label = str(group_value or "Unknown")
            if group_by == GroupByField.CATEGORY and group_value:
                category = self.db.query(Category).filter(Category.id == group_value).first()
                label = category.display_name if category else "Unknown"
            elif group_by == GroupByField.CATEGORY and not group_value:
                label = "Uncategorized"
            elif group_by == GroupByField.ACCOUNT and group_value:
                account = self.db.query(Account).filter(Account.id == group_value).first()
                label = account.name if account else "Unknown"

            amount = abs(total)
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0

            breakdown.append(
                {
                    "label": label,
                    "value": amount,
                    "percentage": percentage,
                }
            )

        return breakdown
