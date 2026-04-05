# 💰 Finance Tracker API

A Python-powered finance tracking system built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

---

## 🚀 Quick Start

### 1. Create & activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

### 4. Open the interactive API docs

```
http://127.0.0.1:8000/docs
```

The database is created automatically on first run, and seed data (3 users + 17 transactions) is loaded so you can explore immediately.

---

## 🗂 Project Structure

```
finance-tracker/
├── app/
│   ├── main.py              # FastAPI app, middleware, router registration
│   ├── database.py          # SQLAlchemy engine & session
│   ├── models.py            # ORM models: User, Transaction
│   ├── schemas.py           # Pydantic schemas: validation & serialization
│   ├── seed.py              # Demo seed data
│   ├── routers/
│   │   ├── users.py         # /api/users endpoints
│   │   ├── transactions.py  # /api/transactions endpoints
│   │   └── summary.py       # /api/summary endpoint
│   └── services/
│       ├── user_service.py        # User CRUD + role enforcement
│       ├── transaction_service.py # Transaction CRUD + filters
│       └── summary_service.py     # Analytics & financial summaries
├── requirements.txt
└── README.md
```

---

## 👥 User Roles

| Role     | Permissions |
|----------|-------------|
| `viewer`   | View transactions and basic summary |
| `analyst`  | View + filter transactions, access category breakdown |
| `admin`    | Full access: create, update, delete records and users |

Role is passed via the `requesting_user_id` query parameter. The system looks up the user's role from the database and enforces access accordingly.

---

## 🌱 Seed Users (auto-created on first run)

| ID | Name          | Email              | Role     |
|----|---------------|--------------------|----------|
| 1  | Alice Admin   | alice@example.com  | admin    |
| 2  | Bob Analyst   | bob@example.com    | analyst  |
| 3  | Carol Viewer  | carol@example.com  | viewer   |

---

## 📡 API Endpoints

### Users — `/api/users`

| Method | Path               | Description               | Role Required |
|--------|--------------------|---------------------------|---------------|
| POST   | `/`                | Create a new user         | Anyone        |
| GET    | `/`                | List all users            | Anyone        |
| GET    | `/{user_id}`       | Get user by ID            | Anyone        |
| PATCH  | `/{user_id}`       | Update user               | Admin         |
| DELETE | `/{user_id}`       | Delete user               | Admin         |

### Transactions — `/api/transactions`

| Method | Path                    | Description              | Role Required     |
|--------|-------------------------|--------------------------|-------------------|
| POST   | `/`                     | Create a transaction     | Admin             |
| GET    | `/`                     | List/filter transactions | Viewer+           |
| GET    | `/{transaction_id}`     | Get transaction by ID    | Anyone            |
| PATCH  | `/{transaction_id}`     | Update transaction       | Admin             |
| DELETE | `/{transaction_id}`     | Delete transaction       | Admin             |

**Filter parameters** (for analysts/admins):
- `type` — `income` or `expense`
- `category` — partial text match
- `date_from` / `date_to` — date range (YYYY-MM-DD)
- `user_id` — filter by a specific user

### Summary — `/api/summary`

| Method | Path | Description                     | Role Required |
|--------|------|---------------------------------|---------------|
| GET    | `/`  | Get full financial summary      | Viewer+       |

**Response includes:**
- Total income, total expenses, current balance
- Transaction count
- Category-wise breakdown *(analyst/admin only)*
- Monthly totals (income, expense, net)
- 10 most recent transactions

---

## 📋 Example Requests

### Create a transaction (admin)
```bash
curl -X POST "http://localhost:8000/api/transactions/?requesting_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2500.00,
    "type": "income",
    "category": "Consulting",
    "date": "2026-04-01",
    "notes": "April consulting fees",
    "user_id": 2
  }'
```

### Filter expenses by category (analyst)
```bash
curl "http://localhost:8000/api/transactions/?requesting_user_id=2&type=expense&category=rent"
```

### Get financial summary (viewer)
```bash
curl "http://localhost:8000/api/summary/?requesting_user_id=3"
```

### Get summary with category breakdown (analyst)
```bash
curl "http://localhost:8000/api/summary/?requesting_user_id=2"
```

---

## 🧠 Design Assumptions

1. **Authentication is simplified** — users are identified by `requesting_user_id` query param. In production, this would be replaced by JWT/session-based auth.
2. **Role enforcement** is handled at the service layer, keeping routers thin.
3. **SQLite** is used for simplicity. Switching to PostgreSQL requires only changing `DATABASE_URL` in `database.py`.
4. **Amounts are always positive** — transaction type (`income`/`expense`) determines direction, not the sign of the amount.
5. **Seed data** is only inserted once (checked via row count); safe to restart the server.

---

## ✅ Optional Enhancements (not included but ready to add)

- JWT authentication (FastAPI `OAuth2PasswordBearer`)
- Pagination metadata in list responses
- CSV/JSON export endpoint
- Unit tests with `pytest` + `httpx`
- Search across notes/category fields
