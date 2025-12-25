"""Analytics schemas for API requests/responses."""

from datetime import date as date_type

from pydantic import BaseModel, Field


class SummaryMetrics(BaseModel):
    """Summary metrics for dashboard summary cards."""

    total_balance: float = Field(..., description="Total account balance")
    total_spending: float = Field(..., description="Total spending in period")
    total_income: float = Field(..., description="Total income in period")
    transaction_count: int = Field(..., description="Number of transactions in period")
    uncategorized_count: int = Field(..., description="Number of uncategorized transactions")
    account_count: int = Field(..., description="Number of active accounts")


class TimeSeriesDataPoint(BaseModel):
    """Single data point in a time series."""

    date: date_type = Field(..., description="Date of data point")
    value: float = Field(..., description="Value for this date")
    label: str | None = Field(None, description="Optional display label")


class TimeSeriesResponse(BaseModel):
    """Time series data response."""

    data: list[TimeSeriesDataPoint] = Field(..., description="Time series data points")
    granularity: str = Field(..., description="Data granularity (daily, weekly, monthly)")


class CategoryBreakdown(BaseModel):
    """Breakdown of spending/income by category."""

    category_id: int | None = Field(..., description="Category ID (null for uncategorized)")
    category_name: str = Field(..., description="Category name")
    amount: float = Field(..., description="Total amount for category")
    transaction_count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total")


class CategoryBreakdownResponse(BaseModel):
    """Category breakdown response."""

    data: list[CategoryBreakdown] = Field(..., description="Category breakdown data")
    total_amount: float = Field(..., description="Total amount across all categories")


class MerchantBreakdown(BaseModel):
    """Breakdown of spending by merchant."""

    merchant_name: str = Field(..., description="Merchant name")
    amount: float = Field(..., description="Total amount for merchant")
    transaction_count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total")


class MerchantBreakdownResponse(BaseModel):
    """Merchant breakdown response."""

    data: list[MerchantBreakdown] = Field(..., description="Merchant breakdown data")
    total_amount: float = Field(..., description="Total amount across all merchants")
