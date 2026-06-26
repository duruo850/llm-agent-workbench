from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class Budget(SQLModel, table=True):
    """预算：ORM 表 + API 序列化（SQLModel 合一）。"""

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("category_id", "month", name="uq_budgets_category_month"),
        Index("ix_budgets_month", "month"),
        Index("ix_budgets_account_id", "account_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    category_id: int = Field(foreign_key="categories.id")
    month: str = Field(max_length=7)
    limit_amount: Decimal = Field(max_digits=12, decimal_places=2)
