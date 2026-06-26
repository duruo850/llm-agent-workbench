from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """分类：ORM 表 + API 序列化（SQLModel 合一）。"""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("account_id", "name", name="uq_categories_account_name"),
        Index("ix_categories_account_id", "account_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    name: str = Field(max_length=100)
    budget_monthly: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
