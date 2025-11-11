"""Create exports table

Revision ID: create_exports_table
Revises: optimize_video_indexes
Create Date: 2025-11-11 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_exports_table"
down_revision: str | None = "optimize_video_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enum types
    op.execute(
        """
        CREATE TYPE exportstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled')
        """
    )
    op.execute(
        """
        CREATE TYPE exporttype AS ENUM ('single', 'combined', 'clips')
        """
    )
    op.execute(
        """
        CREATE TYPE resolution AS ENUM ('720p', '1080p', '4k')
        """
    )
    op.execute(
        """
        CREATE TYPE format AS ENUM ('mp4', 'mov', 'webm')
        """
    )
    op.execute(
        """
        CREATE TYPE qualitypreset AS ENUM ('high', 'medium', 'low')
        """
    )

    # Create exports table
    op.create_table(
        "exports",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        # Export configuration
        sa.Column(
            "export_type",
            postgresql.ENUM(
                "single", "combined", "clips", name="exporttype", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "resolution",
            postgresql.ENUM(
                "720p", "1080p", "4k", name="resolution", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "format",
            postgresql.ENUM("mp4", "mov", "webm", name="format", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "quality_preset",
            postgresql.ENUM(
                "high", "medium", "low", name="qualitypreset", create_type=False
            ),
            nullable=False,
        ),
        # Segment selections as JSONB
        sa.Column("segment_selections", postgresql.JSONB(), nullable=True),
        # Processing status
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "processing",
                "completed",
                "failed",
                "cancelled",
                name="exportstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("progress_percentage", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Output data
        sa.Column(
            "output_s3_key", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True
        ),
        sa.Column(
            "output_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True
        ),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="progress_percentage_check",
        ),
    )

    # Create indexes for fast lookups
    op.create_index(op.f("ix_exports_user_id"), "exports", ["user_id"], unique=False)
    op.create_index(op.f("ix_exports_video_id"), "exports", ["video_id"], unique=False)
    op.create_index(op.f("ix_exports_status"), "exports", ["status"], unique=False)
    op.create_index(
        op.f("ix_exports_created_at"), "exports", ["created_at"], unique=False
    )

    # Create composite index for common queries (user exports sorted by date)
    op.create_index(
        "ix_exports_user_created",
        "exports",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_exports_user_created", table_name="exports")
    op.drop_index(op.f("ix_exports_created_at"), table_name="exports")
    op.drop_index(op.f("ix_exports_status"), table_name="exports")
    op.drop_index(op.f("ix_exports_video_id"), table_name="exports")
    op.drop_index(op.f("ix_exports_user_id"), table_name="exports")

    # Drop exports table
    op.drop_table("exports")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS exportstatus")
    op.execute("DROP TYPE IF EXISTS exporttype")
    op.execute("DROP TYPE IF EXISTS resolution")
    op.execute("DROP TYPE IF EXISTS format")
    op.execute("DROP TYPE IF EXISTS qualitypreset")
