import pytest
from app.core.security import (
    InputSanitizer,
    URLValidator,
    PathSanitizer,
    generate_secure_token,
    hash_sensitive_data,
    mask_sensitive,
)


class TestInputSanitizer:
    """Tests for input sanitization"""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        result = InputSanitizer.sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_sanitize_string_removes_null_bytes(self):
        """Test null byte removal"""
        result = InputSanitizer.sanitize_string("test\x00value")
        assert "\x00" not in result

    def test_sanitize_string_max_length(self):
        """Test max length enforcement"""
        long_string = "a" * 2000
        result = InputSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_sanitize_html_escapes_tags(self):
        """Test HTML escaping"""
        result = InputSanitizer.sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_html_removes_dangerous_tags(self):
        """Test dangerous tag removal"""
        result = InputSanitizer.sanitize_html("<iframe src='evil'></iframe><script>evil</script>")
        assert "<iframe" not in result
        assert "<script>" not in result

    def test_sanitize_room_id_allows_valid(self):
        """Test valid room IDs"""
        assert InputSanitizer.sanitize_room_id("room-123") == "room-123"
        assert InputSanitizer.sanitize_room_id("test_room_456") == "test_room_456"

    def test_sanitize_room_id_blocks_invalid(self):
        """Test invalid room ID sanitization"""
        result = InputSanitizer.sanitize_room_id("room; DROP TABLE--")
        assert ";" not in result
        # Special characters are removed, but remaining letters stay

    def test_check_sql_injection_detects_sql(self):
        """Test SQL injection detection"""
        assert InputSanitizer.check_sql_injection("'; DROP TABLE users;--") is True
        assert InputSanitizer.check_sql_injection("UNION SELECT * FROM passwords") is True

    def test_check_sql_injection_allows_normal(self):
        """Test normal input passes"""
        assert InputSanitizer.check_sql_injection("Hello world") is False
        assert InputSanitizer.check_sql_injection("I'm looking for the meeting") is False

    def test_check_xss_detects_xss(self):
        """Test XSS detection"""
        assert InputSanitizer.check_xss("<script>alert(1)</script>") is True
        assert InputSanitizer.check_xss("javascript:alert(1)") is True
        assert InputSanitizer.check_xss("<img onerror=alert(1) src=x>") is True

    def test_check_xss_allows_normal(self):
        """Test normal input passes XSS check"""
        assert InputSanitizer.check_xss("Hello <world>") is False
        assert InputSanitizer.check_xss("Meeting notes") is False


class TestURLValidator:
    """Tests for URL validation"""

    def test_is_safe_url_allows_https(self):
        """Test HTTPS URLs are allowed"""
        assert URLValidator.is_safe_url("https://example.com/page") is True
        assert URLValidator.is_safe_url("https://api.github.com") is True

    def test_is_safe_url_blocks_javascript(self):
        """Test javascript: URLs are blocked"""
        assert URLValidator.is_safe_url("javascript:alert(1)") is False

    def test_is_safe_url_blocks_localhost(self):
        """Test localhost is blocked"""
        assert URLValidator.is_safe_url("http://localhost:3000") is False
        assert URLValidator.is_safe_url("http://127.0.0.1:8080") is False

    def test_is_safe_url_blocks_private_ips(self):
        """Test private IP ranges are blocked"""
        assert URLValidator.is_safe_url("http://10.0.0.1/admin") is False
        assert URLValidator.is_safe_url("http://192.168.1.1/secret") is False
        assert URLValidator.is_safe_url("http://172.16.0.1/api") is False

    def test_is_safe_url_respects_allowed_hosts(self):
        """Test allowed_hosts parameter works"""
        assert URLValidator.is_safe_url("https://trusted.com", allowed_hosts=["trusted.com"]) is True
        assert URLValidator.is_safe_url("https://evil.com", allowed_hosts=["trusted.com"]) is False


