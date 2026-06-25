"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-06-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("budget_monthly", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("limit_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "month", name="uq_budgets_category_month"),
    )
    op.create_index("ix_budgets_month", "budgets", ["month"], unique=False)
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("merchant", sa.String(length=200), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=False),
        sa.Column("transacted_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transactions_transacted_at",
        "transactions",
        ["transacted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_transacted_at", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_budgets_month", table_name="budgets")
    op.drop_table("budgets")
    op.drop_table("categories")
