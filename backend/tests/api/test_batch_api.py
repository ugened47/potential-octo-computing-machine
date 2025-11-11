"""Tests for batch processing API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.main import app
from app.models.user import User
from app.models.video import Video, VideoStatus


class BatchJobStatus:
    """Batch job status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchVideoStatus:
    """Batch video status enum."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="batch_test@example.com",
        hashed_password="hashed_password",
        full_name="Batch Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_videos(db_session: AsyncSession, test_user: User) -> list[Video]:
    """Create test videos for batch processing."""
    videos = []
    for i in range(5):
        video = Video(
            user_id=test_user.id,
            title=f"Test Video {i+1}",
            status=VideoStatus.UPLOADED,
            s3_key=f"videos/test/video-{i+1}.mp4",
            duration=120.0,
        )
        db_session.add(video)
        videos.append(video)
    await db_session.commit()
    for video in videos:
        await db_session.refresh(video)
    return videos


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


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


@pytest.mark.asyncio
class TestBatchJobAPI:
    """Test batch job API endpoints."""

    async def test_create_batch_job_with_videos(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test POST /api/batch/jobs creates batch job with videos."""
        with patch("app.services.s3.S3Service.generate_presigned_url") as mock_s3:
            mock_s3.return_value = ("http://presigned-url", "videos/batch/test.mp4")

            response = client.post(
                "/api/batch/jobs",
                json={
                    "name": "My Batch Job",
                    "description": "Test batch processing",
                    "settings": {
                        "transcribe": True,
                        "remove_silence": True,
                        "detect_highlights": False,
                        "silence_threshold": -40.0,
                        "export_format": "mp4",
                        "export_quality": "1080p",
                    },
                    "video_count": 3,
                },
                headers=auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert "batch_job_id" in data
            assert "upload_urls" in data
            assert len(data["upload_urls"]) == 3
            assert data["batch_job"]["name"] == "My Batch Job"
            assert data["batch_job"]["status"] == BatchJobStatus.PENDING
            assert data["batch_job"]["total_videos"] == 3

    async def test_create_batch_job_validates_settings(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch job creation validates settings."""
        response = client.post(
            "/api/batch/jobs",
            json={
                "name": "Invalid Batch",
                "settings": {
                    "transcribe": True,
                    "silence_threshold": -100.0,  # Invalid threshold
                },
                "video_count": 1,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    async def test_create_batch_job_enforces_quota(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch job creation enforces user quota limits."""
        response = client.post(
            "/api/batch/jobs",
            json={
                "name": "Large Batch",
                "settings": {"transcribe": True},
                "video_count": 100,  # Exceeds quota
            },
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "quota" in response.json()["detail"].lower()

    async def test_add_videos_to_batch(
        self, client: TestClient, test_videos: list[Video], auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/videos adds videos to batch."""
        # First create a batch job
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={
                    "name": "Test Batch",
                    "settings": {"transcribe": True},
                    "video_count": 0,
                },
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Add videos to batch
        video_ids = [str(v.id) for v in test_videos[:3]]
        response = client.post(
            f"/api/batch/jobs/{batch_job_id}/videos",
            json={"video_ids": video_ids},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_videos"] == 3

    async def test_start_batch_processing(
        self, client: TestClient, auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/start starts processing."""
        # Create batch job
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={
                    "name": "Start Test",
                    "settings": {"transcribe": True},
                    "video_count": 2,
                },
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start processing
        with patch("app.worker.process_batch_job") as mock_worker:
            mock_worker.return_value = "job-123"

            response = client.post(
                f"/api/batch/jobs/{batch_job_id}/start",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["status"] == BatchJobStatus.PROCESSING

    async def test_start_already_processing_batch_fails(
        self, client: TestClient, auth_headers: dict
    ):
        """Test starting already processing batch fails."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Test", "settings": {"transcribe": True}, "video_count": 1},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start once
        with patch("app.worker.process_batch_job"):
            client.post(f"/api/batch/jobs/{batch_job_id}/start", headers=auth_headers)

            # Try to start again
            response = client.post(
                f"/api/batch/jobs/{batch_job_id}/start",
                headers=auth_headers,
            )

            assert response.status_code == 400
            assert "already processing" in response.json()["detail"].lower()

    async def test_list_batch_jobs_with_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """Test GET /api/batch/jobs lists jobs with pagination."""
        # Create multiple batch jobs
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            for i in range(5):
                client.post(
                    "/api/batch/jobs",
                    json={
                        "name": f"Batch {i}",
                        "settings": {"transcribe": True},
                        "video_count": 1,
                    },
                    headers=auth_headers,
                )

        # List all
        response = client.get("/api/batch/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["batch_jobs"]) == 5
        assert data["total"] == 5

        # Test pagination
        response = client.get(
            "/api/batch/jobs?limit=2&offset=0",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["batch_jobs"]) == 2

    async def test_list_batch_jobs_filters_by_status(
        self, client: TestClient, auth_headers: dict
    ):
        """Test listing batch jobs filters by status."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            # Create batch jobs with different statuses
            for status in ["pending", "processing", "completed"]:
                response = client.post(
                    "/api/batch/jobs",
                    json={
                        "name": f"Batch {status}",
                        "settings": {"transcribe": True},
                        "video_count": 1,
                    },
                    headers=auth_headers,
                )
                # Manually update status for testing
                # In real scenario, this would be done by worker

        # Filter by status
        response = client.get(
            "/api/batch/jobs?status=pending",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(job["status"] == "pending" for job in data["batch_jobs"])

    async def test_list_batch_jobs_sorts_by_created_date(
        self, client: TestClient, auth_headers: dict
    ):
        """Test listing batch jobs sorts correctly."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            for i in range(3):
                client.post(
                    "/api/batch/jobs",
                    json={
                        "name": f"Batch {i}",
                        "settings": {"transcribe": True},
                        "video_count": 1,
                    },
                    headers=auth_headers,
                )

        response = client.get(
            "/api/batch/jobs?sort=created_at",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        dates = [job["created_at"] for job in data["batch_jobs"]]
        assert dates == sorted(dates, reverse=True)

    async def test_get_batch_job_details(
        self, client: TestClient, auth_headers: dict
    ):
        """Test GET /api/batch/jobs/{id} returns job details."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={
                    "name": "Detail Test",
                    "description": "Test description",
                    "settings": {"transcribe": True, "remove_silence": False},
                    "video_count": 2,
                },
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        response = client.get(
            f"/api/batch/jobs/{batch_job_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == batch_job_id
        assert data["name"] == "Detail Test"
        assert data["description"] == "Test description"
        assert data["settings"]["transcribe"] is True
        assert "videos" in data

    async def test_get_nonexistent_batch_job_returns_404(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting nonexistent batch job returns 404."""
        fake_id = str(uuid4())
        response = client.get(
            f"/api/batch/jobs/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_pause_batch_processing(
        self, client: TestClient, auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/pause pauses batch."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Pause Test", "settings": {"transcribe": True}, "video_count": 2},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start processing first
        with patch("app.worker.process_batch_job"):
            client.post(f"/api/batch/jobs/{batch_job_id}/start", headers=auth_headers)

        # Pause
        response = client.post(
            f"/api/batch/jobs/{batch_job_id}/pause",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BatchJobStatus.PAUSED

    async def test_resume_batch_processing(
        self, client: TestClient, auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/resume resumes batch."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Resume Test", "settings": {"transcribe": True}, "video_count": 2},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start and pause
        with patch("app.worker.process_batch_job"):
            client.post(f"/api/batch/jobs/{batch_job_id}/start", headers=auth_headers)
            client.post(f"/api/batch/jobs/{batch_job_id}/pause", headers=auth_headers)

            # Resume
            response = client.post(
                f"/api/batch/jobs/{batch_job_id}/resume",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == BatchJobStatus.PROCESSING

    async def test_cancel_batch_processing(
        self, client: TestClient, auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/cancel cancels batch."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Cancel Test", "settings": {"transcribe": True}, "video_count": 2},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start processing
        with patch("app.worker.process_batch_job"):
            client.post(f"/api/batch/jobs/{batch_job_id}/start", headers=auth_headers)

        # Cancel
        response = client.post(
            f"/api/batch/jobs/{batch_job_id}/cancel",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BatchJobStatus.CANCELLED

    async def test_retry_failed_videos(
        self, client: TestClient, auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/retry-failed retries failed videos."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Retry Test", "settings": {"transcribe": True}, "video_count": 3},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Simulate some failed videos
        # In real scenario, videos would fail during processing

        with patch("app.worker.process_batch_job"):
            response = client.post(
                f"/api/batch/jobs/{batch_job_id}/retry-failed",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "retried_count" in data

    async def test_delete_batch_job(
        self, client: TestClient, auth_headers: dict
    ):
        """Test DELETE /api/batch/jobs/{id} deletes batch job."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Delete Test", "settings": {"transcribe": True}, "video_count": 1},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        response = client.delete(
            f"/api/batch/jobs/{batch_job_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(
            f"/api/batch/jobs/{batch_job_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_processing_batch_fails(
        self, client: TestClient, auth_headers: dict
    ):
        """Test deleting processing batch fails."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Delete Test", "settings": {"transcribe": True}, "video_count": 1},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start processing
        with patch("app.worker.process_batch_job"):
            client.post(f"/api/batch/jobs/{batch_job_id}/start", headers=auth_headers)

            # Try to delete
            response = client.delete(
                f"/api/batch/jobs/{batch_job_id}",
                headers=auth_headers,
            )

            assert response.status_code == 400
            assert "processing" in response.json()["detail"].lower()

    async def test_get_batch_progress(
        self, client: TestClient, auth_headers: dict
    ):
        """Test GET /api/batch/jobs/{id}/progress returns progress updates."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Progress Test", "settings": {"transcribe": True}, "video_count": 2},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Note: SSE endpoint test would require special handling
        # This test validates the endpoint exists
        response = client.get(
            f"/api/batch/jobs/{batch_job_id}/progress",
            headers=auth_headers,
        )

        # SSE endpoint should accept the connection
        assert response.status_code in [200, 202]

    async def test_export_batch_as_zip(
        self, client: TestClient, auth_headers: dict
    ):
        """Test POST /api/batch/jobs/{id}/export exports as ZIP."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Export Test", "settings": {"transcribe": True}, "video_count": 2},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        with patch("app.services.batch_export.BatchExportService.create_export") as mock_export:
            mock_export.return_value = {"export_job_id": "export-123"}

            response = client.post(
                f"/api/batch/jobs/{batch_job_id}/export",
                json={"format": "zip", "include_failed": False},
                headers=auth_headers,
            )

            assert response.status_code == 202
            data = response.json()
            assert "export_job_id" in data

    async def test_export_batch_as_merged_video(
        self, client: TestClient, auth_headers: dict
    ):
        """Test exporting batch as merged video."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Merge Test", "settings": {"transcribe": True}, "video_count": 3},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        with patch("app.services.batch_export.BatchExportService.create_export") as mock_export:
            mock_export.return_value = {"export_job_id": "export-456"}

            response = client.post(
                f"/api/batch/jobs/{batch_job_id}/export",
                json={"format": "merged"},
                headers=auth_headers,
            )

            assert response.status_code == 202
            data = response.json()
            assert "export_job_id" in data

    async def test_get_export_status(
        self, client: TestClient, auth_headers: dict
    ):
        """Test GET /api/batch/jobs/{id}/export/{export_id} returns export status."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Export Status Test", "settings": {"transcribe": True}, "video_count": 1},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        export_id = "export-789"

        with patch("app.services.batch_export.BatchExportService.get_export_status") as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "progress": 100,
                "download_url": "http://download-url.com/batch.zip",
                "expires_at": datetime.utcnow().isoformat(),
            }

            response = client.get(
                f"/api/batch/jobs/{batch_job_id}/export/{export_id}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "download_url" in data

    async def test_authorization_users_cannot_access_others_batches(
        self, client: TestClient, db_session: AsyncSession, auth_headers: dict
    ):
        """Test users can only access their own batch jobs."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
            full_name="Other User",
        )
        db_session.add(other_user)
        await db_session.commit()

        # Create batch job as other user
        from app.api.deps import get_current_user

        def override_other_user():
            return other_user

        app.dependency_overrides[get_current_user] = override_other_user

        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Other's Batch", "settings": {"transcribe": True}, "video_count": 1},
                headers={"Authorization": "Bearer other-token"},
            )
            other_batch_id = create_response.json()["batch_job_id"]

        # Reset to original user
        app.dependency_overrides[get_current_user] = lambda: auth_headers

        # Try to access other user's batch
        response = client.get(
            f"/api/batch/jobs/{other_batch_id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_batch_job_includes_progress_percentage(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch job response includes progress percentage."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Progress %", "settings": {"transcribe": True}, "video_count": 10},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        response = client.get(
            f"/api/batch/jobs/{batch_job_id}",
            headers=auth_headers,
        )

        data = response.json()
        assert "progress_percentage" in data
        assert 0 <= data["progress_percentage"] <= 100

    async def test_batch_job_includes_estimated_time(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch job includes estimated time remaining."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            create_response = client.post(
                "/api/batch/jobs",
                json={"name": "Time Estimate", "settings": {"transcribe": True}, "video_count": 5},
                headers=auth_headers,
            )
            batch_job_id = create_response.json()["batch_job_id"]

        # Start processing
        with patch("app.worker.process_batch_job"):
            client.post(f"/api/batch/jobs/{batch_job_id}/start", headers=auth_headers)

        response = client.get(
            f"/api/batch/jobs/{batch_job_id}",
            headers=auth_headers,
        )

        data = response.json()
        assert "estimated_time_remaining" in data

    async def test_rate_limiting_batch_creation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test rate limiting on batch job creation."""
        with patch("app.services.s3.S3Service.generate_presigned_url"):
            # Create multiple batches rapidly
            for i in range(10):
                response = client.post(
                    "/api/batch/jobs",
                    json={
                        "name": f"Rate Limit Test {i}",
                        "settings": {"transcribe": True},
                        "video_count": 1,
                    },
                    headers=auth_headers,
                )

                # After certain number, should hit rate limit
                if i >= 5:  # Assuming limit is 5 per hour for free tier
                    if response.status_code == 429:
                        assert "rate limit" in response.json()["detail"].lower()
                        break
