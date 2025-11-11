"""Add subtitle tables for styles, translations, and presets

Revision ID: add_subtitle_tables_001
Revises: optimize_video_001
Create Date: 2025-11-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'add_subtitle_tables_001'
down_revision: Union[str, None] = 'optimize_video_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create subtitle-related tables."""

    # Create subtitle_styles table
    op.create_table(
        'subtitle_styles',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('video_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('language_code', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),

        # Font properties
        sa.Column('font_family', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False, server_default='Arial'),
        sa.Column('font_size', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('font_weight', sa.String(), nullable=False, server_default='bold'),
        sa.Column('font_color', sqlmodel.sql.sqltypes.AutoString(length=9), nullable=False, server_default='#FFFFFF'),
        sa.Column('font_alpha', sa.Float(), nullable=False, server_default='1.0'),

        # Background properties
        sa.Column('background_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('background_color', sqlmodel.sql.sqltypes.AutoString(length=9), nullable=False, server_default='#000000'),
        sa.Column('background_alpha', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('background_padding', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('background_radius', sa.Integer(), nullable=False, server_default='4'),

        # Outline properties
        sa.Column('outline_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('outline_color', sqlmodel.sql.sqltypes.AutoString(length=9), nullable=False, server_default='#000000'),
        sa.Column('outline_width', sa.Integer(), nullable=False, server_default='2'),

        # Position properties
        sa.Column('position_vertical', sa.String(), nullable=False, server_default='bottom'),
        sa.Column('position_horizontal', sa.String(), nullable=False, server_default='center'),
        sa.Column('margin_vertical', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('margin_horizontal', sa.Integer(), nullable=False, server_default='40'),
        sa.Column('max_width_percent', sa.Integer(), nullable=False, server_default='80'),

        # Timing properties
        sa.Column('words_per_line', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('max_lines', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('min_display_duration', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('max_display_duration', sa.Float(), nullable=False, server_default='6.0'),

        # Animation properties
        sa.Column('animation_type', sa.String(), nullable=False, server_default='none'),
        sa.Column('animation_duration', sa.Float(), nullable=False, server_default='0.3'),

        # Metadata
        sa.Column('preset_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sqlmodel.sql.sqltypes.GUID(), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('video_id', 'language_code', name='uq_subtitle_styles_video_language'),
    )

    # Create indexes for subtitle_styles
    op.create_index('ix_subtitle_styles_video_id', 'subtitle_styles', ['video_id'], unique=False)
    op.create_index('ix_subtitle_styles_language_code', 'subtitle_styles', ['language_code'], unique=False)
    op.create_index('ix_subtitle_styles_preset_name', 'subtitle_styles', ['preset_name'], unique=False)

    # Create subtitle_translations table
    op.create_table(
        'subtitle_translations',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('video_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('source_language', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('target_language', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),

        # Translation metadata
        sa.Column('translation_service', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='google'),
        sa.Column('translation_quality', sa.String(), nullable=False, server_default='machine'),

        # Translation content (JSONB)
        sa.Column('segments', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),

        # Statistics
        sa.Column('character_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),

        # Status
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('video_id', 'target_language', name='uq_subtitle_translations_video_target'),
    )

    # Create indexes for subtitle_translations
    op.create_index('ix_subtitle_translations_video_id', 'subtitle_translations', ['video_id'], unique=False)
    op.create_index('ix_subtitle_translations_target_language', 'subtitle_translations', ['target_language'], unique=False)
    op.create_index('ix_subtitle_translations_status', 'subtitle_translations', ['status'], unique=False)

    # Create subtitle_style_presets table
    op.create_table(
        'subtitle_style_presets',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('platform', sa.String(), nullable=False, server_default='custom'),

        # Preview
        sa.Column('thumbnail_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),

        # Style configuration (JSONB)
        sa.Column('style_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),

        # Metadata
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_system_preset', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sqlmodel.sql.sqltypes.GUID(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('name', name='uq_subtitle_style_presets_name'),
    )

    # Create indexes for subtitle_style_presets
    op.create_index('ix_subtitle_style_presets_name', 'subtitle_style_presets', ['name'], unique=False)
    op.create_index('ix_subtitle_style_presets_platform', 'subtitle_style_presets', ['platform'], unique=False)
    op.create_index('ix_subtitle_style_presets_is_public', 'subtitle_style_presets', ['is_public'], unique=False)


def downgrade() -> None:
    """Drop subtitle-related tables."""

    # Drop subtitle_style_presets table
    op.drop_index('ix_subtitle_style_presets_is_public', table_name='subtitle_style_presets')
    op.drop_index('ix_subtitle_style_presets_platform', table_name='subtitle_style_presets')
    op.drop_index('ix_subtitle_style_presets_name', table_name='subtitle_style_presets')
    op.drop_table('subtitle_style_presets')

    # Drop subtitle_translations table
    op.drop_index('ix_subtitle_translations_status', table_name='subtitle_translations')
    op.drop_index('ix_subtitle_translations_target_language', table_name='subtitle_translations')
    op.drop_index('ix_subtitle_translations_video_id', table_name='subtitle_translations')
    op.drop_table('subtitle_translations')

    # Drop subtitle_styles table
    op.drop_index('ix_subtitle_styles_preset_name', table_name='subtitle_styles')
    op.drop_index('ix_subtitle_styles_language_code', table_name='subtitle_styles')
    op.drop_index('ix_subtitle_styles_video_id', table_name='subtitle_styles')
    op.drop_table('subtitle_styles')
