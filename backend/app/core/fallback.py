"""
core/fallback.py — Fallback behaviors for external services.

Provides graceful degradation when external services (AI, transcription, etc.) fail.
"""

from typing import Any, Dict, Optional
from enum import Enum

from app.core.logging import get_logger

logger = get_logger("fallback")


class FallbackType(str, Enum):
    """Types of fallback behaviors."""

    AI_SERVICE = "ai_service"
    TRANSCRIPTION = "transcription"
    REPORT_GENERATION = "report_generation"
    EXTERNAL_API = "external_api"


class FallbackResponse:
    """Standard fallback response when a service fails."""

    def __init__(
        self,
        success: bool = False,
        fallback: bool = True,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
        fallback_type: Optional[FallbackType] = None,
    ):
        self.success = success
        self.fallback = fallback
        self.message = message
        self.data = data or {}
        self.fallback_type = fallback_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "fallback": self.fallback,
            "message": self.message,
            "data": self.data,
            "fallback_type": self.fallback_type.value if self.fallback_type else None,
        }


class FallbackHandler:
    """Handles fallback behavior for different service types."""

    @staticmethod
    def handle_ai_service_failure(
        original_error: Exception,
        fallback_model: Optional[str] = None
    ) -> FallbackResponse:
        """Handle AI service failure with graceful fallback."""
        logger.warning(
            f"AI service failed, using fallback [error={type(original_error).__name__}, fallback_model={fallback_model}]",
            extra={
                "error_type": type(original_error).__name__,
                "fallback_model": fallback_model,
            },
        )

        return FallbackResponse(
            success=False,
            fallback=True,
            message="AI service temporarily unavailable. Please try again later.",
            data={
                "error": type(original_error).__name__,
                "fallback_used": fallback_model is not None,
            },
            fallback_type=FallbackType.AI_SERVICE,
        )

    @staticmethod
    def handle_transcription_failure() -> FallbackResponse:
        """Handle transcription service failure."""
        logger.warning("Transcription service failed, using fallback")

        return FallbackResponse(
            success=False,
            fallback=True,
            message="Transcription service is temporarily unavailable. Meeting will continue without live transcription.",
            data={"service": "deepgram"},
            fallback_type=FallbackType.TRANSCRIPTION,
        )

    @staticmethod
    def handle_report_generation_failure() -> FallbackResponse:
        """Handle report generation failure."""
        logger.warning("Report generation failed, using fallback")

        return FallbackResponse(
            success=False,
            fallback=True,
            message="Report generation is temporarily unavailable. You can request the report later.",
            data={"service": "report_generator"},
            fallback_type=FallbackType.REPORT_GENERATION,
        )

    @staticmethod
    def get_default_intent() -> Dict[str, Any]:
        """Get default intent response when all AI services fail."""
        return {
            "action": "NONE",
            "title": None,
            "assignee": None,
            "deadline": None,
            "target_task_id": None,
            "confidence": 0.0,
        }

    @staticmethod
    def get_default_report() -> Dict[str, Any]:
        """Get default report when report generation fails."""
        return {
            "executive_summary": "Report generation is temporarily unavailable. Please try again later.",
            "key_decisions": [],
            "tasks": [],
            "meeting_minutes": "Report generation failed. Please retry.",
            "quality_score": 0,
        }


# Decorator for automatic fallback handling
def with_fallback(fallback_type: FallbackType):
    """Decorator to add fallback behavior to functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Fallback triggered [func={func.__name__}, type={fallback_type}]",
                    extra={"function": func.__name__, "fallback_type": fallback_type.value},
                )

                if fallback_type == FallbackType.AI_SERVICE:
                    return FallbackHandler.handle_ai_service_failure(e)
                elif fallback_type == FallbackType.TRANSCRIPTION:
                    return FallbackHandler.handle_transcription_failure()
                elif fallback_type == FallbackType.REPORT_GENERATION:
                    return FallbackHandler.handle_report_generation_failure()
                else:
                    return FallbackResponse(
                        success=False,
                        fallback=True,
                        message="Service temporarily unavailable",
                    )
        return wrapper
    return decorator