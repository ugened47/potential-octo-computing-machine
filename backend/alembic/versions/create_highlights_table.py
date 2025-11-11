"""Create highlights table

Revision ID: create_highlights_table
Revises: create_clips_table
Create Date: 2025-11-11 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_highlights_table"
down_revision: str | None = "create_clips_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enum types for highlight_type and status
    highlight_type_enum = postgresql.ENUM(
        "high_energy",
        "key_moment",
        "keyword_match",
        "scene_change",
        name="highlighttype",
        create_type=False,
    )
    highlight_type_enum.create(op.get_bind(), checkfirst=True)

    highlight_status_enum = postgresql.ENUM(
        "detected",
        "reviewed",
        "exported",
        "rejected",
        name="highlightstatus",
        create_type=False,
    )
    highlight_status_enum.create(op.get_bind(), checkfirst=True)

    # Create highlights table
    op.create_table(
        "highlights",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("audio_energy_score", sa.Integer(), nullable=False),
        sa.Column("scene_change_score", sa.Integer(), nullable=False),
        sa.Column("speech_density_score", sa.Integer(), nullable=False),
        sa.Column("keyword_score", sa.Integer(), nullable=False),
        sa.Column(
            "detected_keywords",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("confidence_level", sa.Float(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column(
            "highlight_type",
            postgresql.ENUM(
                "high_energy",
                "key_moment",
                "keyword_match",
                "scene_change",
                name="highlighttype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "detected",
                "reviewed",
                "exported",
                "rejected",
                name="highlightstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("context_before_seconds", sa.Float(), nullable=False),
        sa.Column("context_after_seconds", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            ondelete="CASCADE",
        ),
    )

    # Create indexes
    op.create_index(
        op.f("ix_highlights_video_id"), "highlights", ["video_id"], unique=False
    )
    op.create_index(
        op.f("ix_highlights_overall_score"),
        "highlights",
        [sa.text("overall_score DESC")],
        unique=False,
    )
    op.create_index(op.f("ix_highlights_rank"), "highlights", ["rank"], unique=False)
    op.create_index(
        op.f("ix_highlights_status"), "highlights", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_highlights_created_at"), "highlights", ["created_at"], unique=False
    )

    # Create composite index on (video_id, status) for filtered queries
    op.create_index(
        "ix_highlights_video_id_status",
        "highlights",
        ["video_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_highlights_video_id_status", table_name="highlights")
    op.drop_index(op.f("ix_highlights_created_at"), table_name="highlights")
    op.drop_index(op.f("ix_highlights_status"), table_name="highlights")
    op.drop_index(op.f("ix_highlights_rank"), table_name="highlights")
    op.drop_index(op.f("ix_highlights_overall_score"), table_name="highlights")
    op.drop_index(op.f("ix_highlights_video_id"), table_name="highlights")

    # Drop highlights table
    op.drop_table("highlights")

    # Drop enum types
    highlight_status_enum = postgresql.ENUM(name="highlightstatus")
    highlight_status_enum.drop(op.get_bind(), checkfirst=True)

    highlight_type_enum = postgresql.ENUM(name="highlighttype")
    highlight_type_enum.drop(op.get_bind(), checkfirst=True)
