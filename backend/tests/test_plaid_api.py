"""Tests for Plaid API endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.plaid_item import PlaidItem


class TestCreateLinkToken:
    """Test POST /api/v1/plaid/link/token/create endpoint."""

    @patch("app.api.v1.plaid.plaid_service")
    def test_create_link_token_success(self, mock_service, client: TestClient):
        """Test successful link token creation."""
        mock_service.create_link_token.return_value = {
            "link_token": "link-sandbox-test-token",
            "expiration": "2024-12-31T23:59:59",
        }

        response = client.post("/api/v1/plaid/link/token/create", json={"user_id": "user-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["link_token"] == "link-sandbox-test-token"
        assert "expiration" in data

    @patch("app.api.v1.plaid.plaid_service")
    def test_create_link_token_no_credentials(self, mock_service, client: TestClient):
        """Test link token creation with no Plaid credentials."""
        mock_service.create_link_token.side_effect = ValueError("not initialized")

        response = client.post("/api/v1/plaid/link/token/create", json={"user_id": "user-123"})

        assert response.status_code == 503


class TestExchangePublicToken:
    """Test POST /api/v1/plaid/item/public_token/exchange endpoint."""

    @patch("app.api.v1.plaid.plaid_service")
    def test_exchange_token_success(
        self, mock_service, client: TestClient, sample_plaid_item: PlaidItem
    ):
        """Test successful token exchange."""
        mock_service.exchange_public_token.return_value = sample_plaid_item

        response = client.post(
            "/api/v1/plaid/item/public_token/exchange",
            json={"public_token": "public-sandbox-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == sample_plaid_item.item_id
        assert data["institution_name"] == sample_plaid_item.institution_name

    @patch("app.api.v1.plaid.plaid_service")
    def test_exchange_token_error(self, mock_service, client: TestClient):
        """Test token exchange with error."""
        mock_service.exchange_public_token.side_effect = Exception("Plaid API error")

        response = client.post(
            "/api/v1/plaid/item/public_token/exchange", json={"public_token": "invalid-token"}
        )

        assert response.status_code == 500


class TestListPlaidItems:
    """Test GET /api/v1/plaid/items endpoint."""

    def test_list_items_empty(self, client: TestClient):
        """Test listing items when none exist."""
        response = client.get("/api/v1/plaid/items")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_items_with_data(self, client: TestClient, sample_plaid_item: PlaidItem):
        """Test listing items with data."""
        response = client.get("/api/v1/plaid/items")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["item_id"] == sample_plaid_item.item_id
        assert data[0]["institution_name"] == sample_plaid_item.institution_name
        assert data[0]["is_active"] is True


class TestGetPlaidItem:
    """Test GET /api/v1/plaid/items/{item_id} endpoint."""

    def test_get_item_success(self, client: TestClient, sample_plaid_item: PlaidItem):
        """Test getting specific item."""
        response = client.get(f"/api/v1/plaid/items/{sample_plaid_item.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_plaid_item.id
        assert data["item_id"] == sample_plaid_item.item_id

    def test_get_item_not_found(self, client: TestClient):
        """Test getting non-existent item."""
        response = client.get("/api/v1/plaid/items/999")

        assert response.status_code == 404


class TestSyncTransactions:
    """Test POST /api/v1/plaid/items/{item_id}/sync endpoint."""

    @patch("app.api.v1.plaid.plaid_service")
    def test_sync_success(self, mock_service, client: TestClient, sample_plaid_item: PlaidItem):
        """Test successful transaction sync."""
        mock_service.sync_transactions.return_value = (5, 2, 1, "cursor_123")

        response = client.post(f"/api/v1/plaid/items/{sample_plaid_item.id}/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == 5
        assert data["modified"] == 2
        assert data["removed"] == 1
        assert data["cursor"] == "cursor_123"

    def test_sync_item_not_found(self, client: TestClient):
        """Test sync with non-existent item."""
        response = client.post("/api/v1/plaid/items/999/sync")

        assert response.status_code == 404

    def test_sync_inactive_item(
        self, client: TestClient, sample_plaid_item: PlaidItem, db: Session
    ):
        """Test sync with inactive item."""
        sample_plaid_item.is_active = False
        db.commit()

        response = client.post(f"/api/v1/plaid/items/{sample_plaid_item.id}/sync")

        assert response.status_code == 400

    @patch("app.api.v1.plaid.plaid_service")
    def test_sync_error(self, mock_service, client: TestClient, sample_plaid_item: PlaidItem):
        """Test sync with Plaid API error."""
        mock_service.sync_transactions.side_effect = Exception("Plaid API error")

        response = client.post(f"/api/v1/plaid/items/{sample_plaid_item.id}/sync")

        assert response.status_code == 500


class TestDeletePlaidItem:
    """Test DELETE /api/v1/plaid/items/{item_id} endpoint."""

    def test_delete_item_success(
        self, client: TestClient, sample_plaid_item: PlaidItem, db: Session
    ):
        """Test successful item deletion (deactivation)."""
        response = client.delete(f"/api/v1/plaid/items/{sample_plaid_item.id}")

        assert response.status_code == 204

        # Verify item is deactivated, not deleted
        db.refresh(sample_plaid_item)
        assert sample_plaid_item.is_active is False

    def test_delete_item_not_found(self, client: TestClient):
        """Test deleting non-existent item."""
        response = client.delete("/api/v1/plaid/items/999")

        assert response.status_code == 404


class TestEndToEndPlaidFlow:
    """E2E tests for complete Plaid integration flow."""

    @patch("app.api.v1.plaid.plaid_service")
    def test_complete_plaid_flow(self, mock_service, client: TestClient, db: Session):
        """Test complete flow: link token → exchange → sync."""
        # Step 1: Create link token
        mock_service.create_link_token.return_value = {
            "link_token": "link-sandbox-test",
            "expiration": "2024-12-31T23:59:59",
        }

        link_response = client.post(
            "/api/v1/plaid/link/token/create", json={"user_id": "test-user"}
        )
        assert link_response.status_code == 200
        assert "link_token" in link_response.json()

        # Step 2: Exchange public token
        plaid_item = PlaidItem(
            item_id="item_test_123",
            access_token="access-test-token",
            institution_id="ins_test",
            institution_name="Test Bank",
            is_active=True,
        )
        db.add(plaid_item)
        db.commit()
        db.refresh(plaid_item)

        mock_service.exchange_public_token.return_value = plaid_item

        exchange_response = client.post(
            "/api/v1/plaid/item/public_token/exchange", json={"public_token": "public-test-token"}
        )
        assert exchange_response.status_code == 200
        item_data = exchange_response.json()
        assert item_data["item_id"] == "item_test_123"

        # Step 3: Verify item appears in list
        list_response = client.get("/api/v1/plaid/items")
        assert list_response.status_code == 200
        items = list_response.json()
        assert len(items) == 1
        assert items[0]["institution_name"] == "Test Bank"

        # Step 4: Sync transactions
        mock_service.sync_transactions.return_value = (10, 2, 0, "cursor_abc")

        sync_response = client.post(f"/api/v1/plaid/items/{plaid_item.id}/sync")
        assert sync_response.status_code == 200
        sync_data = sync_response.json()
        assert sync_data["added"] == 10
        assert sync_data["modified"] == 2

        # Step 5: Disconnect (deactivate)
        delete_response = client.delete(f"/api/v1/plaid/items/{plaid_item.id}")
        assert delete_response.status_code == 204

        # Verify item is deactivated
        db.refresh(plaid_item)
        assert plaid_item.is_active is False
