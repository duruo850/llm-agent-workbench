"""agent_loop_steps

Revision ID: 004
Revises: 003
Create Date: 2026-07-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_loop_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("turn_id", sa.String(length=36), nullable=False),
        sa.Column("user_chat_message_id", sa.Integer(), nullable=True),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("token_usage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("node_name", sa.String(length=32), nullable=True),
        sa.Column("tool_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["user_chat_message_id"], ["chat_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_loop_steps_conversation_id",
        "agent_loop_steps",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_loop_steps_turn_id",
        "agent_loop_steps",
        ["turn_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_agent_loop_steps_turn_id", table_name="agent_loop_steps")
    op.drop_index("ix_agent_loop_steps_conversation_id", table_name="agent_loop_steps")
    op.drop_table("agent_loop_steps")
