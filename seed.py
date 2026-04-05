from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models


SEED_USERS = [
    {"name": "Alice Admin", "email": "alice@example.com", "role": models.Role.admin},
    {"name": "Bob Analyst", "email": "bob@example.com", "role": models.Role.analyst},
    {"name": "Carol Viewer", "email": "carol@example.com", "role": models.Role.viewer},
]

SEED_TRANSACTIONS = [
    # Income
    {"amount": 5000.00, "type": models.TransactionType.income, "category": "Salary", "date": date.today() - timedelta(days=60), "notes": "Monthly salary", "user_id": 1},
    {"amount": 5000.00, "type": models.TransactionType.income, "category": "Salary", "date": date.today() - timedelta(days=30), "notes": "Monthly salary", "user_id": 1},
    {"amount": 5000.00, "type": models.TransactionType.income, "category": "Salary", "date": date.today() - timedelta(days=1), "notes": "Monthly salary", "user_id": 1},
    {"amount": 800.00, "type": models.TransactionType.income, "category": "Freelance", "date": date.today() - timedelta(days=45), "notes": "Design project", "user_id": 2},
    {"amount": 1200.00, "type": models.TransactionType.income, "category": "Freelance", "date": date.today() - timedelta(days=15), "notes": "Web project", "user_id": 2},
    {"amount": 300.00, "type": models.TransactionType.income, "category": "Dividends", "date": date.today() - timedelta(days=20), "notes": "Stock dividends", "user_id": 1},
    # Expenses
    {"amount": 1200.00, "type": models.TransactionType.expense, "category": "Rent", "date": date.today() - timedelta(days=58), "notes": "Monthly rent", "user_id": 1},
    {"amount": 1200.00, "type": models.TransactionType.expense, "category": "Rent", "date": date.today() - timedelta(days=28), "notes": "Monthly rent", "user_id": 1},
    {"amount": 350.00, "type": models.TransactionType.expense, "category": "Groceries", "date": date.today() - timedelta(days=55), "notes": "Supermarket", "user_id": 1},
    {"amount": 280.00, "type": models.TransactionType.expense, "category": "Groceries", "date": date.today() - timedelta(days=25), "notes": "Supermarket", "user_id": 2},
    {"amount": 120.00, "type": models.TransactionType.expense, "category": "Utilities", "date": date.today() - timedelta(days=50), "notes": "Electricity bill", "user_id": 1},
    {"amount": 95.00, "type": models.TransactionType.expense, "category": "Utilities", "date": date.today() - timedelta(days=20), "notes": "Internet", "user_id": 2},
    {"amount": 450.00, "type": models.TransactionType.expense, "category": "Transport", "date": date.today() - timedelta(days=40), "notes": "Flight ticket", "user_id": 1},
    {"amount": 85.00, "type": models.TransactionType.expense, "category": "Transport", "date": date.today() - timedelta(days=10), "notes": "Fuel", "user_id": 2},
    {"amount": 200.00, "type": models.TransactionType.expense, "category": "Entertainment", "date": date.today() - timedelta(days=35), "notes": "Streaming + dining", "user_id": 1},
    {"amount": 500.00, "type": models.TransactionType.expense, "category": "Healthcare", "date": date.today() - timedelta(days=22), "notes": "Dental visit", "user_id": 3},
    {"amount": 150.00, "type": models.TransactionType.expense, "category": "Education", "date": date.today() - timedelta(days=12), "notes": "Online course", "user_id": 2},
]


def run_seed():
    db: Session = SessionLocal()
    try:
        # Only seed if DB is empty
        if db.query(models.User).count() > 0:
            return

        for u in SEED_USERS:
            db.add(models.User(**u))
        db.commit()

        for t in SEED_TRANSACTIONS:
            db.add(models.Transaction(**t))
        db.commit()

        print("✅ Seed data loaded successfully.")
    except Exception as e:
        db.rollback()
        print(f"⚠️  Seed failed: {e}")
    finally:
        db.close()
