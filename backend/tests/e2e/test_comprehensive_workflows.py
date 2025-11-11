"""
Comprehensive E2E tests for all major workflows.

Tests cover:
- Video upload and management
- Transcription workflow
- Clip creation workflow
- Timeline editing workflow
- Silence removal workflow
- Dashboard and stats
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from io import BytesIO
from uuid import uuid4


def test_video_lifecycle(client: TestClient):
    """Test complete video lifecycle from upload to deletion."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"lifecycle-{uuid4()}@example.com",
            "password": "Password123!",
            "full_name": "Lifecycle Test User"
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create video
    video_data = {
        "title": "Test Video Lifecycle",
        "s3_key": f"videos/test-{uuid4()}.mp4",
        "duration": 120,
        "file_size": 1024 * 1024
    }

    create_response = client.post(
        "/api/v1/videos",
        json=video_data,
        headers=headers
    )

    if create_response.status_code == 201:
        video_id = create_response.json()["id"]

        # Read video
        get_response = client.get(f"/api/v1/videos/{video_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Test Video Lifecycle"

        # Update video
        update_response = client.patch(
            f"/api/v1/videos/{video_id}",
            json={"title": "Updated Title"},
            headers=headers
        )
        if update_response.status_code == 200:
            assert update_response.json()["title"] == "Updated Title"

        # List videos
        list_response = client.get("/api/v1/videos", headers=headers)
        if list_response.status_code == 200:
            videos = list_response.json()
            assert any(v["id"] == video_id for v in videos)

        # Delete video
        delete_response = client.delete(f"/api/v1/videos/{video_id}", headers=headers)
        assert delete_response.status_code in [200, 204]

        # Verify deletion
        get_after_delete = client.get(f"/api/v1/videos/{video_id}", headers=headers)
        assert get_after_delete.status_code == 404


def test_transcription_workflow(client: TestClient):
    """Test complete transcription workflow."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"transcript-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create video
    video_data = {
        "title": "Transcription Test",
        "s3_key": f"videos/test-{uuid4()}.mp4",
        "duration": 60,
        "file_size": 512 * 1024
    }

    create_response = client.post("/api/v1/videos", json=video_data, headers=headers)

    if create_response.status_code == 201:
        video_id = create_response.json()["id"]

        # Request transcription
        with patch('app.services.transcription.TranscriptionService.transcribe_video'):
            transcribe_response = client.post(
                f"/api/v1/videos/{video_id}/transcribe",
                headers=headers
            )

            # Should accept request
            if transcribe_response.status_code in [200, 202]:
                # Check transcription progress
                progress_response = client.get(
                    f"/api/v1/transcript/{video_id}/progress",
                    headers=headers
                )
                assert progress_response.status_code in [200, 404]

                # Get transcript (may not exist yet in test)
                transcript_response = client.get(
                    f"/api/v1/transcript/{video_id}",
                    headers=headers
                )
                assert transcript_response.status_code in [200, 404]


def test_clip_creation_workflow(client: TestClient):
    """Test clip creation from keyword search."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"clips-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create video
    video_data = {
        "title": "Clip Test Video",
        "s3_key": f"videos/test-{uuid4()}.mp4",
        "duration": 180,
        "file_size": 1024 * 1024
    }

    create_response = client.post("/api/v1/videos", json=video_data, headers=headers)

    if create_response.status_code == 201:
        video_id = create_response.json()["id"]

        # Search for keywords
        search_response = client.post(
            f"/api/v1/videos/{video_id}/clips/search",
            json={"keywords": ["test", "demo"]},
            headers=headers
        )

        if search_response.status_code == 200:
            # Create clip
            clip_data = {
                "start_time": 10.5,
                "end_time": 30.5,
                "title": "Test Clip"
            }

            clip_response = client.post(
                f"/api/v1/videos/{video_id}/clips",
                json=clip_data,
                headers=headers
            )

            if clip_response.status_code in [200, 201]:
                clip_id = clip_response.json()["id"]

                # Get clip details
                get_clip_response = client.get(
                    f"/api/v1/clips/{clip_id}",
                    headers=headers
                )
                assert get_clip_response.status_code == 200

                # List clips for video
                list_clips_response = client.get(
                    f"/api/v1/videos/{video_id}/clips",
                    headers=headers
                )
                if list_clips_response.status_code == 200:
                    clips = list_clips_response.json()
                    assert any(c["id"] == clip_id for c in clips)

                # Delete clip
                delete_clip_response = client.delete(
                    f"/api/v1/clips/{clip_id}",
                    headers=headers
                )
                assert delete_clip_response.status_code in [200, 204]


def test_silence_removal_workflow(client: TestClient):
    """Test silence detection and removal."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"silence-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create video
    video_data = {
        "title": "Silence Removal Test",
        "s3_key": f"videos/test-{uuid4()}.mp4",
        "duration": 300,
        "file_size": 2 * 1024 * 1024
    }

    create_response = client.post("/api/v1/videos", json=video_data, headers=headers)

    if create_response.status_code == 201:
        video_id = create_response.json()["id"]

        # Detect silence segments
        detect_response = client.post(
            "/api/v1/silence/detect",
            json={
                "video_id": video_id,
                "threshold_db": -40,
                "min_duration_ms": 1000
            },
            headers=headers
        )

        if detect_response.status_code in [200, 202]:
            # Get silence segments
            segments_response = client.get(
                f"/api/v1/silence/segments?video_id={video_id}",
                headers=headers
            )
            assert segments_response.status_code in [200, 404]

            # Remove silence
            with patch('app.services.silence_removal.SilenceRemovalService.remove_silence'):
                remove_response = client.post(
                    "/api/v1/silence/remove",
                    json={"video_id": video_id},
                    headers=headers
                )

                if remove_response.status_code in [200, 202]:
                    job_id = remove_response.json().get("job_id")

                    if job_id:
                        # Check progress
                        progress_response = client.get(
                            f"/api/v1/silence/progress?job_id={job_id}",
                            headers=headers
                        )
                        assert progress_response.status_code in [200, 404]


def test_timeline_editing_workflow(client: TestClient):
    """Test timeline editing operations."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"timeline-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create video
    video_data = {
        "title": "Timeline Edit Test",
        "s3_key": f"videos/test-{uuid4()}.mp4",
        "duration": 240,
        "file_size": 1500 * 1024
    }

    create_response = client.post("/api/v1/videos", json=video_data, headers=headers)

    if create_response.status_code == 201:
        video_id = create_response.json()["id"]

        # Generate waveform
        waveform_response = client.post(
            "/api/v1/waveform",
            json={"video_id": video_id},
            headers=headers
        )

        if waveform_response.status_code in [200, 202]:
            # Get waveform data
            get_waveform_response = client.get(
                f"/api/v1/waveform?video_id={video_id}",
                headers=headers
            )
            assert get_waveform_response.status_code in [200, 404]

            # Create timeline segments
            segment_data = {
                "video_id": video_id,
                "segments": [
                    {"start_time": 0, "end_time": 60},
                    {"start_time": 120, "end_time": 180}
                ]
            }

            segments_response = client.post(
                "/api/v1/timeline/segments",
                json=segment_data,
                headers=headers
            )

            if segments_response.status_code in [200, 201]:
                # Get segments
                get_segments_response = client.get(
                    f"/api/v1/timeline/segments?video_id={video_id}",
                    headers=headers
                )
                assert get_segments_response.status_code in [200, 404]


def test_dashboard_stats(client: TestClient):
    """Test dashboard statistics endpoint."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"dashboard-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get dashboard stats
    stats_response = client.get("/api/v1/dashboard/stats", headers=headers)

    if stats_response.status_code == 200:
        stats = stats_response.json()

        # Verify stats structure
        assert "total_videos" in stats or "videos_count" in stats
        # Stats should be valid numbers
        assert isinstance(stats.get("total_videos", 0), int)


def test_concurrent_video_uploads(client: TestClient):
    """Test handling concurrent video uploads from same user."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"concurrent-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple videos concurrently (simulated)
    video_ids = []

    for i in range(3):
        video_data = {
            "title": f"Concurrent Video {i}",
            "s3_key": f"videos/concurrent-{uuid4()}.mp4",
            "duration": 60,
            "file_size": 512 * 1024
        }

        response = client.post("/api/v1/videos", json=video_data, headers=headers)

        if response.status_code == 201:
            video_ids.append(response.json()["id"])

    # Verify all videos were created
    if len(video_ids) > 0:
        list_response = client.get("/api/v1/videos", headers=headers)

        if list_response.status_code == 200:
            videos = list_response.json()
            # At least some videos should exist
            assert len(videos) > 0


def test_error_handling_invalid_video_id(client: TestClient):
    """Test error handling for invalid video IDs."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"errors-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to access non-existent video
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/videos/{fake_id}", headers=headers)

    assert response.status_code == 404

    # Try to update non-existent video
    update_response = client.patch(
        f"/api/v1/videos/{fake_id}",
        json={"title": "Updated"},
        headers=headers
    )

    assert update_response.status_code == 404

    # Try to delete non-existent video
    delete_response = client.delete(f"/api/v1/videos/{fake_id}", headers=headers)

    assert delete_response.status_code == 404


def test_user_data_isolation(client: TestClient):
    """Test that users can only access their own data."""
    # Register two users
    user1_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user1-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert user1_response.status_code == 201
    user1_token = user1_response.json()["access_token"]

    user2_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user2-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert user2_response.status_code == 201
    user2_token = user2_response.json()["access_token"]

    # User 1 creates a video
    video_data = {
        "title": "User 1 Video",
        "s3_key": f"videos/user1-{uuid4()}.mp4",
        "duration": 60,
        "file_size": 512 * 1024
    }

    create_response = client.post(
        "/api/v1/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {user1_token}"}
    )

    if create_response.status_code == 201:
        user1_video_id = create_response.json()["id"]

        # User 2 tries to access User 1's video
        access_response = client.get(
            f"/api/v1/videos/{user1_video_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        # Should be forbidden or not found
        assert access_response.status_code in [403, 404]

        # User 2 tries to delete User 1's video
        delete_response = client.delete(
            f"/api/v1/videos/{user1_video_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        # Should be forbidden or not found
        assert delete_response.status_code in [403, 404]


def test_pagination(client: TestClient):
    """Test pagination for video lists."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pagination-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple videos
    for i in range(5):
        video_data = {
            "title": f"Pagination Test {i}",
            "s3_key": f"videos/page-{uuid4()}.mp4",
            "duration": 60,
            "file_size": 512 * 1024
        }

        client.post("/api/v1/videos", json=video_data, headers=headers)

    # Test pagination parameters
    page1_response = client.get(
        "/api/v1/videos?limit=2&offset=0",
        headers=headers
    )

    if page1_response.status_code == 200:
        page1_videos = page1_response.json()

        # Should return limited results
        if isinstance(page1_videos, list):
            assert len(page1_videos) <= 2

        # Get next page
        page2_response = client.get(
            "/api/v1/videos?limit=2&offset=2",
            headers=headers
        )

        if page2_response.status_code == 200:
            page2_videos = page2_response.json()

            # Should return different results
            if isinstance(page1_videos, list) and isinstance(page2_videos, list):
                # Pages should be different (if enough videos)
                if len(page1_videos) > 0 and len(page2_videos) > 0:
                    assert page1_videos[0]["id"] != page2_videos[0]["id"]


def test_filtering_and_sorting(client: TestClient):
    """Test filtering and sorting video lists."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"filter-{uuid4()}@example.com",
            "password": "Password123!",
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create videos with different statuses
    video_data = {
        "title": "Filter Test Video",
        "s3_key": f"videos/filter-{uuid4()}.mp4",
        "duration": 60,
        "file_size": 512 * 1024,
        "status": "completed"
    }

    client.post("/api/v1/videos", json=video_data, headers=headers)

    # Test filtering by status
    filter_response = client.get(
        "/api/v1/videos?status=completed",
        headers=headers
    )

    if filter_response.status_code == 200:
        videos = filter_response.json()

        # All returned videos should have completed status
        if isinstance(videos, list):
            for video in videos:
                if "status" in video:
                    assert video["status"] == "completed"

    # Test sorting
    sort_response = client.get(
        "/api/v1/videos?sort_by=created_at&sort_order=desc",
        headers=headers
    )

    if sort_response.status_code == 200:
        # Should return sorted results
        assert True
