"""Unit tests for video validation service."""

import pytest
from fastapi import HTTPException

from app.services.video_validation import VideoValidationService


def test_validate_file_extension_success():
    """Test valid file extensions."""
    # Test all allowed formats
    for ext in ["mp4", "mov", "avi", "webm", "mkv"]:
        result = VideoValidationService.validate_file_extension(f"test.{ext}")
        assert result == ext

        # Test uppercase
        result = VideoValidationService.validate_file_extension(f"test.{ext.upper()}")
        assert result == ext  # Should be lowercased


def test_validate_file_extension_with_multiple_dots():
    """Test file with multiple dots in name."""
    result = VideoValidationService.validate_file_extension("my.video.file.mp4")
    assert result == "mp4"


def test_validate_file_extension_no_extension():
    """Test file without extension fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_file_extension("video")

    assert exc_info.value.status_code == 400
    assert "extension" in str(exc_info.value.detail).lower()


def test_validate_file_extension_empty_filename():
    """Test empty filename fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_file_extension("")

    assert exc_info.value.status_code == 400


def test_validate_file_extension_invalid_format():
    """Test invalid file format fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_file_extension("video.txt")

    assert exc_info.value.status_code == 400
    assert "not allowed" in str(exc_info.value.detail).lower()
    assert "txt" in str(exc_info.value.detail).upper()


def test_validate_file_extension_executable():
    """Test that executable files are rejected."""
    for ext in ["exe", "sh", "bat", "py"]:
        with pytest.raises(HTTPException) as exc_info:
            VideoValidationService.validate_file_extension(f"malicious.{ext}")

        assert exc_info.value.status_code == 400


def test_validate_file_size_success():
    """Test valid file sizes."""
    # Test small file
    VideoValidationService.validate_file_size(1024)  # 1 KB

    # Test medium file
    VideoValidationService.validate_file_size(100 * 1024 * 1024)  # 100 MB

    # Test large file (under max)
    VideoValidationService.validate_file_size(1024 * 1024 * 1024)  # 1 GB


def test_validate_file_size_too_large():
    """Test file size exceeds maximum."""
    from app.core.config import settings

    # Test file larger than maximum
    too_large = settings.max_upload_size_bytes + 1

    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_file_size(too_large)

    assert exc_info.value.status_code == 400
    assert "exceeds" in str(exc_info.value.detail).lower()


def test_validate_file_size_zero():
    """Test zero file size fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_file_size(0)

    assert exc_info.value.status_code == 400
    assert "greater than 0" in str(exc_info.value.detail)


def test_validate_file_size_negative():
    """Test negative file size fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_file_size(-1)

    assert exc_info.value.status_code == 400


def test_validate_mime_type_mp4_success():
    """Test valid MP4 MIME types."""
    VideoValidationService.validate_mime_type("video/mp4", "mp4")
    VideoValidationService.validate_mime_type("video/x-m4v", "mp4")


def test_validate_mime_type_mov_success():
    """Test valid MOV MIME types."""
    VideoValidationService.validate_mime_type("video/quicktime", "mov")
    VideoValidationService.validate_mime_type("video/x-quicktime", "mov")


def test_validate_mime_type_avi_success():
    """Test valid AVI MIME types."""
    VideoValidationService.validate_mime_type("video/x-msvideo", "avi")
    VideoValidationService.validate_mime_type("video/avi", "avi")


def test_validate_mime_type_webm_success():
    """Test valid WebM MIME type."""
    VideoValidationService.validate_mime_type("video/webm", "webm")


def test_validate_mime_type_mkv_success():
    """Test valid MKV MIME types."""
    VideoValidationService.validate_mime_type("video/x-matroska", "mkv")
    VideoValidationService.validate_mime_type("video/mkv", "mkv")


def test_validate_mime_type_with_charset():
    """Test MIME type with charset parameter."""
    VideoValidationService.validate_mime_type("video/mp4; charset=utf-8", "mp4")


def test_validate_mime_type_mismatch():
    """Test MIME type mismatch fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_mime_type("audio/mp3", "mp4")

    assert exc_info.value.status_code == 400
    assert "does not match" in str(exc_info.value.detail).lower()


def test_validate_mime_type_invalid():
    """Test invalid MIME type fails."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_mime_type("application/pdf", "mp4")

    assert exc_info.value.status_code == 400


def test_validate_upload_request_success():
    """Test complete validation success."""
    extension = VideoValidationService.validate_upload_request(
        filename="my_video.mp4",
        file_size=50 * 1024 * 1024,  # 50 MB
        content_type="video/mp4"
    )

    assert extension == "mp4"


def test_validate_upload_request_all_formats():
    """Test validation for all supported formats."""
    mime_types = {
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
        "webm": "video/webm",
        "mkv": "video/x-matroska"
    }

    for ext, mime in mime_types.items():
        extension = VideoValidationService.validate_upload_request(
            filename=f"test.{ext}",
            file_size=10 * 1024 * 1024,  # 10 MB
            content_type=mime
        )
        assert extension == ext


def test_validate_upload_request_invalid_extension():
    """Test validation fails with invalid extension."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_upload_request(
            filename="document.pdf",
            file_size=1024,
            content_type="application/pdf"
        )

    assert exc_info.value.status_code == 400


def test_validate_upload_request_invalid_size():
    """Test validation fails with invalid size."""
    from app.core.config import settings

    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_upload_request(
            filename="video.mp4",
            file_size=settings.max_upload_size_bytes + 1,
            content_type="video/mp4"
        )

    assert exc_info.value.status_code == 400


def test_validate_upload_request_invalid_mime():
    """Test validation fails with invalid MIME type."""
    with pytest.raises(HTTPException) as exc_info:
        VideoValidationService.validate_upload_request(
            filename="video.mp4",
            file_size=1024 * 1024,  # 1 MB
            content_type="audio/mp3"
        )

    assert exc_info.value.status_code == 400


def test_validate_upload_request_complex_filename():
    """Test validation with complex filename."""
    extension = VideoValidationService.validate_upload_request(
        filename="My Video - Recording (2024-01-15) [Final].MP4",
        file_size=100 * 1024 * 1024,
        content_type="video/mp4"
    )

    assert extension == "mp4"
