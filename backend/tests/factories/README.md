# Test Factories Documentation

This directory contains comprehensive test factories for all models in the AI Video Clipper project.

## Overview

All factories follow the pytest-factoryboy pattern using `factory.alchemy.SQLAlchemyModelFactory` as the base class. They use the Faker library to generate realistic test data.

## Factory Files

### Core Models (Existing)

1. **`user_factory.py`** - UserFactory
   - Traits: `verified`, `superuser`, `inactive`, `google_oauth`, `with_verification_token`, `with_reset_token`

2. **`video_factory.py`** - VideoFactory
   - Traits: `uploaded`, `processing`, `completed`, `failed`, `short`, `long`, `hd`, `uhd`

3. **`transcript_factory.py`** - TranscriptFactory
   - Traits: `processing`, `failed`, `spanish`, `russian`, `german`, `french`, `high_accuracy`, `low_accuracy`, `short`, `long`

4. **`clip_factory.py`** - ClipFactory
   - Traits: `processing`, `failed`, `short`, `medium`, `long`, `keyword_highlight`, `silence_removed`, `intro`, `outro`

### Post-MVP Features (Models to be created)

5. **`export_factory.py`** - ExportFactory
   - Traits: `pending`, `processing`, `completed`, `failed`, `hd`, `uhd`, `web_optimized`, `individual_clips`, `merged_clips`

6. **`highlight_factory.py`** - HighlightFactory
   - Traits: `high_quality`, `medium_quality`, `low_quality`, `audio_driven`, `keyword_driven`, `scene_change`, `manual`, `short`, `long`

7. **`batch_factory.py`** - BatchJobFactory, BatchVideoFactory
   - BatchJobFactory traits: `pending`, `processing`, `completed`, `failed`, `paused`, `small`, `large`, `with_failures`
   - BatchVideoFactory traits: `pending`, `processing`, `completed`, `failed`, `transcribed`, `silence_removed`, `highlights_detected`

8. **`subtitle_factory.py`** - SubtitleStyleFactory, SubtitleTranslationFactory
   - SubtitleStyleFactory traits: `preset`, `minimal`, `bold`, `gaming`, `professional`
   - SubtitleTranslationFactory traits: `pending`, `processing`, `completed`, `failed`, `spanish`, `french`, `german`, `chinese`, `japanese`, `high_confidence`, `low_cost`, `high_cost`

9. **`template_factory.py`** - SocialMediaTemplateFactory
   - Traits: `preset`, `youtube_shorts`, `tiktok`, `instagram_reels`, `instagram_story`, `twitter`, `linkedin`, `square`, `vertical`, `horizontal`, `with_background_music`, `no_captions`

10. **`collaboration_factory.py`** - OrganizationFactory, TeamMemberFactory, VideoShareFactory, CommentFactory, VersionFactory
    - OrganizationFactory traits: `free_plan`, `pro_plan`, `business_plan`, `enterprise_plan`, `inactive`
    - TeamMemberFactory traits: `owner`, `admin`, `editor`, `viewer`, `invited`, `suspended`
    - VideoShareFactory traits: `user_share`, `team_share`, `public_link`, `with_password`, `with_expiration`, `limited_views`
    - CommentFactory traits: `timeline_comment`, `reply`, `with_mentions`, `with_reactions`, `resolved`, `edited`
    - VersionFactory traits: `current`, `initial`, `auto_saved`

11. **`project_factory.py`** - ProjectFactory, TrackFactory, TrackItemFactory, AssetFactory
    - ProjectFactory traits: `draft`, `in_progress`, `rendering`, `completed`, `hd`, `uhd`, `vertical`
    - TrackFactory traits: `video_track`, `audio_track`, `image_track`, `text_track`, `locked`, `muted`
    - TrackItemFactory traits: `with_fade`, `scaled`, `rotated`, `semi_transparent`, `with_blur`, `with_color_correction`
    - AssetFactory traits: `video`, `audio`, `image`, `font`, `from_video`

12. **`__init__.py`** - Exports all factories for easy importing

## Usage Examples

### Basic Usage

