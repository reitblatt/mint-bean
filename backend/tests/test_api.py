"""Basic API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_list_transactions() -> None:
    """Test listing transactions."""
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 200
    assert "transactions" in response.json()


def test_list_accounts() -> None:
    """Test listing accounts."""
    response = client.get("/api/v1/accounts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_categories() -> None:
    """Test listing categories."""
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_rules() -> None:
    """Test listing rules."""
    response = client.get("/api/v1/rules/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
