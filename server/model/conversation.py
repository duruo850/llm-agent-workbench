from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    """会话: 按 account + thread_id 隔离."""

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("account_id", "thread_id", name="uq_conversations_account_thread"),
        Index("ix_conversations_account_id", "account_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")  # 用户id
    thread_id: str = Field(max_length=64)  # 会话id
    title: str | None = Field(default=None, max_length=200)  # 会话标题
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=False),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
