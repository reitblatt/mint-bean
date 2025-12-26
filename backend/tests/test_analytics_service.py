"""Tests for analytics service with empty data."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.widget_config import MetricType
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = User(id=1, email="test@example.com", hashed_password="hashed")
    return user


@pytest.fixture
def mock_db(mocker):
    """Create a mock database session."""
    return mocker.Mock(spec=Session)


def test_calculate_metric_with_empty_data(mock_db, mock_user):
    """Test that calculate_metric handles empty data gracefully."""
    # Mock empty query results
    mock_db.query.return_value.filter.return_value.scalar.return_value = None

    service = AnalyticsService(mock_db, mock_user)

    # Test balance metrics return 0.0 for empty data
    result = service.calculate_metric(
        metric=MetricType.TOTAL_BALANCE,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        filters=[],
    )

    assert result == 0.0


def test_calculate_metric_total_spending_empty(mock_db, mock_user):
    """Test total spending with no transactions."""
    # Mock the entire chain for spending queries (multiple filters)
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = (
        None
    )

    service = AnalyticsService(mock_db, mock_user)

    result = service.calculate_metric(
        metric=MetricType.TOTAL_SPENDING,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        filters=[],
    )

    assert result == 0.0


def test_calculate_metric_total_income_empty(mock_db, mock_user):
    """Test total income with no transactions."""
    # Mock the entire chain for income queries (multiple filters)
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = (
        None
    )

    service = AnalyticsService(mock_db, mock_user)

    result = service.calculate_metric(
        metric=MetricType.TOTAL_INCOME,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        filters=[],
    )

    assert result == 0.0


def test_get_breakdown_with_empty_data(mock_db, mock_user):
    """Test breakdown query with no transactions."""
    # Mock the query chain for breakdown - need to return [] for .all()
    mock_query = mock_db.query.return_value
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []

    service = AnalyticsService(mock_db, mock_user)

    from app.schemas.widget_config import GroupByField

    result = service.get_breakdown(
        metric=MetricType.TOTAL_SPENDING,
        group_by=GroupByField.CATEGORY,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        limit=10,
        filters=[],
    )

    assert result == []


def test_get_time_series_with_empty_data(mock_db, mock_user):
    """Test time series query with no transactions."""
    # Mock the query chain for time series - need to return [] for .all()
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    service = AnalyticsService(mock_db, mock_user)

    from app.schemas.widget_config import Granularity

    result = service.get_time_series(
        metric=MetricType.TOTAL_SPENDING,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        granularity=Granularity.DAILY,
        filters=[],
    )

    # Should return data points for each day with 0 values
    assert len(result) == 3
    assert result[0]["date"] == "2025-01-01"
    assert result[0]["value"] == 0.0