```python
from tests.factories import UserFactory, VideoFactory, TranscriptFactory

# Create instances with default values
user = UserFactory()
video = VideoFactory()
transcript = TranscriptFactory()
```

### Using Traits

```python
# Create a verified user
verified_user = UserFactory(verified=True)

# Create a completed video
completed_video = VideoFactory(completed=True)

# Create a Spanish transcript with high accuracy
spanish_transcript = TranscriptFactory(spanish=True, high_accuracy=True)

# Create a failed export
failed_export = ExportFactory(failed=True)
```

### Custom Values

```python
# Override specific fields
user = UserFactory(email="test@example.com", full_name="Test User")

# Create related objects
video = VideoFactory(user_id=user.id, title="My Test Video")
transcript = TranscriptFactory(video_id=video.id)
```

### Complex Scenarios

```python
# Create a complete video processing workflow
user = UserFactory(verified=True)
video = VideoFactory(user_id=user.id, completed=True)
transcript = TranscriptFactory(video_id=video.id, high_accuracy=True)
clip = ClipFactory(video_id=video.id, keyword_highlight=True)
export = ExportFactory(video_id=video.id, user_id=user.id, hd=True, completed=True)

# Create a batch processing job
batch_job = BatchJobFactory(user_id=user.id, processing=True, large=True)
batch_videos = [
    BatchVideoFactory(batch_job_id=batch_job.id, completed=True)
    for _ in range(5)
]

# Create collaboration scenario
org = OrganizationFactory(owner_id=user.id, business_plan=True)
admin = TeamMemberFactory(organization_id=org.id, user_id=user.id, admin=True)
share = VideoShareFactory(video_id=video.id, public_link=True, with_expiration=True)
comment = CommentFactory(video_id=video.id, user_id=user.id, timeline_comment=True)
```

### Using in Tests

```python
import pytest
from tests.factories import UserFactory, VideoFactory

@pytest.fixture
def user(db_session):
    """Create a test user."""
    return UserFactory()

@pytest.fixture
def completed_video(db_session, user):
    """Create a completed video for testing."""
    return VideoFactory(user_id=user.id, completed=True)

def test_video_export(completed_video):
    """Test video export functionality."""
    export = ExportFactory(video_id=completed_video.id, hd=True)
    assert export.resolution == "1080p"
    assert export.status == "pending"
```

## Important Notes

### For Models Not Yet Created

Some factories (Export, Highlight, BatchJob, SubtitleStyle, etc.) reference models that don't exist yet. These are based on the comprehensive specifications in `agent-os/specs/`. When implementing these models:

1. Uncomment the `model` line in the Meta class:
   ```python
   class Meta:
       model = Export  # Uncomment when model is created
       sqlalchemy_session_persistence = "commit"
   ```

2. Add the proper import at the top of the file:
   ```python
   from app.models.export import Export
   ```

### Database Session

Factories use `sqlalchemy_session_persistence = "commit"` which means they will commit objects to the database. Make sure your test setup includes proper database fixtures.

### Faker Randomization

Since factories use Faker, generated values will be different each time. For deterministic tests, set specific values:

```python
# Random each time
user1 = UserFactory()
user2 = UserFactory()

# Deterministic
user1 = UserFactory(email="user1@example.com")
user2 = UserFactory(email="user2@example.com")
```

## Factory Pattern Best Practices

1. **Use traits for common scenarios** instead of overriding multiple fields
2. **Create related objects together** to ensure referential integrity
3. **Use LazyAttribute** for computed fields that depend on other fields
4. **Keep factories DRY** by using traits and inheritance
5. **Document custom traits** in factory docstrings

## Related Documentation

- **PRD.md** - Product requirements and feature specifications
- **.claude/TASKS.md** - Feature implementation status
- **agent-os/specs/** - Detailed specifications for all features

## Contributing

When adding new models:

1. Create a factory file in this directory
2. Follow the existing pattern (SQLAlchemyModelFactory base, Faker usage, traits)
3. Add the factory to `__init__.py` exports
4. Document traits in this README
5. Add usage examples for complex models
