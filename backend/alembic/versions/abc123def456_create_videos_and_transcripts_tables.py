"""Create videos and transcripts tables

Revision ID: abc123def456
Revises: 7224904a41f3
Create Date: 2025-11-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, None] = '7224904a41f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create videos table
    op.create_table('videos',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('format', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('resolution', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('s3_key', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('cloudfront_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_videos_user_id'), 'videos', ['user_id'], unique=False)
    op.create_index(op.f('ix_videos_created_at'), 'videos', ['created_at'], unique=False)

    # Create transcripts table
    op.create_table('transcripts',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('video_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('word_timestamps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('language', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
    )
    op.create_index(op.f('ix_transcripts_video_id'), 'transcripts', ['video_id'], unique=False)
    op.create_index(op.f('ix_transcripts_full_text'), 'transcripts', ['full_text'], unique=False)
    
    # Create full-text search index on full_text
    op.execute(
        "CREATE INDEX idx_transcripts_full_text_fts ON transcripts USING gin(to_tsvector('english', full_text))"
    )


def downgrade() -> None:
    # Drop full-text search index
    op.execute("DROP INDEX IF EXISTS idx_transcripts_full_text_fts")
    
    # Drop transcripts table
    op.drop_index(op.f('ix_transcripts_full_text'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_video_id'), table_name='transcripts')
    op.drop_table('transcripts')
    
    # Drop videos table
    op.drop_index(op.f('ix_videos_created_at'), table_name='videos')
    op.drop_index(op.f('ix_videos_user_id'), table_name='videos')
    op.drop_table('videos')

