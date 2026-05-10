"""
core/audit.py — Audit logging for security-sensitive operations.

Records all security-relevant actions for compliance and forensic purposes.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.core.database import db
from app.core.logging import get_logger

logger = get_logger("audit")


class AuditAction(str, Enum):
    """Security-relevant actions to audit."""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"

    # Authorization
    ACCESS_DENIED = "access_denied"
    ADMIN_GRANTED = "admin_granted"
    ADMIN_REVOKED = "admin_revoked"

    # Data operations
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"

    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_INPUT = "suspicious_input"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"

    # Meeting events
    MEETING_CREATED = "meeting_created"
    MEETING_JOINED = "meeting_joined"
    MEETING_LOCKED = "meeting_locked"
    MEETING_ENDED = "meeting_ended"

    # Report events
    REPORT_GENERATED = "report_generated"
    REPORT_ACCESSED = "report_accessed"
    REPORT_SHARED = "report_shared"

    # Integration events
    INTEGRATION_CONNECTED = "integration_connected"
    INTEGRATION_DISCONNECTED = "integration_disconnected"
    WEBHOOK_CALLED = "webhook_called"


class AuditLevel(str, Enum):
    """Audit event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """Log security-relevant events for audit trail."""

    @staticmethod
    async def log(
        action: AuditAction,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
        room_id: Optional[str] = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            action: The type of action being audited
            actor_id: ID of the user performing the action
            target_id: ID of the resource being acted upon
            metadata: Additional context about the action
            level: Severity level of the audit event
            room_id: Associated meeting room ID (if applicable)
        """
        # Always log to application logs for visibility
        log_data = {
            "action": action.value,
            "actor_id": actor_id,
            "target_id": target_id,
            "metadata": metadata or {},
            "level": level.value,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Log at appropriate level
        log_message = f"AUDIT: {action.value}"
        if actor_id:
            log_message += f" by {actor_id}"
        if target_id:
            log_message += f" on {target_id}"

        if level == AuditLevel.WARNING:
            logger.warning(log_message, extra=log_data)
        elif level == AuditLevel.ERROR or level == AuditLevel.CRITICAL:
            logger.error(log_message, extra=log_data)
        else:
            logger.info(log_message, extra=log_data)

        # Store in database if available
        if db.pool:
            try:
                await db.pool.execute(
                    """INSERT INTO audit_logs (action, actor_id, target_id, metadata, level, room_id, created_at)
                       VALUES ($1, $2, $3, $4::jsonb, $5, $6, NOW())""",
                    action.value,
                    actor_id,
                    target_id,
                    json.dumps(metadata) if metadata else "{}",
                    level.value,
                    room_id,
                )
            except Exception as e:
                logger.error(f"Failed to store audit log in database: {e}")

    # Convenience methods for common security events

    @staticmethod
    async def log_login_success(user_id: str, metadata: Optional[Dict] = None) -> None:
        """Log successful login."""
        await AuditLogger.log(
            AuditAction.LOGIN_SUCCESS,
            actor_id=user_id,
            metadata=metadata,
            level=AuditLevel.INFO,
        )

    @staticmethod
    async def log_login_failed(user_id: str, reason: str, metadata: Optional[Dict] = None) -> None:
        """Log failed login attempt."""
        await AuditLogger.log(
            AuditAction.LOGIN_FAILED,
            actor_id=user_id,
            metadata={"reason": reason, **(metadata or {})},
            level=AuditLevel.WARNING,
        )

    @staticmethod
    async def log_access_denied(
        user_id: str,
        resource: str,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log access denied event."""
        await AuditLogger.log(
            AuditAction.ACCESS_DENIED,
            actor_id=user_id,
            target_id=resource,
            metadata={"reason": reason, **(metadata or {})},
            level=AuditLevel.WARNING,
        )

    @staticmethod
    async def log_data_deleted(
        user_id: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log data deletion."""
        await AuditLogger.log(
            AuditAction.DATA_DELETED,
            actor_id=user_id,
            target_id=resource_id,
            metadata={"resource_type": resource_type, **(metadata or {})},
            level=AuditLevel.INFO,
        )

    @staticmethod
    async def log_suspicious_input(
        user_id: Optional[str],
        input_type: str,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log suspicious input detection."""
        await AuditLogger.log(
            AuditAction.SUSPICIOUS_INPUT,
            actor_id=user_id,
            metadata={"input_type": input_type, "reason": reason, **(metadata or {})},
            level=AuditLevel.WARNING,
        )

    @staticmethod
    async def log_rate_limit_exceeded(
        identifier: str,
        endpoint: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log rate limit exceeded event."""
        await AuditLogger.log(
            AuditAction.RATE_LIMIT_EXCEEDED,
            actor_id=identifier,
            target_id=endpoint,
            metadata=metadata,
            level=AuditLevel.WARNING,
        )

    @staticmethod
    async def log_report_accessed(
        user_id: str,
        room_id: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log report access."""
        await AuditLogger.log(
            AuditAction.REPORT_ACCESSED,
            actor_id=user_id,
            target_id=room_id,
            room_id=room_id,
            metadata=metadata,
            level=AuditLevel.INFO,
        )

    @staticmethod
    async def log_meeting_created(
        user_id: str,
        room_id: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log meeting creation."""
        await AuditLogger.log(
            AuditAction.MEETING_CREATED,
            actor_id=user_id,
            target_id=room_id,
            room_id=room_id,
            metadata=metadata,
            level=AuditLevel.INFO,
        )


async def record_audit_event(
    action: str,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    room_id: Optional[str] = None,
) -> None:
    """
    Record an audit event.

    This is a convenience wrapper around AuditLogger.log() for backward compatibility.
    """
    try:
        audit_action = AuditAction(action)
    except ValueError:
        audit_action = AuditAction.DATA_UPDATED  # Default fallback

    await AuditLogger.log(
        action=audit_action,
        actor_id=actor_id,
        target_id=target_id,
        metadata=metadata,
        room_id=room_id,
    )