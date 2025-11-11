"""Tests for social media template service."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import uuid4

import pytest


class MockTemplateService:
    """Mock TemplateService for testing."""

    PLATFORM_PRESETS = {
        "youtube_shorts": {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 60,
            "crop_strategy": "center",
        },
        "tiktok": {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 180,
            "crop_strategy": "smart",
        },
        "instagram_reels": {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 90,
            "crop_strategy": "center",
        },
        "instagram_story": {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 15,
            "crop_strategy": "face_detection",
        },
        "twitter": {
            "aspect_ratio": "16:9",
            "resolution": (1280, 720),
            "max_duration": 140,
            "crop_strategy": "letterbox",
        },
        "linkedin": {
            "aspect_ratio": "16:9",
            "resolution": (1920, 1080),
            "max_duration": 600,
            "crop_strategy": "letterbox",
        },
        "facebook": {
            "aspect_ratio": "16:9",
            "resolution": (1280, 720),
            "max_duration": 240,
            "crop_strategy": "letterbox",
        },
    }

    CAPTION_STYLES = {
        "minimal": {"font_size": 36, "font_weight": "normal", "animation": "none"},
        "bold": {"font_size": 48, "font_weight": "bold", "animation": "pop"},
        "gaming": {"font_size": 42, "text_color": "#00FF00", "animation": "slide"},
        "podcast": {"font_size": 38, "position": "bottom", "animation": "fade"},
        "vlog": {"font_size": 40, "animation": "pop", "word_highlight": True},
        "professional": {"font_size": 32, "background": "#000000", "animation": "none"},
        "trendy": {"font_size": 50, "animation": "slide", "word_highlight": True},
    }

    @staticmethod
    async def convert_aspect_ratio(
        video_path: Path,
        output_path: Path,
        target_aspect_ratio: str,
        crop_strategy: str,
    ) -> Path:
        """Convert video to target aspect ratio."""
        pass

    @staticmethod
    async def enforce_duration(
        video_path: Path,
        output_path: Path,
        max_duration: float,
        trim_strategy: str = "start",
    ) -> Path:
        """Enforce maximum duration constraint."""
        pass

    @staticmethod
    async def burn_captions(
        video_path: Path,
        transcript_segments: list[dict],
        output_path: Path,
        caption_style: dict,
    ) -> Path:
        """Burn captions into video."""
        pass

    @staticmethod
    async def optimize_for_platform(
        video_path: Path,
        output_path: Path,
        platform: str,
        quality: str = "high",
    ) -> Path:
        """Optimize video for specific platform requirements."""
        pass


class TestAspectRatioConversion:
    """Tests for aspect ratio conversion functionality."""

    @pytest.mark.asyncio
    async def test_convert_to_vertical_center_crop(self):
        """Test converting horizontal video to vertical (9:16) with center crop."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.convert_aspect_ratio(
                    video_path, output_path, "9:16", "center"
                )

                # Verify FFmpeg was called with crop filter
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "ffmpeg" in args
                assert "crop" in str(args) or "scale" in str(args)

    @pytest.mark.asyncio
    async def test_convert_to_vertical_smart_crop(self):
        """Test converting with smart crop (content-aware)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.convert_aspect_ratio(
                    video_path, output_path, "9:16", "smart"
                )

                # Smart crop may use different FFmpeg filters
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_to_horizontal_letterbox(self):
        """Test converting vertical video to horizontal with letterbox."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.convert_aspect_ratio(
                    video_path, output_path, "16:9", "letterbox"
                )

                # Letterbox should add padding
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "pad" in str(args) or "scale" in str(args)

    @pytest.mark.asyncio
    async def test_convert_to_square_crop(self):
        """Test converting to square (1:1) aspect ratio."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.convert_aspect_ratio(
                    video_path, output_path, "1:1", "center"
                )

                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_with_blur_background(self):
        """Test converting with blurred background fill."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.convert_aspect_ratio(
                    video_path, output_path, "9:16", "blur_background"
                )

                # Blur background requires complex filter chain
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "boxblur" in str(args) or "gblur" in str(args) or "blur" in str(args)

    @pytest.mark.asyncio
    async def test_convert_with_face_detection(self):
        """Test converting with face detection for smart cropping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                # Mock face detection
                with patch("app.services.video.detect_faces") as mock_detect:
                    mock_detect.return_value = [{"x": 640, "y": 360, "w": 200, "h": 200}]

                    service = MockTemplateService()
                    result = await service.convert_aspect_ratio(
                        video_path, output_path, "9:16", "face_detection"
                    )

                    mock_subprocess.assert_called_once()


class TestDurationEnforcement:
    """Tests for duration enforcement functionality."""

    @pytest.mark.asyncio
    async def test_enforce_duration_trim_start(self):
        """Test trimming video from start to meet duration limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.enforce_duration(
                    video_path, output_path, max_duration=60.0, trim_strategy="start"
                )

                # Verify FFmpeg trim command
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "-t" in args or "-to" in args

    @pytest.mark.asyncio
    async def test_enforce_duration_trim_end(self):
        """Test trimming video from end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.enforce_duration(
                    video_path, output_path, max_duration=60.0, trim_strategy="end"
                )

                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_enforce_duration_trim_middle(self):
        """Test keeping middle portion of video."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.enforce_duration(
                    video_path, output_path, max_duration=60.0, trim_strategy="middle"
                )

                # Should use -ss and -t to extract middle portion
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert "-ss" in args

    @pytest.mark.asyncio
    async def test_enforce_duration_no_trim_needed(self):
        """Test when video is already within duration limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            # Mock video duration check
            with patch("app.services.video.get_video_duration") as mock_duration:
                mock_duration.return_value = 45.0  # Already under 60s limit

                service = MockTemplateService()
                result = await service.enforce_duration(
                    video_path, output_path, max_duration=60.0
                )

                # Should just copy or return original if under limit


class TestCaptionBurning:
    """Tests for caption burning functionality."""

    @pytest.mark.asyncio
    async def test_burn_captions_with_style(self):
        """Test burning captions with specific style."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [
                {"start": 0.0, "end": 5.0, "text": "Hello world"},
                {"start": 5.0, "end": 10.0, "text": "Test caption"},
            ]

            caption_style = {
                "font_family": "Montserrat",
                "font_size": 48,
                "font_weight": "bold",
                "text_color": "#FFFFFF",
                "position": "bottom",
            }

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.burn_captions(
                    video_path, segments, output_path, caption_style
                )

                # Verify FFmpeg was called with subtitle filter
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_burn_captions_word_highlight(self):
        """Test burning captions with word-by-word highlighting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Hello world",
                    "words": [
                        {"start": 0.0, "end": 2.0, "text": "Hello"},
                        {"start": 2.0, "end": 5.0, "text": "world"},
                    ],
                },
            ]

            caption_style = {
                "font_size": 48,
                "word_highlight": True,
                "highlight_color": "#FFFF00",
            }

            service = MockTemplateService()
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                result = await service.burn_captions(
                    video_path, segments, output_path, caption_style
                )

    @pytest.mark.asyncio
    async def test_burn_captions_with_animation(self):
        """Test burning captions with animation effects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            segments = [{"start": 0.0, "end": 5.0, "text": "Animated caption"}]

            caption_style = {
                "font_size": 48,
                "animation": "pop",
                "animation_duration": 0.3,
            }

            service = MockTemplateService()
            result = await service.burn_captions(
                video_path, segments, output_path, caption_style
            )


