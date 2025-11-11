"""Tests for highlight detection service (composite scoring and segment merging)."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus


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
def highlight_detection_service():
    """Create HighlightDetectionService instance."""
    from app.services.highlight_detection import HighlightDetectionService

    return HighlightDetectionService()


@pytest.mark.asyncio
async def test_calculate_composite_score_weighted_average(highlight_detection_service):
    """Test calculating overall score as weighted average of component scores."""
    component_scores = {
        "audio_energy_score": 80,
        "scene_change_score": 60,
        "speech_density_score": 90,
        "keyword_score": 70,
    }

    # Default weights: audio 35%, scene 20%, speech 25%, keyword 20%
    overall_score = highlight_detection_service.calculate_composite_score(
        component_scores
    )

    # Calculate expected score: 80*0.35 + 60*0.20 + 90*0.25 + 70*0.20 = 77.5
    expected_score = 28 + 12 + 22.5 + 14
    assert abs(overall_score - expected_score) < 1


@pytest.mark.asyncio
async def test_calculate_composite_score_custom_weights(highlight_detection_service):
    """Test calculating overall score with custom weights."""
    component_scores = {
        "audio_energy_score": 80,
        "scene_change_score": 60,
        "speech_density_score": 90,
        "keyword_score": 70,
    }

    custom_weights = {
        "audio_energy": 0.5,  # 50%
        "scene_change": 0.1,  # 10%
        "speech_density": 0.3,  # 30%
        "keyword": 0.1,  # 10%
    }

    overall_score = highlight_detection_service.calculate_composite_score(
        component_scores, weights=custom_weights
    )

    # Calculate expected: 80*0.5 + 60*0.1 + 90*0.3 + 70*0.1 = 80
    expected_score = 40 + 6 + 27 + 7
    assert abs(overall_score - expected_score) < 1


@pytest.mark.asyncio
async def test_apply_bonus_for_aligned_signals(highlight_detection_service):
    """Test applying +10% bonus when multiple high signals align."""
    # Multiple high scores (audio + scene + keyword all > 70)
    aligned_scores = {
        "audio_energy_score": 85,
        "scene_change_score": 80,
        "speech_density_score": 65,
        "keyword_score": 75,
    }

    base_score = highlight_detection_service.calculate_composite_score(aligned_scores)
    bonus_score = highlight_detection_service.apply_alignment_bonus(
        base_score, aligned_scores
    )

    # Should have +10% bonus
    expected_bonus = base_score * 1.1
    assert abs(bonus_score - expected_bonus) < 1


@pytest.mark.asyncio
async def test_apply_bonus_for_sustained_high_scores(highlight_detection_service):
    """Test applying +15% bonus for sustained high scores (>5 seconds)."""
    segment = {
        "start_time": 10.0,
        "end_time": 17.0,  # 7 seconds duration
        "overall_score": 75,
        "audio_energy_score": 80,
        "scene_change_score": 70,
        "speech_density_score": 75,
        "keyword_score": 70,
    }

    bonus_score = highlight_detection_service.apply_sustained_bonus(segment)

    # Should have +15% bonus for >5 second duration
    expected_bonus = 75 * 1.15
    assert abs(bonus_score - expected_bonus) < 1


@pytest.mark.asyncio
async def test_apply_bonus_for_keywords_plus_high_energy(highlight_detection_service):
    """Test applying +20% bonus for keywords + high energy combination."""
    segment = {
        "overall_score": 70,
        "audio_energy_score": 85,  # High energy
        "keyword_score": 80,  # Has keywords
        "detected_keywords": ["amazing", "incredible"],
    }

    bonus_score = highlight_detection_service.apply_keyword_energy_bonus(segment)

    # Should have +20% bonus
    expected_bonus = 70 * 1.2
    assert abs(bonus_score - expected_bonus) < 1


@pytest.mark.asyncio
async def test_normalize_score_to_0_100_range(highlight_detection_service):
    """Test normalizing final score to 0-100 range."""
    # Score might exceed 100 after bonuses
    score_over_100 = 115

    normalized = highlight_detection_service.normalize_score(score_over_100)

    assert normalized == 100

    # Score below 0 should normalize to 0
    score_below_0 = -5
    normalized = highlight_detection_service.normalize_score(score_below_0)

    assert normalized == 0

    # Score within range should stay the same
    normal_score = 75
    normalized = highlight_detection_service.normalize_score(normal_score)

    assert normalized == 75


@pytest.mark.asyncio
async def test_classify_segments_by_priority(highlight_detection_service):
    """Test classifying segments by priority based on overall score."""
    segments = [
        {"overall_score": 85, "start_time": 10.0},  # High priority (>=70)
        {"overall_score": 65, "start_time": 20.0},  # Medium priority (50-69)
        {"overall_score": 40, "start_time": 30.0},  # Low priority (<50)
        {"overall_score": 92, "start_time": 40.0},  # High priority
    ]

    classified = highlight_detection_service.classify_segments_by_priority(segments)

    assert len(classified["high"]) == 2
    assert len(classified["medium"]) == 1
    assert len(classified["low"]) == 1


@pytest.mark.asyncio
async def test_calculate_keyword_score_multiple_keywords(highlight_detection_service):
    """Test keyword scoring with multiple important keywords."""
    transcript_segment = "This is amazing and incredible content that you should definitely watch"
    keywords = ["amazing", "incredible", "watch"]

    keyword_score, detected = highlight_detection_service.calculate_keyword_score(
        transcript_segment, keywords
    )

    # Multiple important keywords: 80-100
    assert 80 <= keyword_score <= 100
    assert len(detected) == 3


@pytest.mark.asyncio
async def test_calculate_keyword_score_single_keyword(highlight_detection_service):
    """Test keyword scoring with single important keyword."""
    transcript_segment = "This is an amazing video tutorial"
    keywords = ["amazing", "incredible", "watch"]

    keyword_score, detected = highlight_detection_service.calculate_keyword_score(
        transcript_segment, keywords
    )

    # Single important keyword: 50-79
    assert 50 <= keyword_score <= 79
    assert len(detected) == 1


@pytest.mark.asyncio
async def test_calculate_keyword_score_no_keywords(highlight_detection_service):
    """Test keyword scoring with no keywords found."""
    transcript_segment = "This is a regular video segment"
    keywords = ["amazing", "incredible", "watch"]

    keyword_score, detected = highlight_detection_service.calculate_keyword_score(
        transcript_segment, keywords
    )

    # No keywords: 0
    assert keyword_score == 0
    assert len(detected) == 0


@pytest.mark.asyncio
async def test_bonus_for_keyword_clusters(highlight_detection_service):
    """Test bonus scoring for keyword clusters (multiple keywords nearby)."""
    # Keywords very close together
    transcript_segment = "This amazing and incredible moment is the best highlight you should watch"
    keywords = ["amazing", "incredible", "best", "highlight", "watch"]

    keyword_score, detected = highlight_detection_service.calculate_keyword_score(
        transcript_segment, keywords, apply_cluster_bonus=True
    )

    # Should have cluster bonus
    assert keyword_score >= 90
    assert len(detected) == 5


@pytest.mark.asyncio
async def test_rank_highlights_by_score(highlight_detection_service):
    """Test ranking highlights by overall score (1 = best, 2 = second best, etc.)."""
    segments = [
        {"start_time": 10.0, "overall_score": 75},
        {"start_time": 20.0, "overall_score": 92},
        {"start_time": 30.0, "overall_score": 68},
        {"start_time": 40.0, "overall_score": 85},
    ]

    ranked = highlight_detection_service.rank_highlights(segments)

    assert ranked[0]["rank"] == 1
    assert ranked[0]["overall_score"] == 92
    assert ranked[1]["rank"] == 2
    assert ranked[1]["overall_score"] == 85
    assert ranked[2]["rank"] == 3
    assert ranked[2]["overall_score"] == 75
    assert ranked[3]["rank"] == 4
    assert ranked[3]["overall_score"] == 68


@pytest.mark.asyncio
async def test_merge_overlapping_segments(highlight_detection_service):
    """Test merging overlapping highlight segments."""
    segments = [
        {"start_time": 10.0, "end_time": 20.0, "overall_score": 80},
        {"start_time": 18.0, "end_time": 25.0, "overall_score": 85},  # Overlaps
    ]

    merged = highlight_detection_service.merge_overlapping_segments(segments)

    assert len(merged) == 1
    assert merged[0]["start_time"] == 10.0
    assert merged[0]["end_time"] == 25.0
    # Score should be max of overlapping segments
    assert merged[0]["overall_score"] == 85


@pytest.mark.asyncio
async def test_merge_adjacent_segments_within_threshold(highlight_detection_service):
    """Test merging adjacent highlights within 3 seconds."""
    segments = [
        {"start_time": 10.0, "end_time": 15.0, "overall_score": 80},
        {"start_time": 17.0, "end_time": 22.0, "overall_score": 85},  # 2s gap
    ]

    merged = highlight_detection_service.merge_adjacent_segments(
        segments, gap_threshold=3.0
    )

    assert len(merged) == 1
    assert merged[0]["start_time"] == 10.0
    assert merged[0]["end_time"] == 22.0


@pytest.mark.asyncio
async def test_do_not_merge_segments_beyond_threshold(highlight_detection_service):
    """Test not merging segments with gap > 3 seconds."""
    segments = [
        {"start_time": 10.0, "end_time": 15.0, "overall_score": 80},
        {"start_time": 20.0, "end_time": 25.0, "overall_score": 85},  # 5s gap
    ]

    merged = highlight_detection_service.merge_adjacent_segments(
        segments, gap_threshold=3.0
    )

    assert len(merged) == 2  # Should remain separate


@pytest.mark.asyncio
async def test_add_context_padding_to_segments(highlight_detection_service):
    """Test adding context padding (default: 2s before, 3s after)."""
    segment = {"start_time": 10.0, "end_time": 20.0, "overall_score": 80}

    padded = highlight_detection_service.add_context_padding(
        segment, before=2.0, after=3.0
    )

    assert padded["start_time"] == 8.0  # 10 - 2
    assert padded["end_time"] == 23.0  # 20 + 3
    assert padded["context_before_seconds"] == 2.0
    assert padded["context_after_seconds"] == 3.0


@pytest.mark.asyncio
async def test_context_padding_respects_video_boundaries(highlight_detection_service):
    """Test ensuring segments don't exceed video boundaries after padding."""
    # Segment at start of video
    segment_start = {"start_time": 1.0, "end_time": 5.0, "overall_score": 80}

    padded_start = highlight_detection_service.add_context_padding(
        segment_start, before=2.0, after=3.0, video_duration=120.0
    )

    assert padded_start["start_time"] == 0.0  # Can't go before 0

    # Segment at end of video
    segment_end = {"start_time": 115.0, "end_time": 118.0, "overall_score": 80}

    padded_end = highlight_detection_service.add_context_padding(
        segment_end, before=2.0, after=3.0, video_duration=120.0
    )

    assert padded_end["end_time"] == 120.0  # Can't exceed video duration


