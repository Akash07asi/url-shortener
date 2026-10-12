"""baseline existing urls schema

Revision ID: 704fc7c550dc
Revises: 
Create Date: 2026-10-12 16:59:09.344197

"""

import sqlalchemy as sa
from alembic import op


from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '704fc7c550dc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial URL mapping table for a fresh database."""
    op.create_table(
        "urls",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("short_code", sa.String(length=6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="urls_pkey"),
        sa.UniqueConstraint("short_code", name="urls_short_code_key"),
    )


def downgrade() -> None:
    """Remove the URL mapping table when reverting the initial migration."""
    op.drop_table("urls")