class TestPathSanitizer:
    """Tests for path sanitization"""

    def test_sanitize_path_removes_traversal(self):
        """Test directory traversal removal"""
        # Traversal patterns are removed, but path structure may remain
        result1 = PathSanitizer.sanitize_path("../../etc/passwd")
        assert ".." not in result1  # No traversal patterns
        assert "etc" in result1  # Path preserved

        result2 = PathSanitizer.sanitize_path("../../../bin/sh")
        assert ".." not in result2
        assert "bin" in result2

    def test_sanitize_path_removes_null_bytes(self):
        """Test null byte removal"""
        result = PathSanitizer.sanitize_path("file\x00.txt")
        assert "\x00" not in result

    def test_sanitize_path_normalizes_separators(self):
        """Test path separator normalization"""
        result = PathSanitizer.sanitize_path("path/to\\file")
        assert "\\" not in result

    def test_is_safe_filename_allows_valid(self):
        """Test valid filenames"""
        assert PathSanitizer.is_safe_filename("document.pdf") is True
        assert PathSanitizer.is_safe_filename("meeting-notes.txt") is True
        assert PathSanitizer.is_safe_filename("report_v1.docx") is True

    def test_is_safe_filename_blocks_dangerous(self):
        """Test dangerous extensions blocked"""
        assert PathSanitizer.is_safe_filename("malware.exe") is False
        assert PathSanitizer.is_safe_filename("script.bat") is False
        assert PathSanitizer.is_safe_filename("hack.sh") is False

    def test_is_safe_filename_blocks_traversal(self):
        """Test path traversal blocked"""
        assert PathSanitizer.is_safe_filename("../etc/passwd") is False
        assert PathSanitizer.is_safe_filename("/etc/passwd") is False


class TestSecurityUtilities:
    """Tests for security utility functions"""

    def test_generate_secure_token_unique(self):
        """Test tokens are unique"""
        tokens = [generate_secure_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_generate_secure_token_length(self):
        """Test token has expected length"""
        token = generate_secure_token(32)
        assert len(token) > 30

    def test_hash_sensitive_data_consistent(self):
        """Test hashing is consistent"""
        result1 = hash_sensitive_data("secret")
        result2 = hash_sensitive_data("secret")
        assert result1 == result2

    def test_hash_sensitive_data_different_for_different_inputs(self):
        """Test different inputs produce different hashes"""
        assert hash_sensitive_data("secret1") != hash_sensitive_data("secret2")

    def test_mask_sensitive_short_value(self):
        """Test short values are fully masked"""
        result = mask_sensitive("abc")
        assert result == "***"

    def test_mask_sensitive_long_value(self):
        """Test long values show visible portion"""
        result = mask_sensitive("longpassword123", visible_chars=4)
        assert result.startswith("long")
        assert "*" in result
        assert len(result) == len("longpassword123")

    def test_mask_sensitive_empty_value(self):
        """Test empty value handling"""
        assert mask_sensitive("") == ""


class TestSecurityHeaders:
    """Tests for security headers configuration"""

    def test_security_headers_exist(self):
        """Test security headers are defined"""
        from app.core.middleware import SECURITY_HEADERS
        assert "X-Content-Type-Options" in SECURITY_HEADERS
        assert "X-Frame-Options" in SECURITY_HEADERS
        assert "X-XSS-Protection" in SECURITY_HEADERS

    def test_security_headers_correct_values(self):
        """Test security header values are correct"""
        from app.core.middleware import SECURITY_HEADERS
        assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
        assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
        assert SECURITY_HEADERS["Referrer-Policy"] == "strict-origin-when-cross-origin"


class TestAuditLogger:
    """Tests for audit logging"""

    def test_audit_action_enum_values(self):
        """Test audit action enum has expected values"""
        from app.core.audit import AuditAction
        assert "login_success" in [a.value for a in AuditAction]
        assert "data_deleted" in [a.value for a in AuditAction]
        assert "access_denied" in [a.value for a in AuditAction]

    def test_audit_level_enum_values(self):
        """Test audit level enum has expected values"""
        from app.core.audit import AuditLevel
        assert "info" in [l.value for l in AuditLevel]
        assert "warning" in [l.value for l in AuditLevel]
        assert "error" in [l.value for l in AuditLevel]

    def test_audit_logger_can_be_imported(self):
        """Test audit logger can be imported"""
        from app.core.audit import AuditLogger
        assert hasattr(AuditLogger, 'log')
        assert hasattr(AuditLogger, 'log_login_success')
        assert hasattr(AuditLogger, 'log_data_deleted')