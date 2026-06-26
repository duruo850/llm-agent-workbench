"""accounts multi tenant

Revision ID: 002
Revises: 001
Create Date: 2025-06-26

"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("token", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("token"),
    )

    legacy_token = str(uuid.uuid4())
    op.execute(
        sa.text(
            "INSERT INTO accounts (name, token) VALUES ('legacy', :token)"
        ).bindparams(token=legacy_token)
    )

    conn = op.get_bind()
    legacy_id = conn.execute(sa.text("SELECT id FROM accounts WHERE name = 'legacy'")).scalar_one()

    for table in ("categories", "budgets", "transactions"):
        op.add_column(table, sa.Column("account_id", sa.Integer(), nullable=True))
        op.execute(
            sa.text(f"UPDATE {table} SET account_id = :account_id").bindparams(account_id=legacy_id)
        )
        op.alter_column(table, "account_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_account_id",
            table,
            "accounts",
            ["account_id"],
            ["id"],
        )
        op.create_index(f"ix_{table}_account_id", table, ["account_id"], unique=False)

    op.drop_constraint("categories_name_key", "categories", type_="unique")
    op.create_unique_constraint(
        "uq_categories_account_name",
        "categories",
        ["account_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_categories_account_name", "categories", type_="unique")
    op.create_unique_constraint("categories_name_key", "categories", ["name"])

    for table in ("transactions", "budgets", "categories"):
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account_id", table, type_="foreignkey")
        op.drop_column(table, "account_id")

    op.drop_table("accounts")
