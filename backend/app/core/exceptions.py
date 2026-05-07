"""
core/exceptions.py — Custom exception hierarchy.

Provides domain-specific exceptions so error handling is precise
and never relies on catching generic Exception.
"""


class FHConnectError(Exception):
    """Base exception for all FH-Connect errors."""
    pass


class DatabaseUnavailableError(FHConnectError):
    """Raised when the database pool is not connected."""
    pass


class IntentDetectionError(FHConnectError):
    """Raised when the LLM intent chain fails."""
    pass


class EventBusError(FHConnectError):
    """Raised for event bus infrastructure errors."""
    pass


class AuthorizationError(FHConnectError):
    """Raised when a user lacks permission for an action."""
    pass


class MeetingNotFoundError(FHConnectError):
    """Raised when a meeting record does not exist."""
    pass
