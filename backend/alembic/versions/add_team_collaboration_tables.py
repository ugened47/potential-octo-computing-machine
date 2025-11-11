"""Add team collaboration tables

Revision ID: add_team_collaboration
Revises: create_clips_table
Create Date: 2025-11-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_team_collaboration"
down_revision: str | None = "create_clips_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("owner_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("max_members", sa.Integer(), nullable=False),
        sa.Column("settings", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)
    op.create_index(op.f("ix_organizations_owner_id"), "organizations", ["owner_id"], unique=False)

    # Create team_members table
    op.create_table(
        "team_members",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("organization_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("invited_by", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("invited_at", sa.DateTime(), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_team_members_org_user"),
    )
    op.create_index(op.f("ix_team_members_organization_id"), "team_members", ["organization_id"], unique=False)
    op.create_index(op.f("ix_team_members_user_id"), "team_members", ["user_id"], unique=False)
    op.create_index(op.f("ix_team_members_role"), "team_members", ["role"], unique=False)
    op.create_index(op.f("ix_team_members_status"), "team_members", ["status"], unique=False)

    # Create video_permissions table
    op.create_table(
        "video_permissions",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("organization_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("permission_level", sa.String(), nullable=False),
        sa.Column("granted_by", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "(organization_id IS NOT NULL AND user_id IS NULL) OR (organization_id IS NULL AND user_id IS NOT NULL)",
            name="ck_video_permissions_org_or_user",
        ),
    )
    op.create_index(op.f("ix_video_permissions_video_id"), "video_permissions", ["video_id"], unique=False)
    op.create_index(op.f("ix_video_permissions_organization_id"), "video_permissions", ["organization_id"], unique=False)
    op.create_index(op.f("ix_video_permissions_user_id"), "video_permissions", ["user_id"], unique=False)
    op.create_index(op.f("ix_video_permissions_permission_level"), "video_permissions", ["permission_level"], unique=False)

    # Create video_shares table
    op.create_table(
        "video_shares",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("shared_by", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("shared_with_user_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("shared_with_organization_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("permission_level", sa.String(), nullable=False),
        sa.Column("access_type", sa.String(), nullable=False),
        sa.Column("share_token", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("access_count", sa.Integer(), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_with_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_with_organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_video_shares_video_id"), "video_shares", ["video_id"], unique=False)
    op.create_index(op.f("ix_video_shares_shared_by"), "video_shares", ["shared_by"], unique=False)
    op.create_index(op.f("ix_video_shares_shared_with_user_id"), "video_shares", ["shared_with_user_id"], unique=False)
    op.create_index(op.f("ix_video_shares_shared_with_organization_id"), "video_shares", ["shared_with_organization_id"], unique=False)
    op.create_index(op.f("ix_video_shares_share_token"), "video_shares", ["share_token"], unique=True)
    op.create_index(op.f("ix_video_shares_expires_at"), "video_shares", ["expires_at"], unique=False)

    # Create comments table
    op.create_table(
        "comments",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("parent_comment_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("timestamp_end", sa.Float(), nullable=True),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(length=10000), nullable=False),
        sa.Column("mentions", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column("attachments", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("resolved_by", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("is_edited", sa.Boolean(), nullable=False),
        sa.Column("edited_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_comments_video_id"), "comments", ["video_id"], unique=False)
    op.create_index(op.f("ix_comments_user_id"), "comments", ["user_id"], unique=False)
    op.create_index(op.f("ix_comments_parent_comment_id"), "comments", ["parent_comment_id"], unique=False)
    op.create_index(op.f("ix_comments_timestamp"), "comments", ["timestamp"], unique=False)
    op.create_index(op.f("ix_comments_is_resolved"), "comments", ["is_resolved"], unique=False)
    op.create_index(op.f("ix_comments_created_at"), "comments", ["created_at"], unique=False)

    # Create comment_reactions table
    op.create_table(
        "comment_reactions",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("comment_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("reaction_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("comment_id", "user_id", name="uq_comment_reactions_comment_user"),
    )
    op.create_index(op.f("ix_comment_reactions_comment_id"), "comment_reactions", ["comment_id"], unique=False)
    op.create_index(op.f("ix_comment_reactions_user_id"), "comment_reactions", ["user_id"], unique=False)

    # Create versions table
    op.create_table(
        "versions",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_by", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("change_summary", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("change_details", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("video_metadata_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("file_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("transcript_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("timeline_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("parent_version_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_version_id"], ["versions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("video_id", "version_number", name="uq_versions_video_number"),
    )
    op.create_index(op.f("ix_versions_video_id"), "versions", ["video_id"], unique=False)
    op.create_index(op.f("ix_versions_version_number"), "versions", ["version_number"], unique=False)
    op.create_index(op.f("ix_versions_is_current"), "versions", ["is_current"], unique=False)
    op.create_index(op.f("ix_versions_created_at"), "versions", ["created_at"], unique=False)

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("related_entity_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("related_entity_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("message", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("action_url", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_notifications_created_at"), "notifications", ["created_at"], unique=False)
    # Composite index for filtering unread notifications
    op.create_index("ix_notifications_user_is_read", "notifications", ["user_id", "is_read"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("notifications")
    op.drop_table("versions")
    op.drop_table("comment_reactions")
    op.drop_table("comments")
    op.drop_table("video_shares")
    op.drop_table("video_permissions")
    op.drop_table("team_members")
    op.drop_table("organizations")
