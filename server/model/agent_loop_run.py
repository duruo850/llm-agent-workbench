from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Text, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class AgentLoopRun(SQLModel, table=True):
    """单次 turn（一次 invoke_v2 / POST /agent/chat）的循环汇总 — 对应 LoopRunResult。"""

    __tablename__ = "agent_loop_runs"
    __table_args__ = (
        UniqueConstraint("turn_id", name="uq_agent_loop_runs_turn_id"),
        Index("ix_agent_loop_runs_conversation_id", "conversation_id"),
        Index("ix_agent_loop_runs_thread_id", "thread_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    conversation_id: int = Field(foreign_key="conversations.id")
    thread_id: str = Field(max_length=64)
    turn_id: str = Field(max_length=36)
    user_chat_message_id: int | None = Field(default=None, foreign_key="chat_messages.id")
    total_steps: int
    total_tokens: int = Field(default=0)
    stopped_reason: str | None = Field(default=None, max_length=32)
    input_message: str = Field(sa_column=Column(Text, nullable=False))
    output_message: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
