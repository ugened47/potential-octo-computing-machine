"""Create clips table

Revision ID: create_clips_table
Revises: add_thumbnail_url
Create Date: 2025-11-07 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_clips_table"
down_revision: str | None = "add_thumbnail_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create clips table
    op.create_table(
        "clips",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("clip_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
        ),
    )
    op.create_index(op.f("ix_clips_video_id"), "clips", ["video_id"], unique=False)

    # Create GIN index on keywords array for fast array search
    op.execute("CREATE INDEX idx_clips_keywords_gin ON clips USING gin(keywords)")


def downgrade() -> None:
    # Drop GIN index
    op.execute("DROP INDEX IF EXISTS idx_clips_keywords_gin")

    # Drop clips table
    op.drop_table("clips")
