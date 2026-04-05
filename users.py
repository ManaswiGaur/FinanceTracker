from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserCreate, UserUpdate, UserOut
from app.services import user_service

router = APIRouter()


@router.post("/", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user. Anyone can register."""
    return user_service.create_user(db, data)


@router.get("/", response_model=list[UserOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all users."""
    return user_service.get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a single user by ID."""
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    requesting_user_id: int = Query(..., description="ID of the user making the request"),
    db: Session = Depends(get_db),
):
    """Update a user. Requires admin role."""
    return user_service.update_user(db, user_id, data, requesting_user_id)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    requesting_user_id: int = Query(..., description="ID of the user making the request"),
    db: Session = Depends(get_db),
):
    """Delete a user. Requires admin role."""
    return user_service.delete_user(db, user_id, requesting_user_id)
