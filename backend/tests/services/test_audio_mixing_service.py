"""Tests for audio mixing service."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def audio_mixing_service():
    """Create audio mixing service instance."""
    from app.services.audio_mixing_service import AudioMixingService

    return AudioMixingService()


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake audio content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_video_file():
    """Create a temporary video file."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_mix_audio_tracks_combines_multiple_tracks(
    audio_mixing_service, temp_audio_file
):
    """Test mix_audio_tracks combines multiple audio tracks into one."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        tracks_config = [
            {"path": temp_audio_file, "start_time": 0.0, "volume": 1.0},
            {"path": temp_audio_file, "start_time": 5.0, "volume": 0.8},
        ]

        output_path = "/tmp/mixed_audio.mp3"

        result = await audio_mixing_service.mix_audio_tracks(tracks_config, output_path)

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_mix_audio_tracks_applies_volume_levels(
    audio_mixing_service, temp_audio_file
):
    """Test mix_audio_tracks applies volume levels to each track."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        tracks_config = [
            {"path": temp_audio_file, "start_time": 0.0, "volume": 0.5},
            {"path": temp_audio_file, "start_time": 0.0, "volume": 0.3},
        ]

        output_path = "/tmp/mixed_audio.mp3"

        result = await audio_mixing_service.mix_audio_tracks(tracks_config, output_path)

        # Verify FFmpeg command includes volume filters
        ffmpeg_command = mock_run.call_args[0][0]
        assert "volume=" in " ".join(ffmpeg_command) or "volume" in str(ffmpeg_command)


@pytest.mark.asyncio
async def test_mix_audio_tracks_handles_timing(
    audio_mixing_service, temp_audio_file
):
    """Test mix_audio_tracks handles start_time and end_time for tracks."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        tracks_config = [
            {
                "path": temp_audio_file,
                "start_time": 0.0,
                "end_time": 10.0,
                "volume": 1.0,
            },
            {
                "path": temp_audio_file,
                "start_time": 5.0,
                "end_time": 15.0,
                "volume": 1.0,
            },
        ]

        output_path = "/tmp/mixed_audio.mp3"

        result = await audio_mixing_service.mix_audio_tracks(tracks_config, output_path)

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_apply_audio_fade_applies_fade_in_and_out(
    audio_mixing_service, temp_audio_file
):
    """Test apply_audio_fade applies fade in and fade out effects."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/faded_audio.mp3"

        result = await audio_mixing_service.apply_audio_fade(
            temp_audio_file,
            fade_in=1.0,  # 1 second fade in
            fade_out=2.0,  # 2 second fade out
            output_path=output_path,
        )

        assert result == output_path
        assert mock_run.called

        # Verify FFmpeg command includes fade filters
        ffmpeg_command = mock_run.call_args[0][0]
        assert "afade" in " ".join(ffmpeg_command)


@pytest.mark.asyncio
async def test_apply_audio_fade_in_only(audio_mixing_service, temp_audio_file):
    """Test apply_audio_fade with fade in only."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/faded_audio.mp3"

        result = await audio_mixing_service.apply_audio_fade(
            temp_audio_file,
            fade_in=1.5,
            fade_out=0.0,  # No fade out
            output_path=output_path,
        )

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_normalize_audio_normalizes_to_target_level(
    audio_mixing_service, temp_audio_file
):
    """Test normalize_audio normalizes audio to target level."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/normalized_audio.mp3"
        target_level = -16.0  # -16 LUFS

        result = await audio_mixing_service.normalize_audio(
            temp_audio_file, target_level, output_path
        )

        assert result == output_path
        assert mock_run.called

        # Verify FFmpeg command includes loudnorm filter
        ffmpeg_command = mock_run.call_args[0][0]
        assert "loudnorm" in " ".join(ffmpeg_command)


@pytest.mark.asyncio
async def test_extract_audio_from_video(audio_mixing_service, temp_video_file):
    """Test extract_audio_from_video extracts audio track from video."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/extracted_audio.mp3"

        result = await audio_mixing_service.extract_audio_from_video(
            temp_video_file, output_path
        )

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_extract_audio_from_video_with_trim(
    audio_mixing_service, temp_video_file
):
    """Test extract_audio_from_video with start time and duration."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/extracted_audio.mp3"

        result = await audio_mixing_service.extract_audio_from_video(
            temp_video_file, output_path, start=5.0, duration=10.0
        )

        assert result == output_path
        assert mock_run.called

        # Verify FFmpeg command includes start and duration
        ffmpeg_command = mock_run.call_args[0][0]
        command_str = " ".join(ffmpeg_command)
        assert "-ss" in command_str  # Start time
        assert "-t" in command_str  # Duration


@pytest.mark.asyncio
async def test_calculate_audio_levels_analyzes_audio(
    audio_mixing_service, temp_audio_file
):
    """Test calculate_audio_levels analyzes audio levels."""
    with patch("subprocess.run") as mock_run:
        # Mock FFmpeg output with audio stats
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="[Parsed_volumedetect] max_volume: -5.0 dB\n"
            "[Parsed_volumedetect] mean_volume: -20.0 dB",
        )

        result = audio_mixing_service.calculate_audio_levels(temp_audio_file)

        assert "max_volume" in result or "peak" in result
        assert mock_run.called


@pytest.mark.asyncio
async def test_create_audio_waveform_generates_waveform_image(
    audio_mixing_service, temp_audio_file
):
    """Test create_audio_waveform generates waveform visualization."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/waveform.png"
        width = 1000
        height = 200

        result = await audio_mixing_service.create_audio_waveform(
            temp_audio_file, width, height, output_path
        )

        assert result == output_path
        assert mock_run.called

        # Verify FFmpeg command includes showwavespic filter
        ffmpeg_command = mock_run.call_args[0][0]
        assert "showwavespic" in " ".join(ffmpeg_command)


@pytest.mark.asyncio
async def test_mix_audio_tracks_handles_stereo_panning(
    audio_mixing_service, temp_audio_file
):
    """Test mix_audio_tracks handles stereo panning for each track."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        tracks_config = [
            {
                "path": temp_audio_file,
                "start_time": 0.0,
                "volume": 1.0,
                "pan": -0.5,  # Pan left
            },
            {
                "path": temp_audio_file,
                "start_time": 0.0,
                "volume": 1.0,
                "pan": 0.5,  # Pan right
            },
        ]

        output_path = "/tmp/mixed_audio.mp3"

        result = await audio_mixing_service.mix_audio_tracks(tracks_config, output_path)

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_mix_audio_tracks_error_handling(audio_mixing_service):
    """Test mix_audio_tracks handles FFmpeg errors gracefully."""
    with patch("subprocess.run") as mock_run:
        # Simulate FFmpeg error
        mock_run.return_value = MagicMock(
            returncode=1, stderr="FFmpeg error: Invalid input"
        )

        tracks_config = [
            {"path": "/invalid/path.mp3", "start_time": 0.0, "volume": 1.0}
        ]

        output_path = "/tmp/mixed_audio.mp3"

        with pytest.raises(Exception):
            await audio_mixing_service.mix_audio_tracks(tracks_config, output_path)
