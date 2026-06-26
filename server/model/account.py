from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    """账号：登录名 + Bearer token。"""

    __tablename__ = "accounts"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    token: str = Field(max_length=36, unique=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