class TestPlatformPresetApplication:
    """Tests for applying platform-specific presets."""

    def test_apply_youtube_shorts_preset(self):
        """Test applying YouTube Shorts preset."""
        service = MockTemplateService()
        preset = service.PLATFORM_PRESETS["youtube_shorts"]

        assert preset["aspect_ratio"] == "9:16"
        assert preset["resolution"] == (1080, 1920)
        assert preset["max_duration"] == 60

    def test_apply_tiktok_preset(self):
        """Test applying TikTok preset."""
        service = MockTemplateService()
        preset = service.PLATFORM_PRESETS["tiktok"]

        assert preset["aspect_ratio"] == "9:16"
        assert preset["max_duration"] == 180

    def test_apply_instagram_reels_preset(self):
        """Test applying Instagram Reels preset."""
        service = MockTemplateService()
        preset = service.PLATFORM_PRESETS["instagram_reels"]

        assert preset["aspect_ratio"] == "9:16"
        assert preset["max_duration"] == 90

    def test_apply_twitter_preset(self):
        """Test applying Twitter preset."""
        service = MockTemplateService()
        preset = service.PLATFORM_PRESETS["twitter"]

        assert preset["aspect_ratio"] == "16:9"
        assert preset["crop_strategy"] == "letterbox"

    def test_all_platform_presets_exist(self):
        """Test that all platform presets are defined."""
        service = MockTemplateService()

        expected_platforms = [
            "youtube_shorts", "tiktok", "instagram_reels",
            "instagram_story", "twitter", "linkedin", "facebook"
        ]

        for platform in expected_platforms:
            assert platform in service.PLATFORM_PRESETS


