from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas import FinancialSummary
from app.services import summary_service

router = APIRouter()


@router.get("/", response_model=FinancialSummary)
def get_summary(
    requesting_user_id: int = Query(..., description="ID of the requesting user"),
    user_id: Optional[int] = Query(None, description="Filter by user (analyst/admin only)"),
    db: Session = Depends(get_db),
):
    """
    Get financial summary and analytics.
    - All roles can access aggregated totals and monthly data.
    - Analysts and Admins also receive category breakdown and can filter by user.
    """
    return summary_service.get_financial_summary(db, requesting_user_id, user_id)
