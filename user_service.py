from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models
from app.schemas import UserCreate, UserUpdate, Role


def get_user(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return user


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 50) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, data: UserCreate) -> models.User:
    existing = get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email '{data.email}' already exists",
        )
    user = models.User(**data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, requesting_user_id: int) -> models.User:
    """Only admins can update users."""
    requesting_user = get_user(db, requesting_user_id)
    if requesting_user.role != models.Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update user records",
        )
    user = get_user(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, requesting_user_id: int) -> dict:
    """Only admins can delete users."""
    requesting_user = get_user(db, requesting_user_id)
    if requesting_user.role != models.Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users",
        )
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully"}


def require_role(db: Session, user_id: int, *allowed_roles: Role) -> models.User:
    """Utility to enforce role-based access."""
    user = get_user(db, user_id)
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
        )
    return user
