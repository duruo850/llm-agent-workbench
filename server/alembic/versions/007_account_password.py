"""accounts.password_hash for password login (salted PBKDF2)

Revision ID: 007
Revises: 006
Create Date: 2026-09-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("password_hash", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accounts", "password_hash")
