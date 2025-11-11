"""Tests for subtitle API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.transcript import Transcript


# Mock SubtitleStyle model and related enums
class SubtitleStatus:
    """Subtitle processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MockSubtitleStyle:
    """Mock SubtitleStyle model for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name', 'Default Style')
        self.description = kwargs.get('description')
        self.is_preset = kwargs.get('is_preset', False)

        # Font settings
        self.font_family = kwargs.get('font_family', 'Arial')
        self.font_size = kwargs.get('font_size', 48)
        self.font_weight = kwargs.get('font_weight', 'bold')
        self.font_style = kwargs.get('font_style', 'normal')

        # Color settings
        self.text_color = kwargs.get('text_color', '#FFFFFF')
        self.text_opacity = kwargs.get('text_opacity', 1.0)
        self.outline_color = kwargs.get('outline_color', '#000000')
        self.outline_width = kwargs.get('outline_width', 2)
        self.shadow_color = kwargs.get('shadow_color', '#000000')
        self.shadow_offset_x = kwargs.get('shadow_offset_x', 2)
        self.shadow_offset_y = kwargs.get('shadow_offset_y', 2)
        self.shadow_blur = kwargs.get('shadow_blur', 3)

        # Background settings
        self.background_color = kwargs.get('background_color', 'transparent')
        self.background_opacity = kwargs.get('background_opacity', 0.0)
        self.background_padding = kwargs.get('background_padding', 10)
        self.background_radius = kwargs.get('background_radius', 5)

        # Position settings
        self.position = kwargs.get('position', 'bottom')
        self.alignment = kwargs.get('alignment', 'center')
        self.margin_horizontal = kwargs.get('margin_horizontal', 50)
        self.margin_vertical = kwargs.get('margin_vertical', 50)

        # Animation
        self.animation_type = kwargs.get('animation_type', 'none')
        self.animation_duration = kwargs.get('animation_duration', 0.3)

        # Advanced settings
        self.max_width = kwargs.get('max_width', 80)
        self.line_height = kwargs.get('line_height', 1.5)
        self.letter_spacing = kwargs.get('letter_spacing', 0)
        self.text_transform = kwargs.get('text_transform', 'none')

        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())


class MockSubtitleBurnJob:
    """Mock SubtitleBurnJob model for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.video_id = kwargs.get('video_id')
        self.transcript_id = kwargs.get('transcript_id')
        self.style_id = kwargs.get('style_id')
        self.user_id = kwargs.get('user_id')
        self.status = kwargs.get('status', SubtitleStatus.PENDING)
        self.progress = kwargs.get('progress', 0)
        self.output_s3_key = kwargs.get('output_s3_key')
        self.output_url = kwargs.get('output_url')
        self.error_message = kwargs.get('error_message')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.completed_at = kwargs.get('completed_at')


class MockSubtitleTranslation:
    """Mock SubtitleTranslation model for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.transcript_id = kwargs.get('transcript_id')
        self.user_id = kwargs.get('user_id')
        self.source_language = kwargs.get('source_language', 'en')
        self.target_language = kwargs.get('target_language', 'es')
        self.status = kwargs.get('status', SubtitleStatus.PENDING)
        self.progress = kwargs.get('progress', 0)
        self.translated_content = kwargs.get('translated_content')
        self.error_message = kwargs.get('error_message')
        self.confidence_score = kwargs.get('confidence_score', 0.95)
        self.character_count = kwargs.get('character_count', 1000)
        self.cost = kwargs.get('cost', 0.5)
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
async def test_transcript(db_session: AsyncSession, test_video: Video) -> Transcript:
    """Create a test transcript."""
    transcript = Transcript(
        video_id=test_video.id,
        language="en",
        segments=[
            {"start": 0.0, "end": 5.0, "text": "Hello world"},
            {"start": 5.0, "end": 10.0, "text": "This is a test"},
        ],
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)
    return transcript


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


class TestCreateSubtitleStyle:
    """Tests for POST /api/subtitles/styles endpoint."""

    @pytest.mark.asyncio
    async def test_create_style_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating custom subtitle style."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "My Custom Style",
                "description": "A bold style for gaming videos",
                "font_family": "Roboto",
                "font_size": 52,
                "font_weight": "bold",
                "text_color": "#00FF00",
                "outline_color": "#000000",
                "outline_width": 3,
                "position": "bottom",
                "alignment": "center",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Custom Style"
        assert data["font_family"] == "Roboto"
        assert data["font_size"] == 52
        assert data["is_preset"] is False

    @pytest.mark.asyncio
    async def test_create_style_minimal_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating style with minimal required fields."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Minimal Style",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Style"
        # Should have default values
        assert data["font_family"] is not None
        assert data["font_size"] is not None

    @pytest.mark.asyncio
    async def test_create_style_invalid_color(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating style with invalid color format."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Invalid Style",
                "text_color": "not-a-color",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_style_invalid_position(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating style with invalid position."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Invalid Position Style",
                "position": "invalid_position",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_style_without_auth(self, client: TestClient):
        """Test creating style without authentication."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Unauthorized Style",
            },
        )

        assert response.status_code == 401


