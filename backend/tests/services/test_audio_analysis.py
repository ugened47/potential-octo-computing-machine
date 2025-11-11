"""Tests for audio analysis service."""

from unittest.mock import Mock, patch

import numpy as np
import pytest


@pytest.fixture
def audio_analysis_service():
    """Create AudioAnalysisService instance."""
    from app.services.analysis.audio_analysis import AudioAnalysisService

    return AudioAnalysisService()


@pytest.mark.asyncio
async def test_extract_audio_waveform_from_video(audio_analysis_service):
    """Test extracting audio waveform from video file using PyAV."""
    with patch("av.open") as mock_av_open:
        mock_container = Mock()
        mock_stream = Mock()
        mock_container.streams.audio = [mock_stream]

        # Create mock audio frames
        mock_frames = []
        for i in range(10):
            frame = Mock()
            frame.time = i * 0.1
            frame.to_ndarray = Mock(return_value=np.random.rand(1, 4800))
            mock_frames.append(frame)

        mock_container.decode = Mock(return_value=mock_frames)
        mock_av_open.return_value = mock_container

        waveform = await audio_analysis_service.extract_audio_waveform("test.mp4")

        assert waveform is not None
        assert isinstance(waveform, np.ndarray)
        assert len(waveform) > 0


@pytest.mark.asyncio
async def test_calculate_audio_energy_rms(audio_analysis_service):
    """Test calculating audio energy (RMS) for audio windows."""
    # Create test audio with varying energy levels
    # Quiet segment: 0-5 seconds
    quiet_audio = np.random.rand(44100 * 5) * 0.1
    # Loud segment: 5-10 seconds
    loud_audio = np.random.rand(44100 * 5) * 0.9
    # Combine
    audio_data = np.concatenate([quiet_audio, loud_audio])

    energy_windows = audio_analysis_service.calculate_audio_energy(
        audio_data, window_size=0.5, sample_rate=44100
    )

    assert len(energy_windows) > 0
    # First half should have lower energy than second half
    first_half_avg = np.mean([e["energy"] for e in energy_windows[: len(energy_windows) // 2]])
    second_half_avg = np.mean([e["energy"] for e in energy_windows[len(energy_windows) // 2 :]])
    assert second_half_avg > first_half_avg


@pytest.mark.asyncio
async def test_detect_high_energy_segments(audio_analysis_service):
    """Test detecting high-energy segments in audio."""
    # Create mock audio with high energy spike at 2-4 seconds
    audio_data = np.random.rand(44100 * 10) * 0.2  # Background noise
    audio_data[44100 * 2 : 44100 * 4] = 0.9  # High energy at 2-4 seconds

    segments = audio_analysis_service.detect_high_energy_segments(
        audio_data, threshold=0.6, sample_rate=44100
    )

    assert len(segments) > 0
    # Check that detected segment is around 2-4 seconds
    assert any(1.5 <= s["start_time"] <= 2.5 and 3.5 <= s["end_time"] <= 4.5 for s in segments)


@pytest.mark.asyncio
async def test_detect_energy_peaks(audio_analysis_service):
    """Test detecting energy peaks in audio."""
    # Create audio with distinct peaks
    audio_data = np.random.rand(44100 * 10) * 0.2
    # Add peaks at 1s, 4s, 7s
    for peak_time in [1, 4, 7]:
        start_idx = 44100 * peak_time
        audio_data[start_idx : start_idx + 4410] = 0.95  # 100ms peak

    peaks = audio_analysis_service.detect_energy_peaks(
        audio_data, threshold=0.7, sample_rate=44100
    )

    assert len(peaks) >= 3
    # Verify peaks are detected near expected times
    peak_times = [p["time"] for p in peaks]
    assert any(0.5 <= t <= 1.5 for t in peak_times)
    assert any(3.5 <= t <= 4.5 for t in peak_times)
    assert any(6.5 <= t <= 7.5 for t in peak_times)


@pytest.mark.asyncio
async def test_detect_sustained_high_energy_periods(audio_analysis_service):
    """Test detecting sustained high-energy periods (>3 seconds)."""
    # Create audio with sustained high energy at 10-18 seconds
    audio_data = np.random.rand(44100 * 30) * 0.2
    audio_data[44100 * 10 : 44100 * 18] = 0.85  # 8 seconds of high energy

    sustained_segments = audio_analysis_service.detect_sustained_high_energy(
        audio_data, threshold=0.6, min_duration=3.0, sample_rate=44100
    )

    assert len(sustained_segments) > 0
    # Check that sustained segment is detected around 10-18 seconds
    assert any(
        9.5 <= s["start_time"] <= 10.5
        and 17.5 <= s["end_time"] <= 18.5
        and s["duration"] >= 3.0
        for s in sustained_segments
    )


@pytest.mark.asyncio
async def test_detect_sudden_energy_changes(audio_analysis_service):
    """Test detecting sudden energy changes (peaks after quiet periods)."""
    # Create audio with quiet period followed by sudden increase
    audio_data = np.random.rand(44100 * 20) * 0.1  # Quiet background
    # Sudden energy increase at 5s
    audio_data[44100 * 5 : 44100 * 8] = 0.9

    sudden_changes = audio_analysis_service.detect_sudden_energy_changes(
        audio_data, quiet_threshold=0.2, loud_threshold=0.6, sample_rate=44100
    )

    assert len(sudden_changes) > 0
    # Verify sudden change detected around 5s
    assert any(4.5 <= change["time"] <= 5.5 for change in sudden_changes)


@pytest.mark.asyncio
async def test_calculate_speech_density_with_vad(audio_analysis_service):
    """Test calculating speech density using voice activity detection."""
    # Mock VAD to simulate speech and non-speech segments
    # Speech at 0-5s and 10-15s, silence at 5-10s and 15-20s
    audio_data = np.random.rand(44100 * 20)

    with patch("webrtcvad.Vad") as mock_vad_class:
        mock_vad = Mock()
        mock_vad_class.return_value = mock_vad

        # Simulate VAD results: True for speech, False for silence
        def vad_is_speech(frame, sample_rate):
            # This is a simplified mock
            return True  # Adjust based on frame position in real implementation

        mock_vad.is_speech = Mock(side_effect=vad_is_speech)

        speech_segments = audio_analysis_service.calculate_speech_density(
            audio_data, sample_rate=44100
        )

        assert len(speech_segments) > 0
        assert all("start_time" in seg and "end_time" in seg for seg in speech_segments)
        assert all("speech_density" in seg for seg in speech_segments)


@pytest.mark.asyncio
async def test_identify_consistent_speech_segments_podcast_style(audio_analysis_service):
    """Test identifying segments with consistent speech (podcast style)."""
    # Create mock audio representing podcast with consistent speech
    audio_data = np.random.rand(44100 * 60) * 0.5  # Moderate consistent energy

    with patch.object(audio_analysis_service, "calculate_speech_density") as mock_speech_density:
        # Mock consistent speech throughout
        mock_speech_density.return_value = [
            {"start_time": i, "end_time": i + 5, "speech_density": 0.85}
            for i in range(0, 60, 5)
        ]

        consistent_segments = audio_analysis_service.identify_consistent_speech_segments(
            audio_data, min_density=0.7, sample_rate=44100
        )

        assert len(consistent_segments) > 0
        assert all(seg["speech_density"] >= 0.7 for seg in consistent_segments)


@pytest.mark.asyncio
async def test_identify_varied_energy_segments_gaming_style(audio_analysis_service):
    """Test identifying segments with varied energy (gaming style)."""
    # Create mock audio with high variation (gaming)
    audio_data = np.random.rand(44100 * 60)
    # Add high variation: alternate between quiet and loud
    for i in range(0, 60, 2):
        if i % 4 == 0:
            audio_data[44100 * i : 44100 * (i + 1)] = 0.9  # Loud
        else:
            audio_data[44100 * i : 44100 * (i + 1)] = 0.1  # Quiet

    varied_segments = audio_analysis_service.identify_varied_energy_segments(
        audio_data, min_variation=0.3, sample_rate=44100
    )

    assert len(varied_segments) > 0
    assert all(seg["energy_variation"] >= 0.3 for seg in varied_segments)


@pytest.mark.asyncio
async def test_score_audio_features_high_energy(audio_analysis_service):
    """Test scoring audio features returns 80-100 for high energy."""
    # High energy audio
    high_energy_data = np.random.rand(44100 * 10) * 0.95

    score = audio_analysis_service.score_audio_features(
        high_energy_data, sample_rate=44100
    )

    assert 80 <= score <= 100


@pytest.mark.asyncio
async def test_score_audio_features_medium_energy(audio_analysis_service):
    """Test scoring audio features returns 50-79 for medium energy."""
    # Medium energy audio
    medium_energy_data = np.random.rand(44100 * 10) * 0.5

    score = audio_analysis_service.score_audio_features(
        medium_energy_data, sample_rate=44100
    )

    assert 50 <= score <= 79


@pytest.mark.asyncio
async def test_score_audio_features_quiet_background(audio_analysis_service):
    """Test scoring audio features returns 0-49 for quiet/background."""
    # Quiet background audio
    quiet_data = np.random.rand(44100 * 10) * 0.1

    score = audio_analysis_service.score_audio_features(
        quiet_data, sample_rate=44100
    )

    assert 0 <= score <= 49


@pytest.mark.asyncio
async def test_analyze_segment_with_different_audio_types(audio_analysis_service):
    """Test analyzing segments with different audio types (podcast, gaming, music)."""
    # Podcast-style: consistent moderate energy
    podcast_audio = np.random.rand(44100 * 30) * 0.4

    podcast_result = audio_analysis_service.analyze_segment(
        podcast_audio, segment_start=0.0, segment_end=30.0, sample_rate=44100
    )

    assert "audio_energy_score" in podcast_result
    assert "segment_type" in podcast_result
    assert podcast_result["segment_type"] in ["podcast", "consistent_speech", "varied_energy"]

    # Gaming-style: high variation
    gaming_audio = np.random.rand(44100 * 30)
    for i in range(0, 30, 2):
        if i % 4 == 0:
            gaming_audio[44100 * i : 44100 * (i + 1)] = 0.9
        else:
            gaming_audio[44100 * i : 44100 * (i + 1)] = 0.1

    gaming_result = audio_analysis_service.analyze_segment(
        gaming_audio, segment_start=0.0, segment_end=30.0, sample_rate=44100
    )

    assert "audio_energy_score" in gaming_result
    assert gaming_result["energy_variation"] > 0.3


@pytest.mark.asyncio
async def test_extract_audio_features_returns_time_series_data(audio_analysis_service):
    """Test extracting audio features returns time-series data."""
    audio_data = np.random.rand(44100 * 60)

    time_series = audio_analysis_service.extract_audio_features(
        audio_data, sample_rate=44100
    )

    assert isinstance(time_series, list)
    assert len(time_series) > 0
    assert all("start_time" in item for item in time_series)
    assert all("end_time" in item for item in time_series)
    assert all("audio_score" in item for item in time_series)
