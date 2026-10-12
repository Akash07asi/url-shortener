"""enforce six character short codes

Revision ID: 95c0404961b6
Revises: 704fc7c550dc
Create Date: 2026-10-12 17:04:44.662221

"""
from alembic import op

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95c0404961b6'
down_revision: Union[str, Sequence[str], None] = '704fc7c550dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Require every short code to contain exactly six characters."""
    op.create_check_constraint(
        "ck_urls_short_code_length",
        "urls",
        "LENGTH(short_code) = 6",
    )


def downgrade() -> None:
    """Remove the short-code length constraint if this migration is reverted."""
    op.drop_constraint(
        "ck_urls_short_code_length",
        "urls",
        type_="check",
    )