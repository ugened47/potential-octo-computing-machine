"""Add thumbnail_url to videos table

Revision ID: add_thumbnail_url
Revises: abc123def456
Create Date: 2025-11-07 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_thumbnail_url"
down_revision: str | None = "abc123def456"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add thumbnail_url column to videos table
    op.add_column(
        "videos",
        sa.Column("thumbnail_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    )


def downgrade() -> None:
    # Remove thumbnail_url column from videos table
    op.drop_column("videos", "thumbnail_url")
