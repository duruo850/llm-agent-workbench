from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Index, func
from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    """交易：ORM 表 + API 序列化（SQLModel 合一）。"""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_transacted_at", "transacted_at"),
        Index("ix_transactions_account_id", "account_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    amount: Decimal = Field(max_digits=12, decimal_places=2, gt=0)
    category: str = Field(max_length=100)
    merchant: str = Field(default="", max_length=200)
    note: str = Field(default="", max_length=500)
    transacted_at: datetime = Field(sa_column=Column(DateTime(timezone=False), nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
