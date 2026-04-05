from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models
from app.schemas import TransactionCreate, TransactionUpdate, TransactionFilters, Role
from app.services.user_service import get_user, require_role


def get_transaction(db: Session, transaction_id: int) -> models.Transaction:
    txn = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )
    return txn


def get_transactions(
    db: Session,
    filters: TransactionFilters,
    requesting_user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[models.Transaction]:
    """
    Viewers and Analysts can list transactions.
    Analysts can apply filters; Viewers get a basic listing.
    """
    user = get_user(db, requesting_user_id)

    query = db.query(models.Transaction)

    # Apply filters — analysts and admins can use all filters; viewers see all records without filters
    if user.role in (models.Role.analyst, models.Role.admin):
        if filters.type:
            query = query.filter(models.Transaction.type == filters.type)
        if filters.category:
            query = query.filter(
                models.Transaction.category.ilike(f"%{filters.category}%")
            )
        if filters.date_from:
            query = query.filter(models.Transaction.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(models.Transaction.date <= filters.date_to)
        if filters.user_id:
            query = query.filter(models.Transaction.user_id == filters.user_id)

    return query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()


def create_transaction(
    db: Session,
    data: TransactionCreate,
    requesting_user_id: int,
) -> models.Transaction:
    """Only admins can create transactions."""
    require_role(db, requesting_user_id, Role.admin)

    # Ensure target user exists
    get_user(db, data.user_id)

    txn = models.Transaction(**data.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def update_transaction(
    db: Session,
    transaction_id: int,
    data: TransactionUpdate,
    requesting_user_id: int,
) -> models.Transaction:
    """Only admins can update transactions."""
    require_role(db, requesting_user_id, Role.admin)

    txn = get_transaction(db, transaction_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(txn, field, value)
    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(
    db: Session,
    transaction_id: int,
    requesting_user_id: int,
) -> dict:
    """Only admins can delete transactions."""
    require_role(db, requesting_user_id, Role.admin)

    txn = get_transaction(db, transaction_id)
    db.delete(txn)
    db.commit()
    return {"message": f"Transaction {transaction_id} deleted successfully"}
