from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict

from app import models
from app.schemas import FinancialSummary, CategoryBreakdown, MonthlyTotal, TransactionOut, Role
from app.services.user_service import require_role


def get_financial_summary(
    db: Session,
    requesting_user_id: int,
    user_id: int | None = None,
) -> FinancialSummary:
    """
    Viewers and Analysts and Admins can access summaries.
    Analysts/Admins can filter by a specific user.
    """
    require_role(db, requesting_user_id, Role.viewer, Role.analyst, Role.admin)

    base_query = db.query(models.Transaction)

    requesting_user = db.query(models.User).filter(models.User.id == requesting_user_id).first()

    # Analysts and admins can filter by user_id; viewers see aggregate only
    if user_id and requesting_user.role in (models.Role.analyst, models.Role.admin):
        base_query = base_query.filter(models.Transaction.user_id == user_id)

    transactions = base_query.all()

    total_income = sum(t.amount for t in transactions if t.type == models.TransactionType.income)
    total_expenses = sum(t.amount for t in transactions if t.type == models.TransactionType.expense)
    current_balance = round(total_income - total_expenses, 2)

    # Category breakdown (only for analyst/admin)
    category_breakdown = []
    if requesting_user.role in (models.Role.analyst, models.Role.admin):
        category_map: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
        for t in transactions:
            key = t.category
            category_map[key]["total"] = round(category_map[key]["total"] + t.amount, 2)
            category_map[key]["count"] += 1
        category_breakdown = [
            CategoryBreakdown(category=cat, total=vals["total"], count=vals["count"])
            for cat, vals in sorted(category_map.items(), key=lambda x: -x[1]["total"])
        ]

    # Monthly totals
    monthly_map: dict[tuple, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for t in transactions:
        key = (t.date.year, t.date.month)
        if t.type == models.TransactionType.income:
            monthly_map[key]["income"] = round(monthly_map[key]["income"] + t.amount, 2)
        else:
            monthly_map[key]["expenses"] = round(monthly_map[key]["expenses"] + t.amount, 2)

    monthly_totals = [
        MonthlyTotal(
            year=year,
            month=month,
            income=vals["income"],
            expenses=vals["expenses"],
            net=round(vals["income"] - vals["expenses"], 2),
        )
        for (year, month), vals in sorted(monthly_map.items(), reverse=True)
    ]

    # Recent activity — last 10 transactions
    recent = (
        base_query.order_by(models.Transaction.date.desc()).limit(10).all()
    )

    return FinancialSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        current_balance=current_balance,
        transaction_count=len(transactions),
        category_breakdown=category_breakdown,
        monthly_totals=monthly_totals,
        recent_transactions=[TransactionOut.model_validate(t) for t in recent],
    )
