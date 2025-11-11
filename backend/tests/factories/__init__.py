"""Test factories for all models in the AI Video Clipper project.

This package provides factory classes for creating test instances of all models
using the pytest-factoryboy pattern with Faker library for realistic test data.

Usage:
    from tests.factories import UserFactory, VideoFactory, TranscriptFactory

    # Create a user with default values
    user = UserFactory()

    # Create a verified user
    verified_user = UserFactory(verified=True)

    # Create a user with specific email
    custom_user = UserFactory(email="test@example.com")

    # Create related objects
    from tests.factories import VideoFactory
    video = VideoFactory(user_id=user.id)

Factory Features:
    - Uses factory.alchemy.SQLAlchemyModelFactory as base
    - Includes all required fields with sensible defaults
    - Uses Faker for realistic data (UUID, sentences, emails, etc.)
    - LazyAttribute for computed fields and relationships
    - Trait/parameterized factories for different states (e.g., verified, processing, failed)

Available Factories:
    - UserFactory: User model with traits (verified, superuser, inactive, google_oauth)
    - VideoFactory: Video model with traits (uploaded, processing, completed, failed, short, long, hd, uhd)
    - TranscriptFactory: Transcript model with traits (processing, failed, spanish, high_accuracy, short, long)
    - ClipFactory: Clip model with traits (processing, failed, short, medium, long, keyword_highlight)
    - ExportFactory: Export model with traits (pending, processing, completed, failed, hd, uhd)
    - HighlightFactory: Highlight model with traits (high_quality, audio_driven, keyword_driven)
    - BatchJobFactory: BatchJob model with traits (pending, processing, completed, small, large)
    - BatchVideoFactory: BatchVideo model with traits (pending, processing, completed, transcribed)
    - SubtitleStyleFactory: SubtitleStyle model with traits (preset, minimal, bold, gaming)
    - SubtitleTranslationFactory: SubtitleTranslation model with traits (pending, completed, spanish, french)
    - SocialMediaTemplateFactory: SocialMediaTemplate model with traits (youtube_shorts, tiktok, instagram_reels)
    - OrganizationFactory: Organization model with traits (free_plan, pro_plan, enterprise_plan)
    - TeamMemberFactory: TeamMember model with traits (owner, admin, editor, viewer, invited)
    - VideoShareFactory: VideoShare model with traits (user_share, team_share, public_link)
    - CommentFactory: Comment model with traits (timeline_comment, reply, with_mentions)
    - VersionFactory: Version model with traits (current, initial, auto_saved)
    - ProjectFactory: Project model with traits (draft, completed, hd, uhd, vertical)
    - TrackFactory: Track model with traits (video_track, audio_track, locked, muted)
    - TrackItemFactory: TrackItem model with traits (with_fade, scaled, rotated)
    - AssetFactory: Asset model with traits (video, audio, image, font)
"""

# Core models (existing)
from tests.factories.user_factory import UserFactory
from tests.factories.video_factory import VideoFactory
from tests.factories.transcript_factory import TranscriptFactory
from tests.factories.clip_factory import ClipFactory

# Post-MVP features (models to be created)
from tests.factories.export_factory import ExportFactory
from tests.factories.highlight_factory import HighlightFactory
from tests.factories.batch_factory import BatchJobFactory, BatchVideoFactory
from tests.factories.subtitle_factory import (
    SubtitleStyleFactory,
    SubtitleTranslationFactory,
)
from tests.factories.template_factory import SocialMediaTemplateFactory
from tests.factories.collaboration_factory import (
    OrganizationFactory,
    TeamMemberFactory,
    VideoShareFactory,
    CommentFactory,
    VersionFactory,
)
from tests.factories.project_factory import (
    ProjectFactory,
    TrackFactory,
    TrackItemFactory,
    AssetFactory,
)

__all__ = [
    # Core models
    "UserFactory",
    "VideoFactory",
    "TranscriptFactory",
    "ClipFactory",
    # Export feature
    "ExportFactory",
    # Auto-highlight feature
    "HighlightFactory",
    # Batch processing feature
    "BatchJobFactory",
    "BatchVideoFactory",
    # Embedded subtitles feature
    "SubtitleStyleFactory",
    "SubtitleTranslationFactory",
    # Social media templates feature
    "SocialMediaTemplateFactory",
    # Team collaboration feature
    "OrganizationFactory",
    "TeamMemberFactory",
    "VideoShareFactory",
    "CommentFactory",
    "VersionFactory",
    # Advanced editor feature
    "ProjectFactory",
    "TrackFactory",
    "TrackItemFactory",
    "AssetFactory",
]
