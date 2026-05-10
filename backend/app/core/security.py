"""
core/security.py — Security utilities for input validation, sanitization, and protection.

Provides protection against common security vulnerabilities like injection attacks,
XSS, and malicious input.
"""

import html
import re
import unicodedata
from typing import Any, Optional
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger("security")


class InputSanitizer:
    """Sanitize and validate user input."""

    # Patterns that indicate potentially malicious input
    INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(<script|javascript:|onerror=|onclick=)",
        r"(\$\{.*\}|\{\{.*\}\})",
    ]

    # Dangerous HTML tags
    DANGEROUS_TAGS = [
        "script", "iframe", "object", "embed", "applet",
        "form", "input", "button", "link", "base",
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize a string value."""
        if not value:
            return ""

        # Normalize unicode
        sanitized = unicodedata.normalize("NFKC", value)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Sanitize HTML content by escaping dangerous characters."""
        if not value:
            return ""

        # Escape HTML entities
        sanitized = html.escape(value)

        # Remove dangerous tags
        for tag in cls.DANGEROUS_TAGS:
            pattern = f"<{tag}[^>]*>.*?</{tag}>"
            sanitized = re.compile(pattern, re.IGNORECASE | re.DOTALL).sub("", sanitized)
            # Also remove self-closing tags
            pattern = f"<{tag}[^>]*/>"
            sanitized = re.compile(pattern, re.IGNORECASE).sub("", sanitized)

        return sanitized

    @classmethod
    def sanitize_room_id(cls, room_id: str) -> str:
        """Sanitize room ID - alphanumeric with hyphens only."""
        if not room_id:
            return ""

        # Only allow alphanumeric, hyphens, and underscores
        sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "", room_id)

        # Limit length
        if len(sanitized) > 80:
            sanitized = sanitized[:80]

        return sanitized

    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """Sanitize email address."""
        if not email:
            return ""

        # Basic email validation
        email = email.strip().lower()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(pattern, email):
            raise ValueError("Invalid email format")

        return email[:254]  # Max email length

    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check if string contains SQL injection patterns."""
        if not value:
            return False

        value_upper = value.upper()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:50]}")
                return True
        return False

    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check if string contains XSS patterns."""
        if not value:
            return False

        xss_patterns = [
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onclick=",
            r"onload=",
            r"<iframe",
            r"eval\(",
            r"expression\(",
        ]

        value_lower = value.lower()
        for pattern in xss_patterns:
            if re.search(pattern, value_lower):
                logger.warning(f"Potential XSS detected: {value[:50]}")
                return True
        return False


class URLValidator:
    """Validate and check URL safety."""

    # Blocked schemes that could be dangerous
    BLOCKED_SCHEMES = ["javascript", "data", "vbscript"]

    # Blocked hosts (internal/private networks)
    BLOCKED_HOSTS = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
    ]

    @classmethod
    def is_safe_url(cls, url: str, allowed_hosts: Optional[list] = None) -> bool:
        """Check if URL is safe (not malicious)."""
        if not url:
            return False

        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme.lower() in cls.BLOCKED_SCHEMES:
                logger.warning(f"Blocked dangerous URL scheme: {parsed.scheme}")
                return False

            # Check host
            if parsed.hostname:
                hostname = parsed.hostname.lower()

                # Check blocked hosts
                if hostname in cls.BLOCKED_HOSTS:
                    logger.warning(f"Blocked internal URL: {hostname}")
                    return False

                # Check private IP ranges
                if hostname.startswith(("10.", "192.168.", "172.16.", "172.31.")):
                    logger.warning(f"Blocked private IP URL: {hostname}")
                    return False

                # Check allowed hosts if specified
                if allowed_hosts and hostname not in allowed_hosts:
                    return False

            return True

        except Exception as e:
            logger.warning(f"URL validation error: {e}")
            return False

    @classmethod
    def is_safe_redirect(cls, url: str, allowed_hosts: list) -> bool:
        """Check if redirect URL is safe."""
        return cls.is_safe_url(url, allowed_hosts)


class PathSanitizer:
    """Sanitize file paths to prevent directory traversal."""

    @classmethod
    def sanitize_path(cls, path: str, base_path: str = "") -> str:
        """Sanitize a file path."""
        if not path:
            return ""

        # Remove null bytes
        path = path.replace("\x00", "")

        # Remove directory traversal attempts
        path = path.replace("..", "")

        # Remove leading slashes (prevent absolute path injection)
        if not base_path:
            path = path.lstrip("/")

        # Normalize path separators
        path = path.replace("\\", "/")

        return path

    @classmethod
    def is_safe_filename(cls, filename: str) -> bool:
        """Check if filename is safe."""
        if not filename:
            return False

        # Check for path traversal
        if ".." in filename or filename.startswith("/"):
            return False

        # Check for dangerous characters
        dangerous_chars = ["\x00", "\n", "\r"]
        for char in dangerous_chars:
            if char in filename:
                return False

        # Block dangerous extensions
        dangerous_extensions = [".exe", ".bat", ".cmd", ".sh", ".ps1", ".jar"]
        for ext in dangerous_extensions:
            if filename.lower().endswith(ext):
                return False

        return True


class RateLimitKey:
    """Generate secure rate limit keys."""

    @classmethod
    def from_request(cls, request, user_id: Optional[str] = None) -> str:
        """Generate rate limit key from request."""
        # Prefer user ID if authenticated
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    import secrets
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging/masking."""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive values for logging."""
    if not value:
        return ""

    if len(value) <= visible_chars:
        return "*" * len(value)

    return value[:visible_chars] + "*" * (len(value) - visible_chars)