from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    """账号：登录名 + 可选密码哈希 + Bearer token（滑动过期）。"""

    __tablename__ = "accounts"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    password_hash: str | None = Field(default=None, max_length=128)
    token: str = Field(max_length=36, unique=True)
    token_expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
