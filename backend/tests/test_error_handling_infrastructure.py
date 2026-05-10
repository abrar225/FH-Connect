import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.error_handlers import ErrorCode, ErrorResponse, ErrorHandler, register_error_handlers
from app.core.retry import RetryConfig, with_retry, AI_SERVICE_RETRY_CONFIG
from app.core.fallback import FallbackHandler, FallbackResponse, FallbackType
from app.core.circuit_breaker import get_breaker, GROQ_CIRCUIT_STATE, GEMINI_CIRCUIT_STATE


class TestErrorResponse:
    """Tests for error response schema"""

    def test_error_response_model(self):
        """Test ErrorResponse can be created and serialized"""
        response = ErrorResponse(
            error="Test Error",
            message="Test message",
            code=ErrorCode.INTERNAL_ERROR,
            request_id="test-123",
        )

        data = response.model_dump()
        assert data["error"] == "Test Error"
        assert data["code"] == "INTERNAL_ERROR"
        assert data["request_id"] == "test-123"

    def test_error_response_with_retry_after(self):
        """Test ErrorResponse includes retry_after"""
        response = ErrorResponse(
            error="Service Unavailable",
            message="Service down",
            code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
            retry_after=30,
        )

        data = response.model_dump()
        assert data["retry_after"] == 30

    def test_error_response_with_details(self):
        """Test ErrorResponse includes details"""
        response = ErrorResponse(
            error="Database Error",
            message="Connection failed",
            code=ErrorCode.DATABASE_ERROR,
            details={"host": "localhost", "port": 5432},
        )

        data = response.model_dump()
        assert data["details"]["host"] == "localhost"


class TestRetryConfig:
    """Tests for retry configuration"""

    def test_retry_config_defaults(self):
        """Test RetryConfig has sensible defaults"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.jitter is True

    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation"""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        # Attempt 0: 1.0 * 2^0 = 1.0
        # Attempt 1: 1.0 * 2^1 = 2.0
        # Attempt 2: 1.0 * 2^2 = 4.0
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0

    def test_calculate_delay_max_limit(self):
        """Test delay is capped at max_delay"""
        config = RetryConfig(
            base_delay=10.0,
            max_delay=15.0,
            exponential_base=2.0,
            jitter=False,
        )

        # 10 * 2^3 = 80, but capped at 15
        assert config.calculate_delay(3) == 15.0


class TestRetryDecorator:
    """Tests for retry decorator"""

    @pytest.mark.asyncio
    async def test_retry_success_first_try(self):
        """Test function succeeds on first try"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.1))
        async def succeed_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await succeed_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test function succeeds after some retries"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.1))
        async def fail_twice_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await fail_twice_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises_exception(self):
        """Test that exception is raised after max attempts"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.1))
        async def always_fail_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError):
            await always_fail_function()

        assert call_count == 3


class TestFallbackHandler:
    """Tests for fallback handler"""

    def test_ai_service_fallback_response(self):
        """Test AI service fallback creates proper response"""
        response = FallbackHandler.handle_ai_service_failure(
            ValueError("API timeout"),
            fallback_model="gemma-3-4b-it"
        )

        assert response.success is False
        assert response.fallback is True
        assert response.fallback_type == FallbackType.AI_SERVICE
        assert "temporarily unavailable" in response.message

    def test_transcription_fallback_response(self):
        """Test transcription fallback creates proper response"""
        response = FallbackHandler.handle_transcription_failure()

        assert response.success is False
        assert response.fallback is True
        assert response.fallback_type == FallbackType.TRANSCRIPTION

    def test_report_generation_fallback_response(self):
        """Test report generation fallback creates proper response"""
        response = FallbackHandler.handle_report_generation_failure()

        assert response.success is False
        assert response.fallback is True
        assert response.fallback_type == FallbackType.REPORT_GENERATION

    def test_default_intent_response(self):
        """Test default intent when AI fails"""
        intent = FallbackHandler.get_default_intent()

        assert intent["action"] == "NONE"
        assert intent["confidence"] == 0.0

    def test_default_report_response(self):
        """Test default report when generation fails"""
        report = FallbackHandler.get_default_report()

        assert "temporarily unavailable" in report["executive_summary"]
        assert report["quality_score"] == 0


class TestCircuitBreaker:
    """Tests for circuit breaker"""

    def test_get_breaker_by_state(self):
        """Test getting circuit breaker by state name"""
        groq_breaker = get_breaker(GROQ_CIRCUIT_STATE)
        gemini_breaker = get_breaker(GEMINI_CIRCUIT_STATE)

        assert groq_breaker is not None
        assert gemini_breaker is not None

    def test_get_breaker_invalid_state_raises(self):
        """Test invalid state name raises ValueError"""
        with pytest.raises(ValueError):
            get_breaker("invalid_state")


class TestErrorHandler:
    """Tests for error handler"""

    def test_generate_error_id_unique(self):
        """Test error IDs are unique"""
        id1 = ErrorHandler._generate_error_id()
        id2 = ErrorHandler._generate_error_id()

        assert id1 != id2
        assert len(id1) == 16  # 8 bytes hex = 16 chars


class TestErrorHandlersRegistration:
    """Tests for error handler registration"""

    def test_error_handlers_can_be_registered(self):
        """Test that error handlers can be imported and used"""
        from app.core import error_handlers
        assert hasattr(error_handlers, 'ErrorResponse')
        assert hasattr(error_handlers, 'ErrorHandler')
        assert hasattr(error_handlers, 'register_error_handlers')