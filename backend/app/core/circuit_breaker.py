import pybreaker
from app.core.logging import get_logger

logger = get_logger("circuit_breaker")

CircuitBreakerError = pybreaker.CircuitBreakerError

GROQ_CIRCUIT_STATE = "groq"
GEMINI_CIRCUIT_STATE = "gemini"
DEEPGRAM_CIRCUIT_STATE = "deepgram"
LIVEKIT_CIRCUIT_STATE = "livekit"

GROQ_BREAKER = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    exclude=[pybreaker.CircuitBreakerError],
)
GEMINI_BREAKER = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    exclude=[pybreaker.CircuitBreakerError],
)
DEEPGRAM_BREAKER = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    exclude=[pybreaker.CircuitBreakerError],
)
LIVEKIT_BREAKER = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    exclude=[pybreaker.CircuitBreakerError],
)


def get_breaker(state: str) -> pybreaker.CircuitBreaker:
    """Get circuit breaker by state name."""
    breakers = {
        GROQ_CIRCUIT_STATE: GROQ_BREAKER,
        GEMINI_CIRCUIT_STATE: GEMINI_BREAKER,
        DEEPGRAM_CIRCUIT_STATE: DEEPGRAM_BREAKER,
        LIVEKIT_CIRCUIT_STATE: LIVEKIT_BREAKER,
    }
    if state not in breakers:
        raise ValueError(f"Unknown circuit breaker state: {state}")
    return breakers[state]


def log_breaker_state(state: str, breaker: pybreaker.CircuitBreaker):
    """Log circuit breaker state changes."""
    logger.info(
        f"Circuit breaker state [state={state}, fail_count={breaker.fail_count}, "
        f"fail_max={breaker.fail_max}, is_open={breaker.is_open}]"
    )