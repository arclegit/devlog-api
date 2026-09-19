"""enforce one active session per user

Revision ID: 6543fe533118
Revises: 22be68e1eeab
Create Date: 2026-09-18 22:44:35.653146
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6543fe533118"
down_revision: Union[str, Sequence[str], None] = "22be68e1eeab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_index(
        "ix_coding_sessions_one_active_per_user",
        "coding_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_coding_sessions_one_active_per_user",
        table_name="coding_sessions",
    )