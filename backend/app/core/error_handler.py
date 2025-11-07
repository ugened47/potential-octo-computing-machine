"""Centralized error handling for FastAPI application."""

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import AppException
from app.core.config import settings

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions.

    Args:
        request: FastAPI request
        exc: Application exception

    Returns:
        JSONResponse: Error response
    """
    # Log error with context
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    # Don't expose internal error details in production
    response_data = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
        }
    }

    # Include details in development
    if settings.debug:
        response_data["error"]["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request
        exc: Pydantic validation error

    Returns:
        JSONResponse: Error response
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error: {len(errors)} field(s) failed validation",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"fields": errors},
            }
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors.

    Args:
        request: FastAPI request
        exc: SQLAlchemy integrity error

    Returns:
        JSONResponse: Error response
    """
    logger.error(
        f"Database integrity error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Check for common integrity errors
    error_message = "Database operation failed"
    error_code = "DATABASE_ERROR"

    if "unique constraint" in str(exc.orig).lower() or "duplicate key" in str(exc.orig).lower():
        error_message = "Resource already exists"
        error_code = "CONFLICT"
    elif "foreign key constraint" in str(exc.orig).lower():
        error_message = "Referenced resource does not exist"
        error_code = "NOT_FOUND"

    response_data = {
        "error": {
            "code": error_code,
            "message": error_message,
        }
    }

    if settings.debug:
        response_data["error"]["details"] = {"database_error": str(exc)}

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT if error_code == "CONFLICT" else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy errors.

    Args:
        request: FastAPI request
        exc: SQLAlchemy error

    Returns:
        JSONResponse: Error response
    """
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    response_data = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "Database operation failed",
        }
    }

    if settings.debug:
        response_data["error"]["details"] = {"database_error": str(exc)}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException.

    Args:
        request: FastAPI request
        exc: HTTPException

    Returns:
        JSONResponse: Error response
    """
    # Log error
    logger.warning(
        f"HTTP error: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Determine error code from status code
    error_codes = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_ERROR",
        403: "AUTHORIZATION_ERROR",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
    }
    error_code = error_codes.get(exc.status_code, "HTTP_ERROR")

    response_data = {
        "error": {
            "code": error_code,
            "message": exc.detail if isinstance(exc.detail, str) else "An error occurred",
        }
    }

    # Include headers if present
    if exc.headers:
        response_data["error"]["details"] = {"headers": exc.headers}

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers or {},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSONResponse: Error response
    """
    logger.exception(
        f"Unexpected error: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    response_data = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
        }
    }

    if settings.debug:
        response_data["error"]["details"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )

