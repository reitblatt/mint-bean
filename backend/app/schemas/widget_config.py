"""Flexible widget configuration schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Available metric types for widgets."""

    # Balance metrics
    TOTAL_BALANCE = "total_balance"
    NET_WORTH = "net_worth"

    # Transaction metrics
    TOTAL_SPENDING = "total_spending"
    TOTAL_INCOME = "total_income"
    NET_INCOME = "net_income"  # income - spending
    TRANSACTION_COUNT = "transaction_count"
    UNCATEGORIZED_COUNT = "uncategorized_count"
    ACCOUNT_COUNT = "account_count"


class FilterOperator(str, Enum):
    """Filter operators for flexible queries."""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    CONTAINS = "contains"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class FilterField(str, Enum):
    """Fields that can be filtered on."""

    CATEGORY_ID = "category_id"
    ACCOUNT_ID = "account_id"
    MERCHANT_NAME = "merchant_name"
    AMOUNT = "amount"
    DESCRIPTION = "description"
    PENDING = "pending"
    REVIEWED = "reviewed"
    PLAID_PRIMARY_CATEGORY = "plaid_primary_category"
    PLAID_DETAILED_CATEGORY = "plaid_detailed_category"


class TransactionFilter(BaseModel):
    """A single filter condition for transactions."""

    field: FilterField = Field(..., description="Field to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(None, description="Filter value (type depends on field and operator)")


class ChartType(str, Enum):
    """Types of charts available."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"


class Granularity(str, Enum):
    """Time granularity for time series."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class GroupByField(str, Enum):
    """Fields to group by for breakdowns."""

    CATEGORY = "category"
    MERCHANT = "merchant"
    ACCOUNT = "account"
    PLAID_PRIMARY_CATEGORY = "plaid_primary_category"
    PLAID_DETAILED_CATEGORY = "plaid_detailed_category"


class SummaryCardConfig(BaseModel):
    """Configuration for summary card widgets."""

    metric: MetricType = Field(..., description="Metric to display")
    filters: list[TransactionFilter] = Field(default_factory=list, description="Filters to apply")


class TimeSeriesConfig(BaseModel):
    """Configuration for time series (line/area) charts."""

    metric: MetricType = Field(..., description="Metric to plot over time")
    granularity: Granularity = Field(default=Granularity.DAILY, description="Time granularity")
    chart_type: ChartType = Field(default=ChartType.LINE, description="Chart type")
    filters: list[TransactionFilter] = Field(default_factory=list, description="Filters to apply")


class BreakdownConfig(BaseModel):
    """Configuration for breakdown charts (bar/pie)."""

    metric: MetricType = Field(
        ..., description="Metric to aggregate (e.g., total_spending, total_income)"
    )
    group_by: GroupByField = Field(..., description="Field to group by")
    chart_type: ChartType = Field(..., description="Chart type (bar or pie)")
    limit: int = Field(default=10, ge=1, le=50, description="Number of items to show")
    filters: list[TransactionFilter] = Field(default_factory=list, description="Filters to apply")


class TableConfig(BaseModel):
    """Configuration for transaction table widgets."""

    limit: int = Field(default=10, ge=1, le=100, description="Number of rows")
    sort_by: str = Field(default="date", description="Field to sort by")
    sort_desc: bool = Field(default=True, description="Sort descending")
    filters: list[TransactionFilter] = Field(default_factory=list, description="Filters to apply")