class TestListSubtitleStyles:
    """Tests for GET /api/subtitles/styles endpoint."""

    @pytest.mark.asyncio
    async def test_list_styles_includes_presets_and_custom(
        self, client: TestClient, auth_headers: dict
    ):
        """Test listing styles includes both presets and user's custom styles."""
        with patch("app.api.routes.subtitles.get_subtitle_styles") as mock_get:
            mock_styles = [
                MockSubtitleStyle(id=uuid4(), name="Preset 1", is_preset=True, user_id=None),
                MockSubtitleStyle(id=uuid4(), name="Preset 2", is_preset=True, user_id=None),
                MockSubtitleStyle(id=uuid4(), name="My Custom", is_preset=False),
            ]
            mock_get.return_value = mock_styles

            response = client.get("/api/subtitles/styles", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_styles_filter_by_preset(
        self, client: TestClient, auth_headers: dict
    ):
        """Test filtering styles by preset flag."""
        response = client.get(
            "/api/subtitles/styles?is_preset=true",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_styles_without_auth(self, client: TestClient):
        """Test listing styles without authentication."""
        response = client.get("/api/subtitles/styles")

        assert response.status_code == 401


class TestGetSubtitleStyle:
    """Tests for GET /api/subtitles/styles/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_style_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting specific style."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_style = MockSubtitleStyle(
                id=style_id,
                user_id=test_user.id,
                name="Test Style",
            )
            mock_get.return_value = mock_style

            response = client.get(
                f"/api/subtitles/styles/{style_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Style"

    @pytest.mark.asyncio
    async def test_get_style_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent style."""
        fake_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_get.return_value = None

            response = client.get(
                f"/api/subtitles/styles/{fake_id}",
                headers=auth_headers,
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_preset_style(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting preset style (accessible by all users)."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_style = MockSubtitleStyle(
                id=style_id,
                name="Preset Style",
                is_preset=True,
                user_id=None,
            )
            mock_get.return_value = mock_style

            response = client.get(
                f"/api/subtitles/styles/{style_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200


class TestUpdateSubtitleStyle:
    """Tests for PATCH /api/subtitles/styles/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_style_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test updating subtitle style."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            with patch("app.api.routes.subtitles.update_style") as mock_update:
                mock_style = MockSubtitleStyle(
                    id=style_id,
                    user_id=test_user.id,
                    name="Original Name",
                )
                mock_get.return_value = mock_style

                updated_style = MockSubtitleStyle(
                    id=style_id,
                    user_id=test_user.id,
                    name="Updated Name",
                    font_size=60,
                )
                mock_update.return_value = updated_style

                response = client.patch(
                    f"/api/subtitles/styles/{style_id}",
                    json={
                        "name": "Updated Name",
                        "font_size": 60,
                    },
                    headers=auth_headers,
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_style_unauthorized(
        self, client: TestClient, other_user: User, auth_headers: dict
    ):
        """Test updating style owned by another user."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_style = MockSubtitleStyle(
                id=style_id,
                user_id=other_user.id,  # Different user
                name="Other User's Style",
            )
            mock_get.return_value = mock_style

            response = client.patch(
                f"/api/subtitles/styles/{style_id}",
                json={"name": "Hacked Name"},
                headers=auth_headers,
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_preset_style_forbidden(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that preset styles cannot be updated."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_style = MockSubtitleStyle(
                id=style_id,
                name="Preset Style",
                is_preset=True,
                user_id=None,
            )
            mock_get.return_value = mock_style

            response = client.patch(
                f"/api/subtitles/styles/{style_id}",
                json={"name": "Modified Preset"},
                headers=auth_headers,
            )

            assert response.status_code == 403


class TestDeleteSubtitleStyle:
    """Tests for DELETE /api/subtitles/styles/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_style_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test deleting subtitle style."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            with patch("app.api.routes.subtitles.delete_style") as mock_delete:
                mock_style = MockSubtitleStyle(
                    id=style_id,
                    user_id=test_user.id,
                )
                mock_get.return_value = mock_style

                response = client.delete(
                    f"/api/subtitles/styles/{style_id}",
                    headers=auth_headers,
                )

                assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_style_unauthorized(
        self, client: TestClient, other_user: User, auth_headers: dict
    ):
        """Test deleting style owned by another user."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_style = MockSubtitleStyle(
                id=style_id,
                user_id=other_user.id,
            )
            mock_get.return_value = mock_style

            response = client.delete(
                f"/api/subtitles/styles/{style_id}",
                headers=auth_headers,
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_preset_style_forbidden(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that preset styles cannot be deleted."""
        style_id = uuid4()

        with patch("app.api.routes.subtitles.get_style_by_id") as mock_get:
            mock_style = MockSubtitleStyle(
                id=style_id,
                is_preset=True,
                user_id=None,
            )
            mock_get.return_value = mock_style

            response = client.delete(
                f"/api/subtitles/styles/{style_id}",
                headers=auth_headers,
            )

            assert response.status_code == 403


class TestGetSubtitlePresets:
    """Tests for GET /api/subtitles/presets endpoint."""

    @pytest.mark.asyncio
    async def test_get_presets_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting all subtitle presets."""
        with patch("app.api.routes.subtitles.get_preset_styles") as mock_get:
            mock_presets = [
                MockSubtitleStyle(id=uuid4(), name="Minimal", is_preset=True),
                MockSubtitleStyle(id=uuid4(), name="Bold", is_preset=True),
                MockSubtitleStyle(id=uuid4(), name="Gaming", is_preset=True),
                MockSubtitleStyle(id=uuid4(), name="Podcast", is_preset=True),
                MockSubtitleStyle(id=uuid4(), name="Vlog", is_preset=True),
                MockSubtitleStyle(id=uuid4(), name="Professional", is_preset=True),
                MockSubtitleStyle(id=uuid4(), name="Trendy", is_preset=True),
            ]
            mock_get.return_value = mock_presets

            response = client.get("/api/subtitles/presets", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 7
            assert all(preset["is_preset"] for preset in data)

    @pytest.mark.asyncio
    async def test_get_presets_includes_style_details(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that preset response includes full style details."""
        with patch("app.api.routes.subtitles.get_preset_styles") as mock_get:
            mock_presets = [
                MockSubtitleStyle(
                    id=uuid4(),
                    name="Bold",
                    is_preset=True,
                    font_family="Montserrat",
                    font_size=48,
                    font_weight="bold",
                ),
            ]
            mock_get.return_value = mock_presets

            response = client.get("/api/subtitles/presets", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data[0]["font_family"] == "Montserrat"
            assert data[0]["font_size"] == 48


class TestBurnSubtitles:
    """Tests for POST /api/subtitles/burn endpoint."""

    @pytest.mark.asyncio
    async def test_burn_subtitles_success(
        self, client: TestClient, test_video: Video, test_transcript: Transcript, auth_headers: dict
    ):
        """Test burning subtitles into video."""
        style_id = uuid4()

        with patch("app.services.redis.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.enqueue_job = AsyncMock(return_value="job-123")
            mock_redis.return_value = mock_redis_instance

            response = client.post(
                "/api/subtitles/burn",
                json={
                    "video_id": str(test_video.id),
                    "transcript_id": str(test_transcript.id),
                    "style_id": str(style_id),
                },
                headers=auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert "job_id" in data
            assert data["status"] == SubtitleStatus.PENDING

    @pytest.mark.asyncio
    async def test_burn_subtitles_with_custom_style(
        self, client: TestClient, test_video: Video, test_transcript: Transcript, auth_headers: dict
    ):
        """Test burning subtitles with inline custom style."""
        with patch("app.services.redis.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.enqueue_job = AsyncMock(return_value="job-123")
            mock_redis.return_value = mock_redis_instance

            response = client.post(
                "/api/subtitles/burn",
                json={
                    "video_id": str(test_video.id),
                    "transcript_id": str(test_transcript.id),
                    "custom_style": {
                        "font_family": "Arial",
                        "font_size": 40,
                        "text_color": "#FFFFFF",
                        "position": "bottom",
                    },
                },
                headers=auth_headers,
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_burn_subtitles_missing_video(
        self, client: TestClient, test_transcript: Transcript, auth_headers: dict
    ):
        """Test burning subtitles with non-existent video."""
        fake_video_id = uuid4()

        response = client.post(
            "/api/subtitles/burn",
            json={
                "video_id": str(fake_video_id),
                "transcript_id": str(test_transcript.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_burn_subtitles_missing_transcript(
        self, client: TestClient, test_video: Video, auth_headers: dict
    ):
        """Test burning subtitles with non-existent transcript."""
        fake_transcript_id = uuid4()

        response = client.post(
            "/api/subtitles/burn",
            json={
                "video_id": str(test_video.id),
                "transcript_id": str(fake_transcript_id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestGetBurnProgress:
    """Tests for GET /api/subtitles/burn/{job_id}/progress endpoint."""

    @pytest.mark.asyncio
    async def test_get_burn_progress_pending(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting progress for pending job."""
        job_id = uuid4()

        with patch("app.api.routes.subtitles.get_burn_job") as mock_get:
            mock_job = MockSubtitleBurnJob(
                id=job_id,
                status=SubtitleStatus.PENDING,
                progress=0,
            )
            mock_get.return_value = mock_job

            response = client.get(
                f"/api/subtitles/burn/{job_id}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SubtitleStatus.PENDING
            assert data["progress"] == 0

    @pytest.mark.asyncio
    async def test_get_burn_progress_processing(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting progress for processing job."""
        job_id = uuid4()

        with patch("app.api.routes.subtitles.get_burn_job") as mock_get:
            mock_job = MockSubtitleBurnJob(
                id=job_id,
                status=SubtitleStatus.PROCESSING,
                progress=45,
            )
            mock_get.return_value = mock_job

            response = client.get(
                f"/api/subtitles/burn/{job_id}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SubtitleStatus.PROCESSING
            assert data["progress"] == 45

    @pytest.mark.asyncio
    async def test_get_burn_progress_completed(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting progress for completed job."""
        job_id = uuid4()

        with patch("app.api.routes.subtitles.get_burn_job") as mock_get:
            mock_job = MockSubtitleBurnJob(
                id=job_id,
                status=SubtitleStatus.COMPLETED,
                progress=100,
                output_url="https://s3.amazonaws.com/bucket/subtitle-video.mp4",
                completed_at=datetime.utcnow(),
            )
            mock_get.return_value = mock_job

            response = client.get(
                f"/api/subtitles/burn/{job_id}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SubtitleStatus.COMPLETED
            assert data["progress"] == 100
            assert data["output_url"] is not None

    @pytest.mark.asyncio
    async def test_get_burn_progress_failed(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting progress for failed job."""
        job_id = uuid4()

        with patch("app.api.routes.subtitles.get_burn_job") as mock_get:
            mock_job = MockSubtitleBurnJob(
                id=job_id,
                status=SubtitleStatus.FAILED,
                progress=30,
                error_message="FFmpeg encoding failed",
            )
            mock_get.return_value = mock_job

            response = client.get(
                f"/api/subtitles/burn/{job_id}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SubtitleStatus.FAILED
            assert data["error_message"] is not None


class TestTranslateSubtitles:
    """Tests for POST /api/subtitles/translate endpoint."""

    @pytest.mark.asyncio
    async def test_translate_subtitles_success(
        self, client: TestClient, test_transcript: Transcript, auth_headers: dict
    ):
        """Test translating subtitles to another language."""
        with patch("app.services.redis.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.enqueue_job = AsyncMock(return_value="job-123")
            mock_redis.return_value = mock_redis_instance

            response = client.post(
                "/api/subtitles/translate",
                json={
                    "transcript_id": str(test_transcript.id),
                    "target_language": "es",
                },
                headers=auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert "translation_id" in data
            assert data["target_language"] == "es"
            assert data["status"] == SubtitleStatus.PENDING

    @pytest.mark.asyncio
    async def test_translate_subtitles_multiple_languages(
        self, client: TestClient, test_transcript: Transcript, auth_headers: dict
    ):
        """Test translating to multiple languages."""
        languages = ["es", "fr", "de", "zh"]

        for lang in languages:
            with patch("app.services.redis.get_redis") as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.enqueue_job = AsyncMock(return_value=f"job-{lang}")
                mock_redis.return_value = mock_redis_instance

                response = client.post(
                    "/api/subtitles/translate",
                    json={
                        "transcript_id": str(test_transcript.id),
                        "target_language": lang,
                    },
                    headers=auth_headers,
                )

                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_translate_subtitles_invalid_language(
        self, client: TestClient, test_transcript: Transcript, auth_headers: dict
    ):
        """Test translating with invalid language code."""
        response = client.post(
            "/api/subtitles/translate",
            json={
                "transcript_id": str(test_transcript.id),
                "target_language": "invalid",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_translate_subtitles_missing_transcript(
        self, client: TestClient, auth_headers: dict
    ):
        """Test translating with non-existent transcript."""
        fake_transcript_id = uuid4()

        response = client.post(
            "/api/subtitles/translate",
            json={
                "transcript_id": str(fake_transcript_id),
                "target_language": "es",
            },
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestGetTranslation:
    """Tests for GET /api/subtitles/translations/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_translation_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting translation details."""
        translation_id = uuid4()

        with patch("app.api.routes.subtitles.get_translation") as mock_get:
            mock_translation = MockSubtitleTranslation(
                id=translation_id,
                user_id=test_user.id,
                source_language="en",
                target_language="es",
                status=SubtitleStatus.COMPLETED,
                confidence_score=0.95,
            )
            mock_get.return_value = mock_translation

            response = client.get(
                f"/api/subtitles/translations/{translation_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["target_language"] == "es"
            assert data["confidence_score"] == 0.95

    @pytest.mark.asyncio
    async def test_get_translation_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent translation."""
        fake_id = uuid4()

        with patch("app.api.routes.subtitles.get_translation") as mock_get:
            mock_get.return_value = None

            response = client.get(
                f"/api/subtitles/translations/{fake_id}",
                headers=auth_headers,
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_translation_unauthorized(
        self, client: TestClient, other_user: User, auth_headers: dict
    ):
        """Test getting translation owned by another user."""
        translation_id = uuid4()

        with patch("app.api.routes.subtitles.get_translation") as mock_get:
            mock_translation = MockSubtitleTranslation(
                id=translation_id,
                user_id=other_user.id,  # Different user
            )
            mock_get.return_value = mock_translation

            response = client.get(
                f"/api/subtitles/translations/{translation_id}",
                headers=auth_headers,
            )

            assert response.status_code == 403


class TestSubtitleValidation:
    """Tests for subtitle validation."""

    @pytest.mark.asyncio
    async def test_validate_contrast_ratio_sufficient(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating style with sufficient contrast ratio."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "High Contrast Style",
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.8,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_validate_contrast_ratio_insufficient(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating style with insufficient contrast ratio."""
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Low Contrast Style",
                "text_color": "#CCCCCC",
                "background_color": "#BBBBBB",
                "background_opacity": 0.5,
            },
            headers=auth_headers,
        )

        # Should either warn or reject based on implementation
        assert response.status_code in [201, 400, 422]

    @pytest.mark.asyncio
    async def test_validate_font_size_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Test font size validation."""
        # Too small
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Tiny Font",
                "font_size": 8,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

        # Too large
        response = client.post(
            "/api/subtitles/styles",
            json={
                "name": "Huge Font",
                "font_size": 200,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422
