"""
Integration test suite for the Finance Tracker API.

Requirements: pip install httpx pytest

Run:
    pytest test_api.py -v
    # or
    python test_api.py
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# ─── In-memory test database ─────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_finance.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=test_engine)
client = TestClient(app)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    """Drop and recreate all tables before each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


def create_user(name, email, role="viewer"):
    return client.post("/api/users/", json={"name": name, "email": email, "role": role})


def make_admin():
    r = create_user("Admin User", "admin@test.com", "admin")
    assert r.status_code == 201
    return r.json()["id"]


def make_analyst():
    r = create_user("Analyst User", "analyst@test.com", "analyst")
    assert r.status_code == 201
    return r.json()["id"]


def make_viewer():
    r = create_user("Viewer User", "viewer@test.com", "viewer")
    assert r.status_code == 201
    return r.json()["id"]


# ─── User Tests ───────────────────────────────────────────────────────────────

class TestUsers:
    def test_create_user_success(self):
        r = create_user("Alice", "alice@test.com", "admin")
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "alice@test.com"
        assert data["role"] == "admin"

    def test_create_user_duplicate_email(self):
        create_user("Alice", "alice@test.com")
        r = create_user("Alice 2", "alice@test.com")
        assert r.status_code == 409

    def test_create_user_invalid_email(self):
        r = client.post("/api/users/", json={"name": "Bad", "email": "not-an-email", "role": "viewer"})
        assert r.status_code == 422

    def test_create_user_empty_name(self):
        r = client.post("/api/users/", json={"name": "   ", "email": "x@test.com", "role": "viewer"})
        assert r.status_code == 422

    def test_get_user(self):
        uid = make_viewer()
        r = client.get(f"/api/users/{uid}")
        assert r.status_code == 200
        assert r.json()["id"] == uid

    def test_get_user_not_found(self):
        r = client.get("/api/users/9999")
        assert r.status_code == 404

    def test_list_users(self):
        make_admin()
        make_viewer()
        r = client.get("/api/users/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_update_user_as_admin(self):
        admin_id = make_admin()
        viewer_id = make_viewer()
        r = client.patch(
            f"/api/users/{viewer_id}?requesting_user_id={admin_id}",
            json={"role": "analyst"},
        )
        assert r.status_code == 200
        assert r.json()["role"] == "analyst"

    def test_update_user_as_viewer_forbidden(self):
        viewer_id = make_viewer()
        r = client.patch(
            f"/api/users/{viewer_id}?requesting_user_id={viewer_id}",
            json={"role": "admin"},
        )
        assert r.status_code == 403

    def test_delete_user_as_admin(self):
        admin_id = make_admin()
        viewer_id = make_viewer()
        r = client.delete(f"/api/users/{viewer_id}?requesting_user_id={admin_id}")
        assert r.status_code == 200
        assert client.get(f"/api/users/{viewer_id}").status_code == 404

    def test_delete_user_as_non_admin_forbidden(self):
        make_admin()
        viewer_id = make_viewer()
        r = client.delete(f"/api/users/{viewer_id}?requesting_user_id={viewer_id}")
        assert r.status_code == 403


# ─── Transaction Tests ────────────────────────────────────────────────────────

def create_txn(admin_id, user_id, amount=100.0, txn_type="income", category="Salary"):
    return client.post(
        f"/api/transactions/?requesting_user_id={admin_id}",
        json={
            "amount": amount,
            "type": txn_type,
            "category": category,
            "date": "2026-03-15",
            "notes": "test",
            "user_id": user_id,
        },
    )


class TestTransactions:
    def test_create_transaction_as_admin(self):
        admin_id = make_admin()
        r = create_txn(admin_id, admin_id)
        assert r.status_code == 201
        assert r.json()["amount"] == 100.0

    def test_create_transaction_as_viewer_forbidden(self):
        admin_id = make_admin()
        viewer_id = make_viewer()
        r = client.post(
            f"/api/transactions/?requesting_user_id={viewer_id}",
            json={"amount": 50, "type": "income", "category": "X", "date": "2026-01-01", "user_id": admin_id},
        )
        assert r.status_code == 403

    def test_create_transaction_negative_amount(self):
        admin_id = make_admin()
        r = client.post(
            f"/api/transactions/?requesting_user_id={admin_id}",
            json={"amount": -50, "type": "income", "category": "X", "date": "2026-01-01", "user_id": admin_id},
        )
        assert r.status_code == 422

    def test_create_transaction_zero_amount(self):
        admin_id = make_admin()
        r = client.post(
            f"/api/transactions/?requesting_user_id={admin_id}",
            json={"amount": 0, "type": "expense", "category": "X", "date": "2026-01-01", "user_id": admin_id},
        )
        assert r.status_code == 422

    def test_list_transactions_as_viewer(self):
        admin_id = make_admin()
        viewer_id = make_viewer()
        create_txn(admin_id, admin_id, 200, "income", "Salary")
        create_txn(admin_id, viewer_id, 50, "expense", "Food")
        r = client.get(f"/api/transactions/?requesting_user_id={viewer_id}")
        assert r.status_code == 200
        assert len(r.json()) == 2  # viewers see all

    def test_filter_transactions_as_analyst(self):
        admin_id = make_admin()
        analyst_id = make_analyst()
        create_txn(admin_id, admin_id, 500, "income", "Salary")
        create_txn(admin_id, admin_id, 100, "expense", "Food")
        r = client.get(f"/api/transactions/?requesting_user_id={analyst_id}&type=expense")
        assert r.status_code == 200
        results = r.json()
        assert all(t["type"] == "expense" for t in results)

    def test_filter_by_date_range(self):
        admin_id = make_admin()
        analyst_id = make_analyst()
        create_txn(admin_id, admin_id)
        r = client.get(
            f"/api/transactions/?requesting_user_id={analyst_id}&date_from=2026-03-01&date_to=2026-03-31"
        )
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_update_transaction_as_admin(self):
        admin_id = make_admin()
        txn_id = create_txn(admin_id, admin_id).json()["id"]
        r = client.patch(
            f"/api/transactions/{txn_id}?requesting_user_id={admin_id}",
            json={"amount": 999.99, "category": "Bonus"},
        )
        assert r.status_code == 200
        assert r.json()["amount"] == 999.99
        assert r.json()["category"] == "Bonus"

    def test_delete_transaction_as_admin(self):
        admin_id = make_admin()
        txn_id = create_txn(admin_id, admin_id).json()["id"]
        r = client.delete(f"/api/transactions/{txn_id}?requesting_user_id={admin_id}")
        assert r.status_code == 200
        assert client.get(f"/api/transactions/{txn_id}").status_code == 404

    def test_get_transaction_not_found(self):
        r = client.get("/api/transactions/99999")
        assert r.status_code == 404


# ─── Summary Tests ────────────────────────────────────────────────────────────

class TestSummary:
    def test_summary_as_viewer(self):
        admin_id = make_admin()
        viewer_id = make_viewer()
        create_txn(admin_id, admin_id, 1000, "income", "Salary")
        create_txn(admin_id, admin_id, 200, "expense", "Food")
        r = client.get(f"/api/summary/?requesting_user_id={viewer_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["total_income"] == 1000.0
        assert data["total_expenses"] == 200.0
        assert data["current_balance"] == 800.0
        assert data["category_breakdown"] == []  # viewers don't get this

    def test_summary_as_analyst_has_category_breakdown(self):
        admin_id = make_admin()
        analyst_id = make_analyst()
        create_txn(admin_id, admin_id, 500, "income", "Salary")
        create_txn(admin_id, admin_id, 100, "expense", "Food")
        r = client.get(f"/api/summary/?requesting_user_id={analyst_id}")
        assert r.status_code == 200
        data = r.json()
        assert len(data["category_breakdown"]) > 0

    def test_summary_has_monthly_totals(self):
        admin_id = make_admin()
        create_txn(admin_id, admin_id, 1500, "income", "Salary")
        r = client.get(f"/api/summary/?requesting_user_id={admin_id}")
        assert r.status_code == 200
        assert len(r.json()["monthly_totals"]) >= 1

    def test_summary_has_recent_transactions(self):
        admin_id = make_admin()
        for i in range(5):
            create_txn(admin_id, admin_id, 100 + i, "income", "Test")
        r = client.get(f"/api/summary/?requesting_user_id={admin_id}")
        assert r.status_code == 200
        assert len(r.json()["recent_transactions"]) == 5


# ─── Run directly ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess, sys
    result = subprocess.run(["pytest", __file__, "-v"], capture_output=False)
    sys.exit(result.returncode)
