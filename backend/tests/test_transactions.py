"""Tests for transaction endpoints and models."""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User


class TestTransactionModel:
    """Test Transaction model."""

    def test_beancount_flag_pending(self, db: Session, sample_transaction: Transaction):
        """Test beancount_flag returns '!' for pending transactions."""
        sample_transaction.pending = True
        db.commit()

        assert sample_transaction.beancount_flag == "!"

    def test_beancount_flag_completed(self, db: Session, sample_transaction: Transaction):
        """Test beancount_flag returns '*' for completed transactions."""
        sample_transaction.pending = False
        db.commit()

        assert sample_transaction.beancount_flag == "*"


class TestListTransactions:
    """Test GET /api/v1/transactions/ endpoint."""

    def test_list_empty(self, client: TestClient, auth_headers: dict):
        """Test listing transactions when none exist."""
        response = client.get("/api/v1/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["transactions"] == []
        assert data["total"] == 0

    def test_list_with_data(
        self, client: TestClient, auth_headers: dict, sample_transaction: Transaction
    ):
        """Test listing transactions with data."""
        response = client.get("/api/v1/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["id"] == sample_transaction.id
        assert data["total"] == 1

    def test_list_with_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User,
        sample_account: Account,
    ):
        """Test transaction listing with pagination."""
        # Create multiple transactions
        for i in range(15):
            txn = Transaction(
                user_id=test_user.id,
                transaction_id=f"test_txn_{i}",
                account_id=sample_account.id,
                date=datetime(2024, 3, i + 1),
                amount=-10.00 * i,
                description=f"Test transaction {i}",
                currency="USD",
                environment="sandbox",
                pending=False,
                reviewed=False,
                synced_to_beancount=False,
            )
            db.add(txn)
        db.commit()

        # Test first page
        response = client.get("/api/v1/transactions?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 10
        assert data["total"] == 15
        assert data["total_pages"] == 2

        # Test second page
        response = client.get("/api/v1/transactions?page=2&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5

    def test_list_with_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User,
        sample_account: Account,
        sample_category: Category,
    ):
        """Test transaction listing with filters."""
        # Create transactions
        txn1 = Transaction(
            user_id=test_user.id,
            transaction_id="test_txn_1",
            account_id=sample_account.id,
            category_id=sample_category.id,
            date=datetime(2024, 3, 15),
            amount=-25.50,
            description="Starbucks coffee",
            payee="Starbucks",
            currency="USD",
            environment="sandbox",
            pending=False,
            reviewed=False,
            synced_to_beancount=False,
        )
        txn2 = Transaction(
            user_id=test_user.id,
            transaction_id="test_txn_2",
            account_id=sample_account.id,
            date=datetime(2024, 4, 10),
            amount=-30.00,
            description="Gas station",
            currency="USD",
            environment="sandbox",
            pending=False,
            reviewed=False,
            synced_to_beancount=False,
        )
        db.add_all([txn1, txn2])
        db.commit()

        # Test account filter
        response = client.get(
            f"/api/v1/transactions?account_id={sample_account.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2

        # Test category filter
        response = client.get(
            f"/api/v1/transactions?category_id={sample_category.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # Test date range filter
        response = client.get(
            "/api/v1/transactions?start_date=2024-03-01&end_date=2024-03-31",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # Test search
        response = client.get("/api/v1/transactions?search=coffee", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestGetTransaction:
    """Test GET /api/v1/transactions/{transaction_id} endpoint."""

    def test_get_transaction_success(
        self, client: TestClient, auth_headers: dict, sample_transaction: Transaction
    ):
        """Test getting specific transaction."""
        response = client.get(f"/api/v1/transactions/{sample_transaction.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_transaction.id
        assert data["description"] == sample_transaction.description

    def test_get_transaction_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent transaction."""
        response = client.get("/api/v1/transactions/999", headers=auth_headers)

        assert response.status_code == 404


class TestCreateTransaction:
    """Test POST /api/v1/transactions/ endpoint."""

    def test_create_transaction_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_account: Account,
        sample_category: Category,
    ):
        """Test creating a new transaction."""
        data = {
            "account_id": sample_account.id,
            "category_id": sample_category.id,
            "date": "2024-03-20T00:00:00",
            "amount": -45.99,
            "description": "New purchase",
            "payee": "Test Store",
            "currency": "USD",
        }

        response = client.post("/api/v1/transactions", json=data, headers=auth_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["description"] == "New purchase"
        assert result["amount"] == -45.99
        assert "transaction_id" in result

    def test_create_transaction_invalid_account(self, client: TestClient, auth_headers: dict):
        """Test creating transaction with invalid account."""
        data = {
            "account_id": 999,
            "date": "2024-03-20T00:00:00",
            "amount": -45.99,
            "description": "Test",
            "currency": "USD",
        }

        response = client.post("/api/v1/transactions", json=data, headers=auth_headers)

        # Should fail due to foreign key constraint
        assert response.status_code in [400, 500]


class TestUpdateTransaction:
    """Test PATCH /api/v1/transactions/{transaction_id} endpoint."""

    def test_update_transaction_description(
        self, client: TestClient, auth_headers: dict, sample_transaction: Transaction
    ):
        """Test updating transaction description."""
        response = client.patch(
            f"/api/v1/transactions/{sample_transaction.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_transaction_category(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_transaction: Transaction,
        db: Session,
        test_user: User,
    ):
        """Test updating transaction category."""
        new_category = Category(
            user_id=test_user.id,
            name="dining",
            display_name="Dining Out",
            beancount_account="Expenses:Food:Dining",
            category_type="expense",
        )
        db.add(new_category)
        db.commit()

        response = client.patch(
            f"/api/v1/transactions/{sample_transaction.id}",
            json={"category_id": new_category.id},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == new_category.id

    def test_update_transaction_reviewed(
        self, client: TestClient, auth_headers: dict, sample_transaction: Transaction
    ):
        """Test marking transaction as reviewed."""
        response = client.patch(
            f"/api/v1/transactions/{sample_transaction.id}",
            json={"reviewed": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reviewed"] is True

    def test_update_transaction_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent transaction."""
        response = client.patch(
            "/api/v1/transactions/999", json={"description": "Updated"}, headers=auth_headers
        )

        assert response.status_code == 404


class TestDeleteTransaction:
    """Test DELETE /api/v1/transactions/{transaction_id} endpoint."""

    def test_delete_transaction_success(
        self, client: TestClient, auth_headers: dict, sample_transaction: Transaction
    ):
        """Test deleting a transaction."""
        response = client.delete(
            f"/api/v1/transactions/{sample_transaction.id}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/v1/transactions/{sample_transaction.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_transaction_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent transaction."""
        response = client.delete("/api/v1/transactions/999", headers=auth_headers)

        assert response.status_code == 404


class TestPendingTransactionWorkflow:
    """Test workflow for pending transactions."""

    def test_pending_to_completed_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User,
        sample_account: Account,
    ):
        """Test creating pending transaction and marking as completed."""
        # Create pending transaction
        data = {
            "account_id": sample_account.id,
            "date": "2024-03-20T00:00:00",
            "amount": -50.00,
            "description": "Pending purchase",
            "currency": "USD",
            "pending": True,
        }

        create_response = client.post("/api/v1/transactions", json=data, headers=auth_headers)
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]

        # Verify it's pending
        get_response = client.get(f"/api/v1/transactions/{txn_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["pending"] is True

        # Mark as completed
        update_response = client.patch(
            f"/api/v1/transactions/{txn_id}", json={"pending": False}, headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["pending"] is False