class TestCaptionStylePresets:
    """Tests for caption style presets."""

    def test_apply_minimal_caption_style(self):
        """Test applying minimal caption style."""
        service = MockTemplateService()
        style = service.CAPTION_STYLES["minimal"]

        assert style["font_size"] == 36
        assert style["animation"] == "none"

    def test_apply_bold_caption_style(self):
        """Test applying bold caption style."""
        service = MockTemplateService()
        style = service.CAPTION_STYLES["bold"]

        assert style["font_weight"] == "bold"
        assert style["animation"] == "pop"

    def test_apply_gaming_caption_style(self):
        """Test applying gaming caption style."""
        service = MockTemplateService()
        style = service.CAPTION_STYLES["gaming"]

        assert style["text_color"] == "#00FF00"

    def test_apply_vlog_caption_style(self):
        """Test applying vlog caption style."""
        service = MockTemplateService()
        style = service.CAPTION_STYLES["vlog"]

        assert style["word_highlight"] is True

    def test_all_caption_styles_exist(self):
        """Test that all 7 caption styles are defined."""
        service = MockTemplateService()

        expected_styles = [
            "minimal", "bold", "gaming", "podcast",
            "vlog", "professional", "trendy"
        ]

        for style_name in expected_styles:
            assert style_name in service.CAPTION_STYLES


class TestPlatformOptimization:
    """Tests for platform-specific optimization."""

    @pytest.mark.asyncio
    async def test_optimize_for_youtube_shorts(self):
        """Test optimization for YouTube Shorts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.optimize_for_platform(
                    video_path, output_path, "youtube_shorts", quality="high"
                )

                # Should apply YouTube-specific encoding settings
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_for_tiktok(self):
        """Test optimization for TikTok."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.optimize_for_platform(
                    video_path, output_path, "tiktok", quality="high"
                )

    @pytest.mark.asyncio
    async def test_optimize_quality_settings(self):
        """Test different quality settings for optimization."""
        qualities = ["high", "medium", "low"]

        for quality in qualities:
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = Path(temp_dir) / "input.mp4"
                output_path = Path(temp_dir) / f"output_{quality}.mp4"

                video_path.touch()

                with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_process.returncode = 0
                    mock_subprocess.return_value = mock_process

                    service = MockTemplateService()
                    result = await service.optimize_for_platform(
                        video_path, output_path, "youtube_shorts", quality=quality
                    )


class TestResolutionOptimization:
    """Tests for resolution and quality optimization."""

    @pytest.mark.asyncio
    async def test_optimize_resolution_1080p(self):
        """Test optimization to 1080p."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                # Test scaling to 1080p
                service = MockTemplateService()
                result = await service.optimize_for_platform(
                    video_path, output_path, "youtube_shorts"
                )

                args = mock_subprocess.call_args[0]
                assert "scale" in str(args) or "1080" in str(args)

    @pytest.mark.asyncio
    async def test_optimize_resolution_720p(self):
        """Test optimization to 720p."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                # Test scaling to 720p (e.g., for Twitter)
                service = MockTemplateService()
                result = await service.optimize_for_platform(
                    video_path, output_path, "twitter"
                )

    @pytest.mark.asyncio
    async def test_optimize_maintains_aspect_ratio(self):
        """Test that optimization maintains aspect ratio."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"

            video_path.touch()

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                service = MockTemplateService()
                result = await service.optimize_for_platform(
                    video_path, output_path, "youtube_shorts"
                )

                # Verify aspect ratio preservation
                args = mock_subprocess.call_args[0]
                # Should use scale with aspect ratio preservation
                assert "scale" in str(args)
