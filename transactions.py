from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.schemas import TransactionCreate, TransactionUpdate, TransactionOut, TransactionFilters, TransactionType
from app.services import transaction_service

router = APIRouter()


@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(
    data: TransactionCreate,
    requesting_user_id: int = Query(..., description="ID of the requesting user (must be admin)"),
    db: Session = Depends(get_db),
):
    """Create a financial record. Requires admin role."""
    return transaction_service.create_transaction(db, data, requesting_user_id)


@router.get("/", response_model=list[TransactionOut])
def list_transactions(
    requesting_user_id: int = Query(..., description="ID of the requesting user"),
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    date_from: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (analyst/admin only)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List financial records with optional filters.
    - Viewers: see all records (no filters applied)
    - Analysts & Admins: full filter support
    """
    filters = TransactionFilters(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
    )
    return transaction_service.get_transactions(
        db, filters, requesting_user_id, skip=skip, limit=limit
    )


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a single transaction by ID."""
    return transaction_service.get_transaction(db, transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    requesting_user_id: int = Query(..., description="ID of the requesting user (must be admin)"),
    db: Session = Depends(get_db),
):
    """Update a transaction. Requires admin role."""
    return transaction_service.update_transaction(db, transaction_id, data, requesting_user_id)


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    requesting_user_id: int = Query(..., description="ID of the requesting user (must be admin)"),
    db: Session = Depends(get_db),
):
    """Delete a transaction. Requires admin role."""
    return transaction_service.delete_transaction(db, transaction_id, requesting_user_id)
