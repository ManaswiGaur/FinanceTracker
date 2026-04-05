from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional
from datetime import date
from enum import Enum


class Role(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


# ─── User Schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role = Role.viewer

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Role] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: Role

    model_config = {"from_attributes": True}


# ─── Transaction Schemas ─────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    category: str
    date: date = date.today()
    notes: Optional[str] = None
    user_id: int

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Category must not be empty")
        return v


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2) if v is not None else v


class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: str
    date: date
    notes: Optional[str]
    user_id: int

    model_config = {"from_attributes": True}


# ─── Filter & Pagination ─────────────────────────────────────────────────────

class TransactionFilters(BaseModel):
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    user_id: Optional[int] = None

    @model_validator(mode="after")
    def date_range_check(self) -> "TransactionFilters":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before date_to")
        return self


# ─── Summary Schemas ─────────────────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int


class MonthlyTotal(BaseModel):
    year: int
    month: int
    income: float
    expenses: float
    net: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    current_balance: float
    transaction_count: int
    category_breakdown: list[CategoryBreakdown]
    monthly_totals: list[MonthlyTotal]
    recent_transactions: list[TransactionOut]
