"""Video file validation service."""

from fastapi import HTTPException, status

from app.core.config import settings


class VideoValidationService:
    """Service for validating video file uploads."""

    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """Validate file extension against allowed formats.

        Args:
            filename: Original filename

        Returns:
            File extension (lowercase)

        Raises:
            HTTPException: If file extension is not allowed
        """
        if not filename or "." not in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have an extension",
            )

        extension = filename.rsplit(".", 1)[-1].lower()

        if extension not in settings.allowed_video_formats:
            allowed_formats = ", ".join(settings.allowed_video_formats).upper()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File format '{extension.upper()}' is not allowed. "
                f"Allowed formats: {allowed_formats}",
            )

        return extension

    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size against maximum upload size.

        Args:
            file_size: File size in bytes

        Raises:
            HTTPException: If file size exceeds maximum
        """
        max_size_bytes = settings.max_upload_size_bytes
        max_size_mb = settings.max_upload_size_mb

        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds "
                f"maximum allowed size ({max_size_mb} MB)",
            )

        if file_size <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be greater than 0",
            )

    @staticmethod
    def validate_mime_type(content_type: str, extension: str) -> None:
        """Validate MIME type matches video format.

        Args:
            content_type: MIME type from request
            extension: File extension (lowercase)

        Raises:
            HTTPException: If MIME type doesn't match format
        """
        # MIME type mapping for video formats
        mime_type_map = {
            "mp4": ["video/mp4", "video/x-m4v"],
            "mov": ["video/quicktime", "video/x-quicktime"],
            "avi": ["video/x-msvideo", "video/avi"],
            "webm": ["video/webm"],
            "mkv": ["video/x-matroska", "video/mkv"],
        }

        expected_mime_types = mime_type_map.get(extension, [])

        if not expected_mime_types:
            # If format not in map, allow common video MIME types
            expected_mime_types = [
                "video/mp4",
                "video/quicktime",
                "video/x-msvideo",
                "video/webm",
                "video/x-matroska",
            ]

        # Check if content_type starts with any expected MIME type
        if not any(content_type.startswith(mime) for mime in expected_mime_types):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MIME type '{content_type}' does not match file format '{extension.upper()}'. "
                f"Expected MIME types: {', '.join(expected_mime_types)}",
            )

    @staticmethod
    def validate_upload_request(filename: str, file_size: int, content_type: str) -> str:
        """Validate complete upload request.

        Args:
            filename: Original filename
            file_size: File size in bytes
            content_type: MIME type of the file

        Returns:
            File extension (lowercase)

        Raises:
            HTTPException: If validation fails
        """
        # Validate file extension
        extension = VideoValidationService.validate_file_extension(filename)

        # Validate file size
        VideoValidationService.validate_file_size(file_size)

        # Validate MIME type
        VideoValidationService.validate_mime_type(content_type, extension)

        return extension
