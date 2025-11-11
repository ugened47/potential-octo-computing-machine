"""Add Advanced Editor models (Project, Track, TrackItem, Asset, Transition, CompositionEffect)

Revision ID: add_advanced_editor_models
Revises: create_clips_table
Create Date: 2025-11-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_advanced_editor_models"
down_revision: str | None = "create_clips_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("frame_rate", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("background_color", sqlmodel.sql.sqltypes.AutoString(length=7), nullable=False),
        sa.Column("canvas_settings", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("export_settings", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("thumbnail_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_rendered_at", sa.DateTime(), nullable=True),
        sa.Column("render_output_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)
    op.create_index(op.f("ix_projects_created_at"), "projects", ["created_at"], unique=False)

    # Create transitions table
    op.create_table(
        "transitions",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("transition_type", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=True),
        sa.Column("default_duration", sa.Float(), nullable=False),
        sa.Column("parameters", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("preview_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transitions_transition_type"), "transitions", ["transition_type"], unique=False)
    op.create_index(op.f("ix_transitions_is_public"), "transitions", ["is_public"], unique=False)

    # Create composition_effects table
    op.create_table(
        "composition_effects",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("effect_type", sa.String(), nullable=False),
        sa.Column("parameters", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("ffmpeg_filter", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("preview_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_composition_effects_effect_type"), "composition_effects", ["effect_type"], unique=False)

    # Create assets table
    op.create_table(
        "assets",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("file_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("thumbnail_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_assets_user_id"), "assets", ["user_id"], unique=False)
    op.create_index(op.f("ix_assets_asset_type"), "assets", ["asset_type"], unique=False)
    op.create_index(op.f("ix_assets_created_at"), "assets", ["created_at"], unique=False)
    # Create GIN index on tags array for fast array search
    op.execute("CREATE INDEX idx_assets_tags_gin ON assets USING gin(tags)")

    # Create tracks table
    op.create_table(
        "tracks",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("project_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("track_type", sa.String(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("z_index", sa.Integer(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column("is_muted", sa.Boolean(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("opacity", sa.Float(), nullable=False),
        sa.Column("blend_mode", sa.String(), nullable=False),
        sa.Column("track_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_tracks_project_id"), "tracks", ["project_id"], unique=False)
    op.create_index(op.f("ix_tracks_z_index"), "tracks", ["z_index"], unique=False)
    op.create_index(op.f("ix_tracks_track_order"), "tracks", ["track_order"], unique=False)

    # Create track_items table
    op.create_table(
        "track_items",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("track_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column("trim_start", sa.Float(), nullable=False),
        sa.Column("trim_end", sa.Float(), nullable=False),
        sa.Column("position_x", sa.Float(), nullable=False),
        sa.Column("position_y", sa.Float(), nullable=False),
        sa.Column("scale_x", sa.Float(), nullable=False),
        sa.Column("scale_y", sa.Float(), nullable=False),
        sa.Column("rotation", sa.Float(), nullable=False),
        sa.Column("crop_settings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("transform_settings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("text_content", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("text_style", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("effects", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("transition_in_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("transition_out_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transition_in_id"], ["transitions.id"]),
        sa.ForeignKeyConstraint(["transition_out_id"], ["transitions.id"]),
    )
    op.create_index(op.f("ix_track_items_track_id"), "track_items", ["track_id"], unique=False)
    op.create_index(op.f("ix_track_items_start_time"), "track_items", ["start_time"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("track_items")
    op.drop_table("tracks")
    op.execute("DROP INDEX IF EXISTS idx_assets_tags_gin")
    op.drop_table("assets")
    op.drop_table("composition_effects")
    op.drop_table("transitions")
    op.drop_table("projects")
