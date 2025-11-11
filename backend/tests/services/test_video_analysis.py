"""Tests for video analysis service."""

from unittest.mock import Mock, patch

import numpy as np
import pytest


@pytest.fixture
def video_analysis_service():
    """Create VideoAnalysisService instance."""
    from app.services.analysis.video_analysis import VideoAnalysisService

    return VideoAnalysisService()


@pytest.mark.asyncio
async def test_detect_scene_changes_using_pyscenedetect(video_analysis_service):
    """Test detecting scene changes using PySceneDetect."""
    with patch("scenedetect.detect") as mock_detect:
        # Mock scene list with detected scenes
        mock_scene1 = Mock()
        mock_scene1.get_timecode.return_value.get_seconds.return_value = 0.0
        mock_scene2 = Mock()
        mock_scene2.get_timecode.return_value.get_seconds.return_value = 5.5
        mock_scene3 = Mock()
        mock_scene3.get_timecode.return_value.get_seconds.return_value = 12.3

        mock_detect.return_value = [mock_scene1, mock_scene2, mock_scene3]

        scenes = await video_analysis_service.detect_scene_changes(
            "test.mp4", threshold=27.0
        )

        assert len(scenes) >= 2  # Transitions between scenes
        assert all("time" in scene for scene in scenes)


@pytest.mark.asyncio
async def test_analyze_frame_to_frame_differences(video_analysis_service):
    """Test analyzing frame-to-frame differences using histogram comparison."""
    with patch("av.open") as mock_av_open:
        mock_container = Mock()
        mock_stream = Mock()
        mock_container.streams.video = [mock_stream]

        # Create mock video frames
        mock_frames = []
        for i in range(30):  # 30 frames
            frame = Mock()
            frame.time = i / 30.0  # 30 fps
            # Simulate frame change at frame 15
            if i < 15:
                frame_array = np.random.randint(0, 100, (720, 1280, 3), dtype=np.uint8)
            else:
                frame_array = np.random.randint(150, 255, (720, 1280, 3), dtype=np.uint8)
            frame.to_ndarray = Mock(return_value=frame_array)
            mock_frames.append(frame)

        mock_container.decode = Mock(return_value=mock_frames)
        mock_av_open.return_value = mock_container

        differences = video_analysis_service.analyze_frame_differences("test.mp4")

        assert len(differences) > 0
        # Should detect significant difference around frame 15
        assert any(d["difference_score"] > 0.5 for d in differences)


@pytest.mark.asyncio
async def test_calculate_histogram_comparison(video_analysis_service):
    """Test calculating histogram comparison between frames."""
    # Create two different frames
    frame1 = np.random.randint(0, 100, (720, 1280, 3), dtype=np.uint8)
    frame2 = np.random.randint(150, 255, (720, 1280, 3), dtype=np.uint8)

    similarity = video_analysis_service.calculate_histogram_similarity(frame1, frame2)

    assert 0.0 <= similarity <= 1.0
    # Different frames should have low similarity
    assert similarity < 0.7


@pytest.mark.asyncio
async def test_calculate_pixel_differences(video_analysis_service):
    """Test calculating pixel-level differences between frames."""
    # Create two similar frames with slight differences
    frame1 = np.random.randint(100, 150, (720, 1280, 3), dtype=np.uint8)
    frame2 = frame1.copy()
    frame2[200:400, 300:600] = 255  # Change a region

    difference_score = video_analysis_service.calculate_pixel_difference(frame1, frame2)

    assert difference_score > 0
    # Should detect the changed region
    assert difference_score > 0.05  # At least 5% difference


@pytest.mark.asyncio
async def test_identify_significant_scene_transitions(video_analysis_service):
    """Test identifying significant scene transitions based on threshold."""
    # Mock frame differences data
    frame_differences = [
        {"time": 1.0, "difference_score": 0.1},
        {"time": 2.0, "difference_score": 0.15},
        {"time": 3.0, "difference_score": 0.8},  # Significant change
        {"time": 4.0, "difference_score": 0.12},
        {"time": 5.0, "difference_score": 0.75},  # Significant change
        {"time": 6.0, "difference_score": 0.1},
    ]

    transitions = video_analysis_service.identify_significant_transitions(
        frame_differences, threshold=0.6
    )

    assert len(transitions) == 2
    assert transitions[0]["time"] == 3.0
    assert transitions[1]["time"] == 5.0


@pytest.mark.asyncio
async def test_detect_camera_motion(video_analysis_service):
    """Test detecting camera motion and cuts."""
    with patch("av.open") as mock_av_open:
        mock_container = Mock()
        mock_stream = Mock()
        mock_container.streams.video = [mock_stream]

        # Create mock frames with camera motion (shifting content)
        mock_frames = []
        for i in range(30):
            frame = Mock()
            frame.time = i / 30.0
            # Simulate camera pan by shifting image
            base_image = np.random.randint(100, 150, (720, 1280, 3), dtype=np.uint8)
            shifted_image = np.roll(base_image, shift=i * 10, axis=1)
            frame.to_ndarray = Mock(return_value=shifted_image)
            mock_frames.append(frame)

        mock_container.decode = Mock(return_value=mock_frames)
        mock_av_open.return_value = mock_container

        motion_segments = video_analysis_service.detect_camera_motion("test.mp4")

        assert len(motion_segments) > 0
        assert all("start_time" in seg and "end_time" in seg for seg in motion_segments)
        assert all("motion_type" in seg for seg in motion_segments)


