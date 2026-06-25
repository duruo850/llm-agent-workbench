from __future__ import annotations

from decimal import Decimal

from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """分类：ORM 表 + API 序列化（SQLModel 合一）。"""

    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    budget_monthly: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
