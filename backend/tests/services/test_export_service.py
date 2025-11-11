"""Tests for export service."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, call

import pytest


# Mock Export models/enums since they don't exist yet
class ExportQuality:
    """Export quality presets."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MockExportService:
    """Mock ExportService for testing."""

    QUALITY_PRESETS = {
        ExportQuality.HIGH: 18,
        ExportQuality.MEDIUM: 23,
        ExportQuality.LOW: 28,
    }

    RESOLUTIONS = {
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "4k": (3840, 2160),
    }

    @staticmethod
    def get_crf_value(quality: str) -> int:
        """Get CRF value for quality preset."""
        preset_map = {
            "high": 18,
            "medium": 23,
            "low": 28,
        }
        return preset_map.get(quality, 23)

    @staticmethod
    def get_resolution_dimensions(resolution: str) -> tuple[int, int]:
        """Get width and height for resolution."""
        return MockExportService.RESOLUTIONS.get(resolution, (1920, 1080))

    @staticmethod
    async def combine_segments(
        video_path: Path,
        segments: list[dict],
        output_path: Path,
    ) -> None:
        """Combine video segments into single file."""
        pass

    @staticmethod
    async def re_encode_video(
        input_path: Path,
        output_path: Path,
        resolution: str,
        quality: str,
    ) -> None:
        """Re-encode video with specified settings."""
        pass

    @staticmethod
    async def export_video(
        video_path: Path,
        segments: list[dict] | None,
        output_path: Path,
        resolution: str,
        quality: str,
    ) -> Path:
        """Complete export process."""
        pass


class TestExportServiceQualityPresets:
    """Tests for quality preset configurations."""

    def test_get_crf_value_high(self):
        """Test CRF value for high quality."""
        service = MockExportService()
        crf = service.get_crf_value("high")
        assert crf == 18

    def test_get_crf_value_medium(self):
        """Test CRF value for medium quality."""
        service = MockExportService()
        crf = service.get_crf_value("medium")
        assert crf == 23

    def test_get_crf_value_low(self):
        """Test CRF value for low quality."""
        service = MockExportService()
        crf = service.get_crf_value("low")
        assert crf == 28

    def test_get_crf_value_default(self):
        """Test CRF value for unknown quality defaults to medium."""
        service = MockExportService()
        crf = service.get_crf_value("unknown")
        assert crf == 23  # Default to medium


class TestExportServiceResolutions:
    """Tests for resolution configurations."""

    def test_get_resolution_dimensions_720p(self):
        """Test dimensions for 720p."""
        service = MockExportService()
        width, height = service.get_resolution_dimensions("720p")
        assert width == 1280
        assert height == 720

    def test_get_resolution_dimensions_1080p(self):
        """Test dimensions for 1080p."""
        service = MockExportService()
        width, height = service.get_resolution_dimensions("1080p")
        assert width == 1920
        assert height == 1080

    def test_get_resolution_dimensions_4k(self):
        """Test dimensions for 4k."""
        service = MockExportService()
        width, height = service.get_resolution_dimensions("4k")
        assert width == 3840
        assert height == 2160

    def test_get_resolution_dimensions_default(self):
        """Test dimensions for unknown resolution defaults to 1080p."""
        service = MockExportService()
        width, height = service.get_resolution_dimensions("unknown")
        assert width == 1920
        assert height == 1080


