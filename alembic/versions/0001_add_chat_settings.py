"""add chat_settings table

Revision ID: 0001
Revises:
Create Date: 2026-05-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_settings",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="anthropic"),
        sa.Column("model", sa.String(64), nullable=False, server_default="claude-sonnet-4-6"),
        sa.PrimaryKeyConstraint("chat_id"),
    )


def downgrade() -> None:
    op.drop_table("chat_settings")
