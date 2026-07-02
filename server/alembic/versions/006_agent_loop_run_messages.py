"""agent_loop_runs input/output message columns

Revision ID: 006
Revises: 005
Create Date: 2026-07-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_loop_runs",
        sa.Column("input_message", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("agent_loop_runs", "reply", new_column_name="output_message")
    op.alter_column("agent_loop_runs", "input_message", server_default=None)


def downgrade() -> None:
    op.alter_column("agent_loop_runs", "output_message", new_column_name="reply")
    op.drop_column("agent_loop_runs", "input_message")