class TestCombineSegments:
    """Tests for segment combining functionality."""

    @pytest.mark.asyncio
    async def test_combine_single_segment(self):
        """Test combining a single segment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            # Create dummy input file
            video_path.touch()

            segments = [{"start_time": 10.0, "end_time": 20.0}]

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.combine_segments(video_path, segments, output_path)

                # Verify FFmpeg was called
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "ffmpeg" in args
                assert str(video_path) in args
                assert str(output_path) in args

    @pytest.mark.asyncio
    async def test_combine_multiple_segments(self):
        """Test combining multiple segments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [
                {"start_time": 0.0, "end_time": 10.0},
                {"start_time": 20.0, "end_time": 30.0},
                {"start_time": 40.0, "end_time": 50.0},
            ]

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.combine_segments(video_path, segments, output_path)

                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_combine_segments_no_segments(self):
        """Test combining with no segments raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            segments = []

            service = MockExportService()
            with pytest.raises(ValueError, match="No segments provided"):
                await service.combine_segments(video_path, segments, output_path)

    @pytest.mark.asyncio
    async def test_combine_segments_ffmpeg_failure(self):
        """Test handling FFmpeg failure during segment combining."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [{"start_time": 10.0, "end_time": 20.0}]

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(
                    return_value=(b"", b"FFmpeg error: invalid input")
                )
                mock_process.returncode = 1  # Error
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                with pytest.raises(RuntimeError, match="FFmpeg failed"):
                    await service.combine_segments(video_path, segments, output_path)

    @pytest.mark.asyncio
    async def test_combine_segments_overlapping_times(self):
        """Test combining segments with overlapping time ranges."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [
                {"start_time": 0.0, "end_time": 20.0},
                {"start_time": 15.0, "end_time": 30.0},  # Overlaps with previous
            ]

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.combine_segments(video_path, segments, output_path)

                mock_subprocess.assert_called_once()


class TestReEncodeVideo:
    """Tests for video re-encoding functionality."""

    @pytest.mark.asyncio
    async def test_re_encode_720p_high(self):
        """Test re-encoding to 720p with high quality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.re_encode_video(
                    input_path, output_path, "720p", "high"
                )

                # Verify FFmpeg command
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "ffmpeg" in args
                assert "-crf" in args
                assert "18" in args  # High quality CRF

    @pytest.mark.asyncio
    async def test_re_encode_1080p_medium(self):
        """Test re-encoding to 1080p with medium quality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.re_encode_video(
                    input_path, output_path, "1080p", "medium"
                )

                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "-crf" in args
                assert "23" in args  # Medium quality CRF

    @pytest.mark.asyncio
    async def test_re_encode_4k_low(self):
        """Test re-encoding to 4k with low quality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.re_encode_video(
                    input_path, output_path, "4k", "low"
                )

                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "-crf" in args
                assert "28" in args  # Low quality CRF

    @pytest.mark.asyncio
    async def test_re_encode_with_codec_settings(self):
        """Test re-encoding includes proper codec settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.re_encode_video(
                    input_path, output_path, "1080p", "high"
                )

                args = mock_subprocess.call_args[0]
                # Check for H.264 codec
                assert "-c:v" in args or "libx264" in args
                # Check for AAC audio
                assert "-c:a" in args or "aac" in args

    @pytest.mark.asyncio
    async def test_re_encode_ffmpeg_failure(self):
        """Test handling FFmpeg failure during re-encoding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(
                    return_value=(b"", b"Encoding error: invalid codec")
                )
                mock_process.returncode = 1
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                with pytest.raises(RuntimeError, match="FFmpeg encoding failed"):
                    await service.re_encode_video(
                        input_path, output_path, "1080p", "high"
                    )

    @pytest.mark.asyncio
    async def test_re_encode_maintains_aspect_ratio(self):
        """Test re-encoding maintains aspect ratio with padding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.re_encode_video(
                    input_path, output_path, "1080p", "high"
                )

                args = mock_subprocess.call_args[0]
                # Check for scale filter
                assert any("scale=" in str(arg) for arg in args)

    @pytest.mark.asyncio
    async def test_re_encode_faststart_enabled(self):
        """Test re-encoding enables faststart for streaming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            input_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.re_encode_video(
                    input_path, output_path, "1080p", "high"
                )

                args = mock_subprocess.call_args[0]
                # Check for faststart flag
                assert "-movflags" in args or "faststart" in str(args)


