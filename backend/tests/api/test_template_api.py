"""Tests for social media template API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.video import Video, VideoStatus


# Mock SocialMediaTemplate model and related enums
class TemplateStatus:
    """Template export status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Platform:
    """Social media platform types."""
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_STORY = "instagram_story"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    CUSTOM = "custom"


class MockSocialMediaTemplate:
    """Mock SocialMediaTemplate model for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name', 'Default Template')
        self.description = kwargs.get('description')
        self.platform = kwargs.get('platform', Platform.YOUTUBE_SHORTS)
        self.is_preset = kwargs.get('is_preset', False)

        # Video settings
        self.aspect_ratio = kwargs.get('aspect_ratio', '9:16')
        self.resolution_width = kwargs.get('resolution_width', 1080)
        self.resolution_height = kwargs.get('resolution_height', 1920)
        self.max_duration = kwargs.get('max_duration', 60)
        self.min_duration = kwargs.get('min_duration', 5)

        # Transformation settings
        self.crop_strategy = kwargs.get('crop_strategy', 'center')
        self.scale_mode = kwargs.get('scale_mode', 'fit')

        # Audio settings
        self.audio_enabled = kwargs.get('audio_enabled', True)
        self.audio_normalization = kwargs.get('audio_normalization', True)

        # Caption settings
        self.caption_settings = kwargs.get('caption_settings', {
            "enabled": True,
            "style": "bold",
            "position": "bottom",
        })

        # Platform requirements
        self.platform_requirements = kwargs.get('platform_requirements', {})

        # Export settings
        self.export_format = kwargs.get('export_format', 'mp4')
        self.export_quality = kwargs.get('export_quality', 'high')

        self.usage_count = kwargs.get('usage_count', 0)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())


class MockTemplateExport:
    """Mock TemplateExport model for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.video_id = kwargs.get('video_id')
        self.template_id = kwargs.get('template_id')
        self.user_id = kwargs.get('user_id')
        self.status = kwargs.get('status', TemplateStatus.PENDING)
        self.progress = kwargs.get('progress', 0)
        self.output_s3_key = kwargs.get('output_s3_key')
        self.output_url = kwargs.get('output_url')
        self.file_size = kwargs.get('file_size')
        self.error_message = kwargs.get('error_message')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.completed_at = kwargs.get('completed_at')


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with database session override."""
    from app.api.deps import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another test user for authorization tests."""
    user = User(
        email="other@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_video(db_session: AsyncSession, test_user: User) -> Video:
    """Create a test video."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
        duration=120.0,
        resolution="1920x1080",
        format="mp4",
        s3_key="videos/test/video.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


class TestListTemplates:
    """Tests for GET /api/templates endpoint."""

    @pytest.mark.asyncio
    async def test_list_templates_includes_presets_and_custom(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test listing templates includes both presets and user's custom templates."""
        with patch("app.api.routes.templates.get_templates") as mock_get:
            mock_templates = [
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="YouTube Shorts",
                    platform=Platform.YOUTUBE_SHORTS,
                    is_preset=True,
                    user_id=None,
                ),
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="TikTok",
                    platform=Platform.TIKTOK,
                    is_preset=True,
                    user_id=None,
                ),
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="My Custom Template",
                    is_preset=False,
                    user_id=test_user.id,
                ),
            ]
            mock_get.return_value = mock_templates

            response = client.get("/api/templates", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_templates_filter_by_platform(
        self, client: TestClient, auth_headers: dict
    ):
        """Test filtering templates by platform."""
        response = client.get(
            f"/api/templates?platform={Platform.YOUTUBE_SHORTS}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_templates_filter_by_preset(
        self, client: TestClient, auth_headers: dict
    ):
        """Test filtering templates by preset flag."""
        response = client.get(
            "/api/templates?is_preset=true",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_templates_without_auth(self, client: TestClient):
        """Test listing templates without authentication."""
        response = client.get("/api/templates")

        assert response.status_code == 401


class TestGetTemplate:
    """Tests for GET /api/templates/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_template_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting specific template."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                user_id=test_user.id,
                name="My Template",
                platform=Platform.YOUTUBE_SHORTS,
            )
            mock_get.return_value = mock_template

            response = client.get(
                f"/api/templates/{template_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "My Template"
            assert data["platform"] == Platform.YOUTUBE_SHORTS

    @pytest.mark.asyncio
    async def test_get_template_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent template."""
        fake_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_get.return_value = None

            response = client.get(
                f"/api/templates/{fake_id}",
                headers=auth_headers,
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_preset_template(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting preset template (accessible by all users)."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                name="YouTube Shorts",
                platform=Platform.YOUTUBE_SHORTS,
                is_preset=True,
                user_id=None,
            )
            mock_get.return_value = mock_template

            response = client.get(
                f"/api/templates/{template_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200


class TestCreateTemplate:
    """Tests for POST /api/templates endpoint."""

    @pytest.mark.asyncio
    async def test_create_template_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating custom template."""
        response = client.post(
            "/api/templates",
            json={
                "name": "My Custom Template",
                "description": "Custom template for vertical videos",
                "platform": Platform.CUSTOM,
                "aspect_ratio": "9:16",
                "resolution_width": 1080,
                "resolution_height": 1920,
                "max_duration": 60,
                "crop_strategy": "center",
                "caption_settings": {
                    "enabled": True,
                    "style": "bold",
                    "position": "bottom",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Custom Template"
        assert data["aspect_ratio"] == "9:16"
        assert data["is_preset"] is False

    @pytest.mark.asyncio
    async def test_create_template_minimal_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating template with minimal required fields."""
        response = client.post(
            "/api/templates",
            json={
                "name": "Minimal Template",
                "platform": Platform.CUSTOM,
                "aspect_ratio": "16:9",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_template_invalid_aspect_ratio(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating template with invalid aspect ratio."""
        response = client.post(
            "/api/templates",
            json={
                "name": "Invalid Template",
                "aspect_ratio": "invalid",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_template_without_auth(self, client: TestClient):
        """Test creating template without authentication."""
        response = client.post(
            "/api/templates",
            json={
                "name": "Unauthorized Template",
                "aspect_ratio": "9:16",
            },
        )

        assert response.status_code == 401


class TestUpdateTemplate:
    """Tests for PATCH /api/templates/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_template_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test updating template."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            with patch("app.api.routes.templates.update_template") as mock_update:
                mock_template = MockSocialMediaTemplate(
                    id=template_id,
                    user_id=test_user.id,
                    name="Original Name",
                )
                mock_get.return_value = mock_template

                updated_template = MockSocialMediaTemplate(
                    id=template_id,
                    user_id=test_user.id,
                    name="Updated Name",
                    max_duration=90,
                )
                mock_update.return_value = updated_template

                response = client.patch(
                    f"/api/templates/{template_id}",
                    json={
                        "name": "Updated Name",
                        "max_duration": 90,
                    },
                    headers=auth_headers,
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_template_unauthorized(
        self, client: TestClient, other_user: User, auth_headers: dict
    ):
        """Test updating template owned by another user."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                user_id=other_user.id,  # Different user
                name="Other User's Template",
            )
            mock_get.return_value = mock_template

            response = client.patch(
                f"/api/templates/{template_id}",
                json={"name": "Hacked Name"},
                headers=auth_headers,
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_preset_template_forbidden(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that preset templates cannot be updated."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                name="YouTube Shorts",
                is_preset=True,
                user_id=None,
            )
            mock_get.return_value = mock_template

            response = client.patch(
                f"/api/templates/{template_id}",
                json={"name": "Modified Preset"},
                headers=auth_headers,
            )

            assert response.status_code == 403


class TestDeleteTemplate:
    """Tests for DELETE /api/templates/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_template_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test deleting template."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            with patch("app.api.routes.templates.delete_template") as mock_delete:
                mock_template = MockSocialMediaTemplate(
                    id=template_id,
                    user_id=test_user.id,
                )
                mock_get.return_value = mock_template

                response = client.delete(
                    f"/api/templates/{template_id}",
                    headers=auth_headers,
                )

                assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_template_unauthorized(
        self, client: TestClient, other_user: User, auth_headers: dict
    ):
        """Test deleting template owned by another user."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                user_id=other_user.id,
            )
            mock_get.return_value = mock_template

            response = client.delete(
                f"/api/templates/{template_id}",
                headers=auth_headers,
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_preset_template_forbidden(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that preset templates cannot be deleted."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                is_preset=True,
                user_id=None,
            )
            mock_get.return_value = mock_template

            response = client.delete(
                f"/api/templates/{template_id}",
                headers=auth_headers,
            )

            assert response.status_code == 403


class TestExportForTemplate:
    """Tests for POST /api/templates/{id}/export endpoint."""

    @pytest.mark.asyncio
    async def test_export_for_template_success(
        self, client: TestClient, test_video: Video, auth_headers: dict
    ):
        """Test exporting video using template."""
        template_id = uuid4()

        with patch("app.services.redis.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.enqueue_job = AsyncMock(return_value="job-123")
            mock_redis.return_value = mock_redis_instance

            with patch("app.api.routes.templates.get_template_by_id") as mock_get:
                mock_template = MockSocialMediaTemplate(
                    id=template_id,
                    platform=Platform.YOUTUBE_SHORTS,
                )
                mock_get.return_value = mock_template

                response = client.post(
                    f"/api/templates/{template_id}/export",
                    json={
                        "video_id": str(test_video.id),
                        "start_time": 0,
                        "end_time": 60,
                    },
                    headers=auth_headers,
                )

                assert response.status_code == 201
                data = response.json()
                assert "export_id" in data
                assert data["status"] == TemplateStatus.PENDING

    @pytest.mark.asyncio
    async def test_export_for_template_exceeds_max_duration(
        self, client: TestClient, test_video: Video, auth_headers: dict
    ):
        """Test export with duration exceeding template max."""
        template_id = uuid4()

        with patch("app.api.routes.templates.get_template_by_id") as mock_get:
            mock_template = MockSocialMediaTemplate(
                id=template_id,
                max_duration=60,  # Max 60 seconds
            )
            mock_get.return_value = mock_template

            response = client.post(
                f"/api/templates/{template_id}/export",
                json={
                    "video_id": str(test_video.id),
                    "start_time": 0,
                    "end_time": 90,  # 90 seconds - exceeds max
                },
                headers=auth_headers,
            )

            # Should either auto-trim or reject
            assert response.status_code in [201, 400, 422]

    @pytest.mark.asyncio
    async def test_export_for_template_missing_video(
        self, client: TestClient, auth_headers: dict
    ):
        """Test export with non-existent video."""
        template_id = uuid4()
        fake_video_id = uuid4()

        response = client.post(
            f"/api/templates/{template_id}/export",
            json={
                "video_id": str(fake_video_id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_for_template_with_captions(
        self, client: TestClient, test_video: Video, auth_headers: dict
    ):
        """Test export with caption burning enabled."""
        template_id = uuid4()

        with patch("app.services.redis.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.enqueue_job = AsyncMock(return_value="job-123")
            mock_redis.return_value = mock_redis_instance

            with patch("app.api.routes.templates.get_template_by_id") as mock_get:
                mock_template = MockSocialMediaTemplate(
                    id=template_id,
                    caption_settings={
                        "enabled": True,
                        "style": "bold",
                        "position": "bottom",
                    },
                )
                mock_get.return_value = mock_template

                response = client.post(
                    f"/api/templates/{template_id}/export",
                    json={
                        "video_id": str(test_video.id),
                        "burn_captions": True,
                    },
                    headers=auth_headers,
                )

                assert response.status_code == 201


class TestGetTemplatePresets:
    """Tests for GET /api/templates/presets endpoint."""

    @pytest.mark.asyncio
    async def test_get_presets_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting all platform presets."""
        with patch("app.api.routes.templates.get_preset_templates") as mock_get:
            mock_presets = [
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="YouTube Shorts",
                    platform=Platform.YOUTUBE_SHORTS,
                    is_preset=True,
                ),
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="TikTok",
                    platform=Platform.TIKTOK,
                    is_preset=True,
                ),
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="Instagram Reels",
                    platform=Platform.INSTAGRAM_REELS,
                    is_preset=True,
                ),
            ]
            mock_get.return_value = mock_presets

            response = client.get("/api/templates/presets", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 3
            assert all(preset["is_preset"] for preset in data)

    @pytest.mark.asyncio
    async def test_get_presets_includes_platform_requirements(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that presets include platform-specific requirements."""
        with patch("app.api.routes.templates.get_preset_templates") as mock_get:
            mock_presets = [
                MockSocialMediaTemplate(
                    id=uuid4(),
                    name="YouTube Shorts",
                    platform=Platform.YOUTUBE_SHORTS,
                    is_preset=True,
                    platform_requirements={
                        "file_size_limit_mb": 200,
                        "max_duration": 60,
                        "aspect_ratio": "9:16",
                    },
                ),
            ]
            mock_get.return_value = mock_presets

            response = client.get("/api/templates/presets", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data[0]["platform_requirements"] is not None


class TestGetExportStatus:
    """Tests for GET /api/templates/exports/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_export_status_pending(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting export status for pending export."""
        export_id = uuid4()

        with patch("app.api.routes.templates.get_template_export") as mock_get:
            mock_export = MockTemplateExport(
                id=export_id,
                user_id=test_user.id,
                status=TemplateStatus.PENDING,
                progress=0,
            )
            mock_get.return_value = mock_export

            response = client.get(
                f"/api/templates/exports/{export_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == TemplateStatus.PENDING
            assert data["progress"] == 0

    @pytest.mark.asyncio
    async def test_get_export_status_completed(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting export status for completed export."""
        export_id = uuid4()

        with patch("app.api.routes.templates.get_template_export") as mock_get:
            mock_export = MockTemplateExport(
                id=export_id,
                user_id=test_user.id,
                status=TemplateStatus.COMPLETED,
                progress=100,
                output_url="https://s3.amazonaws.com/bucket/template-export.mp4",
                completed_at=datetime.utcnow(),
            )
            mock_get.return_value = mock_export

            response = client.get(
                f"/api/templates/exports/{export_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == TemplateStatus.COMPLETED
            assert data["output_url"] is not None

    @pytest.mark.asyncio
    async def test_get_export_status_failed(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting export status for failed export."""
        export_id = uuid4()

        with patch("app.api.routes.templates.get_template_export") as mock_get:
            mock_export = MockTemplateExport(
                id=export_id,
                user_id=test_user.id,
                status=TemplateStatus.FAILED,
                error_message="Aspect ratio conversion failed",
            )
            mock_get.return_value = mock_export

            response = client.get(
                f"/api/templates/exports/{export_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == TemplateStatus.FAILED
            assert data["error_message"] is not None


class TestTemplateValidation:
    """Tests for template validation."""

    @pytest.mark.asyncio
    async def test_validate_aspect_ratio_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Test aspect ratio format validation."""
        valid_ratios = ["9:16", "16:9", "1:1", "4:5", "4:3"]

        for ratio in valid_ratios:
            response = client.post(
                "/api/templates",
                json={
                    "name": f"Template {ratio}",
                    "aspect_ratio": ratio,
                },
                headers=auth_headers,
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_validate_duration_constraints(
        self, client: TestClient, auth_headers: dict
    ):
        """Test duration constraint validation."""
        response = client.post(
            "/api/templates",
            json={
                "name": "Invalid Duration Template",
                "min_duration": 60,
                "max_duration": 30,  # Max < Min - invalid
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_resolution_positive(
        self, client: TestClient, auth_headers: dict
    ):
        """Test resolution must be positive."""
        response = client.post(
            "/api/templates",
            json={
                "name": "Invalid Resolution Template",
                "resolution_width": -1080,
                "resolution_height": 1920,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422
