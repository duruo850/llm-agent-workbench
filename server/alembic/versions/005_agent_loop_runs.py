"""agent_loop_runs

Revision ID: 005
Revises: 004
Create Date: 2026-07-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_loop_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("turn_id", sa.String(length=36), nullable=False),
        sa.Column("user_chat_message_id", sa.Integer(), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stopped_reason", sa.String(length=32), nullable=True),
        sa.Column("reply", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["user_chat_message_id"], ["chat_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("turn_id", name="uq_agent_loop_runs_turn_id"),
    )
    op.create_index(
        "ix_agent_loop_runs_conversation_id",
        "agent_loop_runs",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_loop_runs_thread_id",
        "agent_loop_runs",
        ["thread_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_agent_loop_runs_thread_id", table_name="agent_loop_runs")
    op.drop_index("ix_agent_loop_runs_conversation_id", table_name="agent_loop_runs")
    op.drop_table("agent_loop_runs")