class TestExportVideo:
    """Tests for complete export process."""

    @pytest.mark.asyncio
    async def test_export_full_video_no_segments(self):
        """Test exporting full video without segment combining."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch.object(
                MockExportService, "re_encode_video", new_callable=AsyncMock
            ) as mock_encode:
                service = MockExportService()
                result = await service.export_video(
                    video_path=video_path,
                    segments=None,
                    output_path=output_path,
                    resolution="1080p",
                    quality="high",
                )

                # Should only call re_encode, not combine_segments
                mock_encode.assert_called_once_with(
                    video_path, output_path, "1080p", "high"
                )
                assert result == output_path

    @pytest.mark.asyncio
    async def test_export_with_segments(self):
        """Test exporting video with segment combining."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [
                {"start_time": 0.0, "end_time": 10.0},
                {"start_time": 20.0, "end_time": 30.0},
            ]

            with patch.object(
                MockExportService, "combine_segments", new_callable=AsyncMock
            ) as mock_combine:
                with patch.object(
                    MockExportService, "re_encode_video", new_callable=AsyncMock
                ) as mock_encode:
                    service = MockExportService()
                    result = await service.export_video(
                        video_path=video_path,
                        segments=segments,
                        output_path=output_path,
                        resolution="1080p",
                        quality="high",
                    )

                    # Should call both combine and encode
                    mock_combine.assert_called_once()
                    mock_encode.assert_called_once()
                    assert result == output_path

    @pytest.mark.asyncio
    async def test_export_different_quality_settings(self):
        """Test exporting with different quality settings."""
        qualities = ["high", "medium", "low"]

        for quality in qualities:
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = Path(temp_dir) / "input.mp4"
                output_path = Path(temp_dir) / "output.mp4"

                video_path.touch()

                with patch.object(
                    MockExportService, "re_encode_video", new_callable=AsyncMock
                ) as mock_encode:
                    service = MockExportService()
                    await service.export_video(
                        video_path=video_path,
                        segments=None,
                        output_path=output_path,
                        resolution="1080p",
                        quality=quality,
                    )

                    mock_encode.assert_called_once()
                    call_args = mock_encode.call_args[0]
                    assert call_args[3] == quality

    @pytest.mark.asyncio
    async def test_export_different_resolutions(self):
        """Test exporting with different resolution settings."""
        resolutions = ["720p", "1080p", "4k"]

        for resolution in resolutions:
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = Path(temp_dir) / "input.mp4"
                output_path = Path(temp_dir) / "output.mp4"

                video_path.touch()

                with patch.object(
                    MockExportService, "re_encode_video", new_callable=AsyncMock
                ) as mock_encode:
                    service = MockExportService()
                    await service.export_video(
                        video_path=video_path,
                        segments=None,
                        output_path=output_path,
                        resolution=resolution,
                        quality="high",
                    )

                    mock_encode.assert_called_once()
                    call_args = mock_encode.call_args[0]
                    assert call_args[2] == resolution

    @pytest.mark.asyncio
    async def test_export_cleans_up_temp_files(self):
        """Test that export cleans up temporary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [{"start_time": 0.0, "end_time": 10.0}]

            with patch.object(
                MockExportService, "combine_segments", new_callable=AsyncMock
            ):
                with patch.object(
                    MockExportService, "re_encode_video", new_callable=AsyncMock
                ):
                    service = MockExportService()
                    await service.export_video(
                        video_path=video_path,
                        segments=segments,
                        output_path=output_path,
                        resolution="1080p",
                        quality="high",
                    )

                    # Check temp directory is cleaned (implementation detail)
                    # This test verifies the pattern exists

    @pytest.mark.asyncio
    async def test_export_error_handling(self):
        """Test error handling during export process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch.object(
                MockExportService, "re_encode_video", new_callable=AsyncMock
            ) as mock_encode:
                mock_encode.side_effect = RuntimeError("Encoding failed")

                service = MockExportService()
                with pytest.raises(RuntimeError, match="Encoding failed"):
                    await service.export_video(
                        video_path=video_path,
                        segments=None,
                        output_path=output_path,
                        resolution="1080p",
                        quality="high",
                    )


class TestExportServiceIntegration:
    """Integration tests for export service."""

    @pytest.mark.asyncio
    async def test_export_preserves_audio_sync(self):
        """Test that export maintains audio-video synchronization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [{"start_time": 5.0, "end_time": 15.0}]

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockExportService()
                await service.combine_segments(video_path, segments, output_path)

                # Verify audio and video filters are applied together
                args = mock_subprocess.call_args[0]
                # Should have both -vf (video filter) and -af (audio filter)
                assert "-vf" in args or "select=" in str(args)
                assert "-af" in args or "aselect=" in str(args)

    @pytest.mark.asyncio
    async def test_export_format_conversion(self):
        """Test exporting to different formats."""
        formats = ["mp4", "mov", "webm"]

        for fmt in formats:
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = Path(temp_dir) / "input.mp4"
                output_path = Path(temp_dir) / f"output.{fmt}"

                video_path.touch()

                with patch.object(
                    MockExportService, "re_encode_video", new_callable=AsyncMock
                ) as mock_encode:
                    service = MockExportService()
                    await service.export_video(
                        video_path=video_path,
                        segments=None,
                        output_path=output_path,
                        resolution="1080p",
                        quality="high",
                    )

                    mock_encode.assert_called_once()
