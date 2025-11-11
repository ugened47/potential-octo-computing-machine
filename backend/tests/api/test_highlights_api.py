"""Tests for highlight detection API endpoints."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.video import Video, VideoStatus


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
        s3_key="videos/test/test-video.mp4",
        duration=120.0,
        resolution="1920x1080",
        format="h264",
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


# POST /api/videos/{id}/highlights/detect Tests


@pytest.mark.asyncio
async def test_trigger_highlight_detection_with_medium_sensitivity(
    client: TestClient, test_video: Video, auth_headers: dict
):
    """Test POST /api/videos/{id}/highlights/detect with medium sensitivity."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.enqueue_job = AsyncMock(return_value="job_123")

        response = client.post(
            f"/api/videos/{test_video.id}/highlights/detect",
            json={"sensitivity": "medium"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "message" in data


@pytest.mark.asyncio
async def test_trigger_highlight_detection_with_high_sensitivity(
    client: TestClient, test_video: Video, auth_headers: dict
):
    """Test POST /api/videos/{id}/highlights/detect with high sensitivity."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.enqueue_job = AsyncMock(return_value="job_456")

        response = client.post(
            f"/api/videos/{test_video.id}/highlights/detect",
            json={"sensitivity": "high"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


@pytest.mark.asyncio
async def test_trigger_highlight_detection_with_custom_keywords(
    client: TestClient, test_video: Video, auth_headers: dict
):
    """Test POST /api/videos/{id}/highlights/detect with custom keywords."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.enqueue_job = AsyncMock(return_value="job_789")

        response = client.post(
            f"/api/videos/{test_video.id}/highlights/detect",
            json={
                "sensitivity": "medium",
                "keywords": ["amazing", "incredible", "best"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


@pytest.mark.asyncio
async def test_trigger_highlight_detection_prevents_duplicate(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test POST /api/videos/{id}/highlights/detect prevents duplicate detection."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.get = AsyncMock(
            return_value=b'{"progress": 50, "status": "processing"}'
        )

        response = client.post(
            f"/api/videos/{test_video.id}/highlights/detect",
            json={"sensitivity": "medium"},
            headers=auth_headers,
        )

        assert response.status_code == 409  # Conflict
        data = response.json()
        assert "already processing" in data["detail"].lower() or "in progress" in data["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_highlight_detection_video_not_found(
    client: TestClient, auth_headers: dict
):
    """Test POST /api/videos/{id}/highlights/detect with non-existent video."""
    fake_video_id = uuid4()
    response = client.post(
        f"/api/videos/{fake_video_id}/highlights/detect",
        json={"sensitivity": "medium"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_highlight_detection_unauthorized(
    client: TestClient, test_video: Video, other_user: User
):
    """Test POST /api/videos/{id}/highlights/detect with wrong user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return other_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.post(
        f"/api/videos/{test_video.id}/highlights/detect",
        json={"sensitivity": "medium"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_trigger_highlight_detection_invalid_sensitivity(
    client: TestClient, test_video: Video, auth_headers: dict
):
    """Test POST /api/videos/{id}/highlights/detect with invalid sensitivity."""
    response = client.post(
        f"/api/videos/{test_video.id}/highlights/detect",
        json={"sensitivity": "invalid"},
        headers=auth_headers,
    )

    assert response.status_code == 422  # Validation error


# GET /api/videos/{id}/highlights Tests


@pytest.mark.asyncio
async def test_get_video_highlights_returns_all_highlights(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/videos/{id}/highlights returns all highlights sorted by rank."""
    # Create test highlights
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlights = [
        Highlight(
            video_id=test_video.id,
            start_time=10.0,
            end_time=20.0,
            overall_score=85,
            audio_energy_score=80,
            scene_change_score=70,
            speech_density_score=90,
            keyword_score=85,
            rank=1,
            highlight_type=HighlightType.HIGH_ENERGY,
            status=HighlightStatus.DETECTED,
            duration_seconds=10.0,
        ),
        Highlight(
            video_id=test_video.id,
            start_time=50.0,
            end_time=65.0,
            overall_score=75,
            audio_energy_score=70,
            scene_change_score=80,
            speech_density_score=75,
            keyword_score=70,
            rank=2,
            highlight_type=HighlightType.SCENE_CHANGE,
            status=HighlightStatus.DETECTED,
            duration_seconds=15.0,
        ),
    ]

    for highlight in highlights:
        db_session.add(highlight)
    await db_session.commit()

    response = client.get(
        f"/api/videos/{test_video.id}/highlights", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "highlights" in data
    assert "total" in data
    assert len(data["highlights"]) == 2
    assert data["total"] == 2
    # Check sorted by rank
    assert data["highlights"][0]["rank"] == 1
    assert data["highlights"][1]["rank"] == 2


@pytest.mark.asyncio
async def test_get_video_highlights_filters_by_status(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/videos/{id}/highlights filters by status."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlights = [
        Highlight(
            video_id=test_video.id,
            start_time=10.0,
            end_time=20.0,
            overall_score=85,
            audio_energy_score=80,
            scene_change_score=70,
            speech_density_score=90,
            keyword_score=85,
            rank=1,
            highlight_type=HighlightType.HIGH_ENERGY,
            status=HighlightStatus.DETECTED,
            duration_seconds=10.0,
        ),
        Highlight(
            video_id=test_video.id,
            start_time=50.0,
            end_time=65.0,
            overall_score=75,
            audio_energy_score=70,
            scene_change_score=80,
            speech_density_score=75,
            keyword_score=70,
            rank=2,
            highlight_type=HighlightType.SCENE_CHANGE,
            status=HighlightStatus.REVIEWED,
            duration_seconds=15.0,
        ),
    ]

    for highlight in highlights:
        db_session.add(highlight)
    await db_session.commit()

    response = client.get(
        f"/api/videos/{test_video.id}/highlights?status=detected",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["highlights"]) == 1
    assert data["highlights"][0]["status"] == "detected"


@pytest.mark.asyncio
async def test_get_video_highlights_filters_by_min_score(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/videos/{id}/highlights filters by minimum score."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlights = [
        Highlight(
            video_id=test_video.id,
            start_time=10.0,
            end_time=20.0,
            overall_score=85,
            audio_energy_score=80,
            scene_change_score=70,
            speech_density_score=90,
            keyword_score=85,
            rank=1,
            highlight_type=HighlightType.HIGH_ENERGY,
            status=HighlightStatus.DETECTED,
            duration_seconds=10.0,
        ),
        Highlight(
            video_id=test_video.id,
            start_time=50.0,
            end_time=65.0,
            overall_score=65,
            audio_energy_score=60,
            scene_change_score=70,
            speech_density_score=65,
            keyword_score=60,
            rank=2,
            highlight_type=HighlightType.SCENE_CHANGE,
            status=HighlightStatus.DETECTED,
            duration_seconds=15.0,
        ),
    ]

    for highlight in highlights:
        db_session.add(highlight)
    await db_session.commit()

    response = client.get(
        f"/api/videos/{test_video.id}/highlights?min_score=80",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["highlights"]) == 1
    assert data["highlights"][0]["overall_score"] >= 80


@pytest.mark.asyncio
async def test_get_video_highlights_pagination(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/videos/{id}/highlights pagination with limit and offset."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    # Create 15 highlights
    highlights = []
    for i in range(15):
        highlights.append(
            Highlight(
                video_id=test_video.id,
                start_time=float(i * 10),
                end_time=float(i * 10 + 10),
                overall_score=80 - i,
                audio_energy_score=75,
                scene_change_score=70,
                speech_density_score=75,
                keyword_score=70,
                rank=i + 1,
                highlight_type=HighlightType.HIGH_ENERGY,
                status=HighlightStatus.DETECTED,
                duration_seconds=10.0,
            )
        )

    for highlight in highlights:
        db_session.add(highlight)
    await db_session.commit()

    response = client.get(
        f"/api/videos/{test_video.id}/highlights?limit=5&offset=5",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["highlights"]) == 5
    assert data["total"] == 15
    assert data["highlights"][0]["rank"] == 6  # Offset = 5, so rank starts at 6


# GET /api/highlights/{id} Tests


@pytest.mark.asyncio
async def test_get_single_highlight_returns_full_details(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/highlights/{id} returns single highlight with full details."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        detected_keywords=["amazing", "incredible"],
        confidence_level=0.92,
        rank=1,
        highlight_type=HighlightType.KEYWORD_MATCH,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
        context_before_seconds=2.0,
        context_after_seconds=3.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    response = client.get(f"/api/highlights/{highlight.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(highlight.id)
    assert data["overall_score"] == 85
    assert data["audio_energy_score"] == 80
    assert data["scene_change_score"] == 70
    assert data["speech_density_score"] == 90
    assert data["keyword_score"] == 85
    assert data["detected_keywords"] == ["amazing", "incredible"]
    assert data["confidence_level"] == 0.92
    assert data["highlight_type"] == "keyword_match"


@pytest.mark.asyncio
async def test_get_single_highlight_not_found(client: TestClient, auth_headers: dict):
    """Test GET /api/highlights/{id} with non-existent highlight."""
    fake_highlight_id = uuid4()
    response = client.get(f"/api/highlights/{fake_highlight_id}", headers=auth_headers)

    assert response.status_code == 404


# PATCH /api/highlights/{id} Tests


@pytest.mark.asyncio
async def test_update_highlight_status(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test PATCH /api/highlights/{id} updates highlight status."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    response = client.patch(
        f"/api/highlights/{highlight.id}",
        json={"status": "reviewed"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reviewed"


@pytest.mark.asyncio
async def test_update_highlight_rank(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test PATCH /api/highlights/{id} updates highlight rank."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    response = client.patch(
        f"/api/highlights/{highlight.id}",
        json={"rank": 3},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rank"] == 3


@pytest.mark.asyncio
async def test_update_highlight_times(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test PATCH /api/highlights/{id} updates start_time and end_time."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    response = client.patch(
        f"/api/highlights/{highlight.id}",
        json={"start_time": 12.0, "end_time": 22.0},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["start_time"] == 12.0
    assert data["end_time"] == 22.0


# DELETE /api/highlights/{id} Tests


@pytest.mark.asyncio
async def test_delete_highlight_soft_delete(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test DELETE /api/highlights/{id} soft deletes (marks as rejected)."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    response = client.delete(f"/api/highlights/{highlight.id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify soft delete (status changed to rejected)
    await db_session.refresh(highlight)
    assert highlight.status == HighlightStatus.REJECTED


@pytest.mark.asyncio
async def test_delete_highlight_hard_delete(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test DELETE /api/highlights/{id}?hard=true hard deletes highlight."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType
    from sqlmodel import select

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)
    highlight_id = highlight.id

    response = client.delete(
        f"/api/highlights/{highlight.id}?hard=true", headers=auth_headers
    )

    assert response.status_code == 204

    # Verify hard delete (record removed from database)
    result = await db_session.execute(
        select(Highlight).where(Highlight.id == highlight_id)
    )
    deleted_highlight = result.scalar_one_or_none()
    assert deleted_highlight is None


# GET /api/highlights/{id}/preview Tests


@pytest.mark.asyncio
async def test_get_highlight_preview_url(
    client: TestClient, test_video: Video, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/highlights/{id}/preview returns preview URL."""
    from app.models.highlight import Highlight, HighlightStatus, HighlightType

    highlight = Highlight(
        video_id=test_video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=85,
        audio_energy_score=80,
        scene_change_score=70,
        speech_density_score=90,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
        status=HighlightStatus.DETECTED,
        duration_seconds=10.0,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    with patch("app.services.s3.S3Service.generate_presigned_url") as mock_s3:
        mock_s3.return_value = (
            "https://test-preview-url.com/highlight.mp4",
            "previews/test-key.mp4",
        )

        response = client.get(
            f"/api/highlights/{highlight.id}/preview", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "highlight.mp4" in data["url"]


# GET /api/videos/{id}/highlights/progress Tests


@pytest.mark.asyncio
async def test_get_highlight_detection_progress(
    client: TestClient, test_video: Video, auth_headers: dict
):
    """Test GET /api/videos/{id}/highlights/progress returns detection progress."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.get = AsyncMock(
            return_value=b'{"progress": 45, "status": "analyzing_audio", "estimated_time_remaining": 120, "current_stage": "Analyzing audio energy..."}'
        )

        response = client.get(
            f"/api/videos/{test_video.id}/highlights/progress", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 45
        assert data["status"] == "analyzing_audio"
        assert data["estimated_time_remaining"] == 120
        assert "current_stage" in data


@pytest.mark.asyncio
async def test_get_highlight_detection_progress_not_started(
    client: TestClient, test_video: Video, auth_headers: dict
):
    """Test GET /api/videos/{id}/highlights/progress when detection not started."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.get = AsyncMock(return_value=None)

        response = client.get(
            f"/api/videos/{test_video.id}/highlights/progress", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 0
        assert data["status"] == "not_started"
