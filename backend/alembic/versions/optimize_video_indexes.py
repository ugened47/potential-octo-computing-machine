"""Optimize video table indexes for performance

Revision ID: optimize_video_001
Revises: add_thumbnail_url_to_videos
Create Date: 2025-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'optimize_video_001'
down_revision: Union[str, None] = 'add_thumbnail_url_to_videos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for video queries."""

    # Add index on status for filtering
    op.create_index('ix_videos_status', 'videos', ['status'], unique=False)

    # Add composite index for user_id + status (common query pattern)
    op.create_index('ix_videos_user_status', 'videos', ['user_id', 'status'], unique=False)

    # Add composite index for user_id + created_at (pagination)
    op.create_index('ix_videos_user_created', 'videos', ['user_id', 'created_at'], unique=False)

    # Add index on title for search queries (ILIKE)
    # Using gin_trgm_ops for trigram search (better for ILIKE performance)
    # First ensure pg_trgm extension is installed
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX ix_videos_title_trgm ON videos USING gin(title gin_trgm_ops)")

    # Add index on duration for sorting
    op.create_index('ix_videos_duration', 'videos', ['duration'], unique=False)


def downgrade() -> None:
    """Remove performance indexes."""

    # Drop indexes in reverse order
    op.drop_index('ix_videos_duration', table_name='videos')
    op.execute("DROP INDEX IF EXISTS ix_videos_title_trgm")
    op.drop_index('ix_videos_user_created', table_name='videos')
    op.drop_index('ix_videos_user_status', table_name='videos')
    op.drop_index('ix_videos_status', table_name='videos')
