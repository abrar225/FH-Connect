"""
core/error_handlers.py — Global exception handlers and error response schemas.

Provides consistent error responses across all API endpoints.
"""

import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger("error_handlers")


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""

    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Database errors
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"

    # External service errors
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    AI_SERVICE_TIMEOUT = "AI_SERVICE_TIMEOUT"
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str
    message: str
    code: ErrorCode
    request_id: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None

    model_config = {"use_enum_values": True}


class ErrorHandler:
    """Centralized error handling with logging and monitoring."""

    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_id = ErrorHandler._generate_error_id()
        logger.warning(
            f"Validation error [error_id={error_id}, path={request.url.path}]",
            extra={"error_id": error_id, "error_type": "validation"},
        )

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="Validation Error",
                message=str(exc),
                code=ErrorCode.VALIDATION_ERROR,
                request_id=error_id,
            ).model_dump(),
        )

    @staticmethod
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_id = ErrorHandler._generate_error_id()

        code_map = {
            400: ErrorCode.INVALID_INPUT,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
            503: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        }

        logger.warning(
            f"HTTP exception [error_id={error_id}, status={exc.status_code}, path={request.url.path}]",
            extra={"error_id": error_id, "status_code": exc.status_code},
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="HTTP Error",
                message=exc.detail,
                code=code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR),
                request_id=error_id,
            ).model_dump(),
        )

    @staticmethod
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions with proper logging."""
        error_id = ErrorHandler._generate_error_id()

        # Log full traceback for debugging
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(
            f"Unhandled exception [error_id={error_id}, path={request.url.path}, exception={type(exc).__name__}]",
            extra={
                "error_id": error_id,
                "error_type": type(exc).__name__,
                "traceback": tb_str[:2000],  # Limit traceback length
            },
        )

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                message="An unexpected error occurred. Please try again later.",
                code=ErrorCode.INTERNAL_ERROR,
                request_id=error_id,
                details={"error_type": type(exc).__name__},
            ).model_dump(),
        )

    @staticmethod
    async def handle_database_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle database-related errors."""
        error_id = ErrorHandler._generate_error_id()

        logger.error(
            f"Database error [error_id={error_id}, path={request.url.path}]",
            extra={"error_id": error_id, "error_type": type(exc).__name__},
        )

        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="Service Unavailable",
                message="Database is temporarily unavailable. Please try again later.",
                code=ErrorCode.DATABASE_UNAVAILABLE,
                request_id=error_id,
                retry_after=30,
            ).model_dump(),
        )

    @staticmethod
    def _generate_error_id() -> str:
        """Generate a unique error ID for tracking."""
        import secrets
        return secrets.token_hex(8)


async def register_error_handlers(app):
    """Register all error handlers with the FastAPI app."""
    from fastapi import FastAPI
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await ErrorHandler.handle_validation_error(request, exc)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await ErrorHandler.handle_http_exception(request, exc)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return await ErrorHandler.handle_generic_exception(request, exc)