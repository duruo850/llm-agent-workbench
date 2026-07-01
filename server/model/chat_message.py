from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Text, func
from sqlmodel import Field, SQLModel


class ChatMessage(SQLModel, table=True):
    """单条聊天消息 (user / assistant)."""

    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_conversation_id", "conversation_id"),)

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id")
    role: str = Field(max_length=20)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