@pytest.mark.asyncio
async def test_detect_cuts_vs_gradual_transitions(video_analysis_service):
    """Test distinguishing between cuts and gradual transitions."""
    # Simulate abrupt cut
    cut_diff = {"time": 5.0, "difference_score": 0.9, "change_type": "abrupt"}

    # Simulate gradual transition
    gradual_diffs = [
        {"time": 10.0, "difference_score": 0.3},
        {"time": 10.5, "difference_score": 0.4},
        {"time": 11.0, "difference_score": 0.45},
        {"time": 11.5, "difference_score": 0.5},
    ]

    cut_type = video_analysis_service.classify_transition_type(cut_diff)
    assert cut_type == "cut"

    gradual_type = video_analysis_service.classify_transition_type(gradual_diffs[0])
    assert gradual_type in ["gradual", "fade", "dissolve"]


@pytest.mark.asyncio
async def test_calculate_scene_diversity(video_analysis_service):
    """Test calculating scene diversity (frequent changes vs static scenes)."""
    # High diversity: many scene changes
    high_diversity_scenes = [
        {"time": 1.0},
        {"time": 3.0},
        {"time": 5.0},
        {"time": 7.0},
        {"time": 9.0},
    ]

    diversity_score_high = video_analysis_service.calculate_scene_diversity(
        high_diversity_scenes, video_duration=10.0
    )

    # Low diversity: few scene changes
    low_diversity_scenes = [
        {"time": 5.0},
    ]

    diversity_score_low = video_analysis_service.calculate_scene_diversity(
        low_diversity_scenes, video_duration=10.0
    )

    assert diversity_score_high > diversity_score_low
    assert 0.0 <= diversity_score_high <= 1.0
    assert 0.0 <= diversity_score_low <= 1.0


@pytest.mark.asyncio
async def test_score_scene_changes_based_on_frequency(video_analysis_service):
    """Test scoring scene changes based on frequency (more changes = higher score)."""
    # Many scene changes (high score)
    many_changes = [{"time": i * 2.0} for i in range(15)]  # 15 changes in 30 seconds

    score_high = video_analysis_service.score_scene_changes(
        many_changes, video_duration=30.0
    )

    # Few scene changes (low score)
    few_changes = [{"time": 15.0}]  # 1 change in 30 seconds

    score_low = video_analysis_service.score_scene_changes(
        few_changes, video_duration=30.0
    )

    assert score_high > score_low
    assert 0 <= score_high <= 100
    assert 0 <= score_low <= 100


@pytest.mark.asyncio
async def test_score_scene_changes_based_on_significance(video_analysis_service):
    """Test scoring scene changes based on visual difference magnitude."""
    # High significance changes
    high_sig_changes = [
        {"time": 5.0, "difference_score": 0.9},
        {"time": 10.0, "difference_score": 0.85},
        {"time": 15.0, "difference_score": 0.95},
    ]

    score_high = video_analysis_service.score_scene_changes(
        high_sig_changes, video_duration=20.0
    )

    # Low significance changes
    low_sig_changes = [
        {"time": 5.0, "difference_score": 0.3},
        {"time": 10.0, "difference_score": 0.35},
        {"time": 15.0, "difference_score": 0.4},
    ]

    score_low = video_analysis_service.score_scene_changes(
        low_sig_changes, video_duration=20.0
    )

    assert score_high > score_low


@pytest.mark.asyncio
async def test_apply_timing_bonus_for_audio_alignment(video_analysis_service):
    """Test applying bonus when scene changes align with audio energy."""
    scene_changes = [
        {"time": 5.0, "difference_score": 0.8},
        {"time": 15.0, "difference_score": 0.75},
    ]

    # Mock audio energy data with high energy around 5s and 15s
    audio_energy_timeline = [
        {"start_time": 4.0, "end_time": 6.0, "audio_score": 85},
        {"start_time": 14.0, "end_time": 16.0, "audio_score": 90},
    ]

    scored_changes = video_analysis_service.apply_audio_alignment_bonus(
        scene_changes, audio_energy_timeline
    )

    assert len(scored_changes) == 2
    # Both scene changes should get bonus for alignment
    assert all(change.get("has_audio_alignment_bonus", False) for change in scored_changes)


@pytest.mark.asyncio
async def test_extract_video_features_returns_time_series_data(video_analysis_service):
    """Test extracting video features returns time-series data."""
    with patch.object(video_analysis_service, "detect_scene_changes") as mock_scenes:
        mock_scenes.return_value = [
            {"time": 5.0, "difference_score": 0.8},
            {"time": 15.0, "difference_score": 0.75},
            {"time": 25.0, "difference_score": 0.85},
        ]

        time_series = await video_analysis_service.extract_video_features(
            "test.mp4", video_duration=30.0
        )

        assert isinstance(time_series, list)
        assert len(time_series) > 0
        assert all("start_time" in item for item in time_series)
        assert all("end_time" in item for item in time_series)
        assert all("scene_score" in item for item in time_series)
