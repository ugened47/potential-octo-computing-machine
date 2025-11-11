"""Create social media templates and video exports tables

Revision ID: create_social_media_templates
Revises: create_clips_table
Create Date: 2025-11-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_social_media_templates"
down_revision: str | None = "create_clips_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create platform_type enum
    platform_type = postgresql.ENUM(
        "youtube_shorts",
        "tiktok",
        "instagram_reels",
        "twitter",
        "linkedin",
        "custom",
        name="platformtype",
        create_type=False,
    )
    platform_type.create(op.get_bind(), checkfirst=True)

    # Create style_preset enum
    style_preset = postgresql.ENUM(
        "minimal",
        "bold",
        "gaming",
        "podcast",
        "vlog",
        "professional",
        "trendy",
        "custom",
        name="stylepreset",
        create_type=False,
    )
    style_preset.create(op.get_bind(), checkfirst=True)

    # Create export_status enum
    export_status = postgresql.ENUM(
        "processing",
        "completed",
        "failed",
        name="exportstatus",
        create_type=False,
    )
    export_status.create(op.get_bind(), checkfirst=True)

    # Create crop_strategy enum
    crop_strategy = postgresql.ENUM(
        "smart",
        "center",
        "letterbox",
        "blur",
        name="cropstrategy",
        create_type=False,
    )
    crop_strategy.create(op.get_bind(), checkfirst=True)

    # Create social_media_templates table
    op.create_table(
        "social_media_templates",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "platform",
            postgresql.ENUM(
                "youtube_shorts",
                "tiktok",
                "instagram_reels",
                "twitter",
                "linkedin",
                "custom",
                name="platformtype",
            ),
            nullable=False,
        ),
        sa.Column("aspect_ratio", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("max_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("auto_captions", sa.Boolean(), nullable=False),
        sa.Column("caption_style", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "style_preset",
            postgresql.ENUM(
                "minimal",
                "bold",
                "gaming",
                "podcast",
                "vlog",
                "professional",
                "trendy",
                "custom",
                name="stylepreset",
            ),
            nullable=False,
        ),
        sa.Column("video_codec", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("audio_codec", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("bitrate", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("is_system_preset", sa.Boolean(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.CheckConstraint("aspect_ratio ~ '^[0-9]+:[0-9]+$'", name="valid_aspect_ratio"),
    )
    op.create_index(
        op.f("ix_social_media_templates_name"),
        "social_media_templates",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_media_templates_platform"),
        "social_media_templates",
        ["platform"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_media_templates_is_system_preset"),
        "social_media_templates",
        ["is_system_preset"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_media_templates_user_id"),
        "social_media_templates",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_media_templates_is_active"),
        "social_media_templates",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_media_templates_created_at"),
        "social_media_templates",
        ["created_at"],
        unique=False,
    )

    # Create video_exports table
    op.create_table(
        "video_exports",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("template_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("export_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("s3_key", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("resolution", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("segment_start_time", sa.Float(), nullable=True),
        sa.Column("segment_end_time", sa.Float(), nullable=True),
        sa.Column(
            "crop_strategy",
            postgresql.ENUM(
                "smart",
                "center",
                "letterbox",
                "blur",
                name="cropstrategy",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "processing",
                "completed",
                "failed",
                name="exportstatus",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["social_media_templates.id"],
        ),
        sa.CheckConstraint(
            "segment_start_time IS NULL OR segment_end_time IS NULL OR segment_start_time < segment_end_time",
            name="valid_segment_times",
        ),
        sa.CheckConstraint(
            "segment_start_time IS NULL OR segment_start_time >= 0",
            name="segment_start_non_negative",
        ),
        sa.CheckConstraint(
            "segment_end_time IS NULL OR segment_end_time >= 0",
            name="segment_end_non_negative",
        ),
    )
    op.create_index(
        op.f("ix_video_exports_video_id"), "video_exports", ["video_id"], unique=False
    )
    op.create_index(
        op.f("ix_video_exports_template_id"),
        "video_exports",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_video_exports_status"), "video_exports", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_video_exports_created_at"),
        "video_exports",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop video_exports table
    op.drop_table("video_exports")

    # Drop social_media_templates table
    op.drop_table("social_media_templates")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS cropstrategy")
    op.execute("DROP TYPE IF EXISTS exportstatus")
    op.execute("DROP TYPE IF EXISTS stylepreset")
    op.execute("DROP TYPE IF EXISTS platformtype")
