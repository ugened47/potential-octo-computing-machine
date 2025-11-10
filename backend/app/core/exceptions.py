"""Custom exception classes for the application."""

from typing import Any


class AppException(Exception):
    """Base exception class for application errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        """Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str | None = None):
        """Initialize not found error.

        Args:
            resource: Resource type (e.g., "Video", "User")
            resource_id: Resource identifier
        """
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id},
        )


class ValidationError(AppException):
    """Validation error."""

    def __init__(
        self, message: str, field: str | None = None, details: dict[str, Any] | None = None
    ):
        """Initialize validation error.

        Args:
            message: Validation error message
            field: Field name that failed validation
            details: Additional validation details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=error_details,
        )


class AuthenticationError(AppException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error.

        Args:
            message: Error message
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(AppException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        """Initialize authorization error.

        Args:
            message: Error message
        """
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class ConflictError(AppException):
    """Resource conflict error."""

    def __init__(self, message: str, resource: str | None = None):
        """Initialize conflict error.

        Args:
            message: Error message
            resource: Resource type
        """
        details = {}
        if resource:
            details["resource"] = resource
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
        )


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
        """
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class ProcessingError(AppException):
    """Video processing error."""

    def __init__(self, message: str, video_id: str | None = None):
        """Initialize processing error.

        Args:
            message: Error message
            video_id: Video ID that failed processing
        """
        details = {}
        if video_id:
            details["video_id"] = video_id
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            status_code=500,
            details=details,
        )


class ExternalServiceError(AppException):
    """External service error."""

    def __init__(self, service: str, message: str):
        """Initialize external service error.

        Args:
            service: Service name (e.g., "OpenAI", "S3")
            message: Error message
        """
        super().__init__(
            message=f"{service} error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service},
        )
