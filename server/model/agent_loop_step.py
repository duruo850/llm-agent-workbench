from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, func
from sqlmodel import Field, SQLModel


class AgentLoopStep(SQLModel, table=True):
    """Agent 循环单步指标 — 单次 invoke (turn_id) 内从 1 递增。"""

    __tablename__ = "agent_loop_steps"
    __table_args__ = (
        Index("ix_agent_loop_steps_conversation_id", "conversation_id"),
        Index("ix_agent_loop_steps_turn_id", "turn_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    conversation_id: int = Field(foreign_key="conversations.id")
    thread_id: str = Field(max_length=64)
    turn_id: str = Field(max_length=36)
    user_chat_message_id: int | None = Field(default=None, foreign_key="chat_messages.id")
    step_count: int
    token_usage: int = Field(default=0)
    node_name: str | None = Field(default=None, max_length=32)
    tool_name: str | None = Field(default=None, max_length=100)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
