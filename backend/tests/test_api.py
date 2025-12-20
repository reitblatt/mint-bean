"""Basic API tests."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root(client: TestClient) -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_list_transactions(client: TestClient, auth_headers: dict) -> None:
    """Test listing transactions."""
    response = client.get("/api/v1/transactions", headers=auth_headers)
    assert response.status_code == 200
    assert "transactions" in response.json()


def test_list_accounts(client: TestClient, auth_headers: dict) -> None:
    """Test listing accounts."""
    response = client.get("/api/v1/accounts", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_categories(client: TestClient, auth_headers: dict) -> None:
    """Test listing categories."""
    response = client.get("/api/v1/categories", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_rules(client: TestClient, auth_headers: dict) -> None:
    """Test listing rules."""
    response = client.get("/api/v1/rules", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