@pytest.mark.asyncio
async def test_calculate_segment_duration(highlight_detection_service):
    """Test calculating final segment duration_seconds."""
    segment = {"start_time": 10.5, "end_time": 25.3}

    duration = highlight_detection_service.calculate_segment_duration(segment)

    assert duration == 14.8  # 25.3 - 10.5


@pytest.mark.asyncio
async def test_limit_highlights_per_video_top_10(highlight_detection_service):
    """Test limiting highlights to top N (default: top 10)."""
    # Create 20 segments
    segments = [
        {"start_time": i * 10.0, "end_time": i * 10.0 + 10.0, "overall_score": 90 - i}
        for i in range(20)
    ]

    limited = highlight_detection_service.limit_highlights(segments, max_count=10)

    assert len(limited) == 10
    # Should keep top 10 by score
    assert all(seg["overall_score"] >= 80 for seg in limited)


@pytest.mark.asyncio
async def test_different_sensitivity_levels(highlight_detection_service):
    """Test different sensitivity levels produce expected number of highlights."""
    segments = [
        {"start_time": i * 10.0, "end_time": i * 10.0 + 10.0, "overall_score": 90 - i * 2}
        for i in range(25)
    ]

    # Low: top 5, threshold 80
    low = highlight_detection_service.apply_sensitivity(
        segments, sensitivity="low"
    )
    assert len(low) <= 5
    assert all(seg["overall_score"] >= 80 for seg in low)

    # Medium: top 10, threshold 70
    medium = highlight_detection_service.apply_sensitivity(
        segments, sensitivity="medium"
    )
    assert len(medium) <= 10
    assert all(seg["overall_score"] >= 70 for seg in medium)

    # High: top 15, threshold 60
    high = highlight_detection_service.apply_sensitivity(
        segments, sensitivity="high"
    )
    assert len(high) <= 15
    assert all(seg["overall_score"] >= 60 for seg in high)

    # Max: top 20, threshold 50
    max_sens = highlight_detection_service.apply_sensitivity(
        segments, sensitivity="max"
    )
    assert len(max_sens) <= 20
    assert all(seg["overall_score"] >= 50 for seg in max_sens)


