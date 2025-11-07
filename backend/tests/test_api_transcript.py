"""Tests for transcript API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.main import app
from app.models.transcript import Transcript, TranscriptStatus
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
async def test_video(db_session: AsyncSession, test_user: User) -> Video:
    """Create a test video."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="test-video.mp4",
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
        full_text="This is a test transcript.",
        word_timestamps={
            "words": [
                {"word": "This", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "is", "start": 0.5, "end": 0.8, "confidence": 0.92},
                {"word": "a", "start": 0.8, "end": 1.0, "confidence": 0.90},
                {"word": "test", "start": 1.0, "end": 1.5, "confidence": 0.88},
                {"word": "transcript.", "start": 1.5, "end": 2.2, "confidence": 0.85},
            ]
        },
        language="en",
        status=TranscriptStatus.COMPLETED,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)
    return transcript


@pytest.mark.asyncio
async def test_get_transcript_success(
    client: TestClient, test_user: User, test_video: Video, test_transcript: Transcript
):
    """Test getting transcript successfully."""
    # Create access token
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_transcript.id)
    assert data["video_id"] == str(test_video.id)
    assert data["full_text"] == "This is a test transcript."
    assert data["language"] == "en"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_get_transcript_not_found(
    client: TestClient, test_user: User, test_video: Video
):
    """Test getting transcript when it doesn't exist."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript", headers=headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_transcript_unauthorized(
    client: TestClient, test_video: Video, test_transcript: Transcript
):
    """Test getting transcript without authentication."""
    response = client.get(f"/api/videos/{test_video.id}/transcript")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_transcript_wrong_user(
    client: TestClient, db_session: AsyncSession, test_video: Video, test_transcript: Transcript
):
    """Test getting transcript for video owned by different user."""
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(other_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript", headers=headers
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_transcription_success(
    client: TestClient, test_user: User, test_video: Video
):
    """Test triggering transcription successfully."""
    from app.core.security import create_access_token
    from unittest.mock import patch, AsyncMock

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Test that the endpoint accepts the request and returns 202
    # The actual enqueueing may fail in test environment, but endpoint should still return 202
    response = client.post(
        f"/api/videos/{test_video.id}/transcript/transcribe", headers=headers
    )

    # Endpoint should return 202 (accepted) even if enqueue fails
    assert response.status_code == 202
    data = response.json()
    assert "message" in data
    assert str(test_video.id) in data["video_id"]


@pytest.mark.asyncio
async def test_trigger_transcription_already_processing(
    client: TestClient,
    test_user: User,
    test_video: Video,
    db_session: AsyncSession,
):
    """Test triggering transcription when already processing."""
    # Create transcript with PROCESSING status
    transcript = Transcript(
        video_id=test_video.id,
        full_text="",
        word_timestamps={},
        status=TranscriptStatus.PROCESSING,
    )
    db_session.add(transcript)
    await db_session.commit()

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        f"/api/videos/{test_video.id}/transcript/transcribe", headers=headers
    )

    assert response.status_code == 409
    assert "already in progress" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_export_transcript_srt(
    client: TestClient, test_user: User, test_video: Video, test_transcript: Transcript
):
    """Test exporting transcript as SRT."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript/export?format=srt", headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/srt")
    assert "transcript_" in response.headers["content-disposition"]
    assert ".srt" in response.headers["content-disposition"]
    assert "1" in response.text  # SRT file should have sequence numbers


@pytest.mark.asyncio
async def test_export_transcript_vtt(
    client: TestClient, test_user: User, test_video: Video, test_transcript: Transcript
):
    """Test exporting transcript as VTT."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript/export?format=vtt", headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/vtt")
    assert "transcript_" in response.headers["content-disposition"]
    assert ".vtt" in response.headers["content-disposition"]
    assert "WEBVTT" in response.text


@pytest.mark.asyncio
async def test_export_transcript_invalid_format(
    client: TestClient, test_user: User, test_video: Video, test_transcript: Transcript
):
    """Test exporting transcript with invalid format."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript/export?format=invalid", headers=headers
    )

    assert response.status_code == 400
    assert "invalid format" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_transcription_progress_not_started(
    client: TestClient, test_user: User, test_video: Video
):
    """Test getting transcription progress when not started."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript/progress", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == str(test_video.id)
    assert data["progress"] == 0
    assert data["status"] == "Not started"


@pytest.mark.asyncio
async def test_get_transcription_progress_completed(
    client: TestClient, test_user: User, test_video: Video, test_transcript: Transcript
):
    """Test getting transcription progress when completed."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/transcript/progress", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == str(test_video.id)
    assert data["progress"] == 100
    assert data["status"] == "Completed"

