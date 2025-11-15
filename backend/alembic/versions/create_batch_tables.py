"""Create batch processing tables

Revision ID: create_batch_tables
Revises: create_clips_table
Create Date: 2025-11-11 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_batch_tables"
down_revision: str | None = "create_clips_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create batch_jobs table
    op.create_table(
        "batch_jobs",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("settings", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("total_videos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_videos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_videos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_videos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("processed_duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("estimated_time_remaining", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.CheckConstraint("priority >= 0 AND priority <= 10", name="check_priority_range"),
    )

    # Create indexes on batch_jobs
    op.create_index(op.f("ix_batch_jobs_user_id"), "batch_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_batch_jobs_status"), "batch_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_batch_jobs_created_at"), "batch_jobs", ["created_at"], unique=False)
    op.create_index(
        "ix_batch_jobs_priority_created_at",
        "batch_jobs",
        ["priority", "created_at"],
        unique=False,
    )

    # Create batch_videos table
    op.create_table(
        "batch_videos",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("batch_job_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress_percentage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_stage", sa.String(), nullable=True),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("processing_result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("output_video_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["batch_job_id"],
            ["batch_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
        ),
        sa.CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="check_progress_range"),
    )

    # Create indexes on batch_videos
    op.create_index(op.f("ix_batch_videos_batch_job_id"), "batch_videos", ["batch_job_id"], unique=False)
    op.create_index(op.f("ix_batch_videos_video_id"), "batch_videos", ["video_id"], unique=False)
    op.create_index(op.f("ix_batch_videos_status"), "batch_videos", ["status"], unique=False)
    op.create_index(
        "ix_batch_videos_batch_job_position",
        "batch_videos",
        ["batch_job_id", "position"],
        unique=False,
    )

    # Create unique constraint to prevent duplicate videos in same batch
    op.create_unique_constraint(
        "uq_batch_videos_batch_job_video",
        "batch_videos",
        ["batch_job_id", "video_id"],
    )


def downgrade() -> None:
    # Drop batch_videos table (cascade will handle foreign keys)
    op.drop_table("batch_videos")

    # Drop batch_jobs table
    op.drop_table("batch_jobs")