@pytest.mark.asyncio
async def test_orchestrate_full_detection_workflow(
    highlight_detection_service, test_video: Video, db_session: AsyncSession
):
    """Test orchestrating full highlight detection workflow."""
    with (
        patch.object(
            highlight_detection_service, "extract_audio_features"
        ) as mock_audio,
        patch.object(
            highlight_detection_service, "extract_video_features"
        ) as mock_video,
        patch.object(
            highlight_detection_service, "extract_speech_features"
        ) as mock_speech,
        patch.object(
            highlight_detection_service, "extract_keyword_features"
        ) as mock_keywords,
    ):
        # Mock component analysis results
        mock_audio.return_value = [
            {"start_time": 10.0, "end_time": 20.0, "audio_score": 85}
        ]
        mock_video.return_value = [
            {"start_time": 10.0, "end_time": 20.0, "scene_score": 70}
        ]
        mock_speech.return_value = [
            {"start_time": 10.0, "end_time": 20.0, "speech_score": 80}
        ]
        mock_keywords.return_value = [
            {
                "start_time": 10.0,
                "end_time": 20.0,
                "keyword_score": 75,
                "detected_keywords": ["amazing"],
            }
        ]

        highlights = await highlight_detection_service.detect_highlights(
            video_id=test_video.id,
            video_path="test.mp4",
            sensitivity="medium",
            db=db_session,
        )

        assert len(highlights) > 0
        assert all("overall_score" in h for h in highlights)
        assert all("rank" in h for h in highlights)


@pytest.mark.asyncio
async def test_cache_detection_results(
    highlight_detection_service, test_video: Video, db_session: AsyncSession
):
    """Test caching detection results to avoid reprocessing."""
    with patch("app.worker.redis.from_url") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.setex = AsyncMock()

        # First call should compute and cache
        await highlight_detection_service.get_or_compute_highlights(
            video_id=test_video.id, video_path="test.mp4", db=db_session
        )

        # Verify cache set was called
        mock_redis_client.setex.assert_called_once()
