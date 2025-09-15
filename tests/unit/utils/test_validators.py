"""
Unit Tests for Validators

Tests for:
- Email validation
- Phone number validation
- Data validation patterns
- Input sanitization
- Error handling
"""

import re

import pytest

from app.utils.validators import RobustValidator, ValidationError


class TestRobustValidator:
    """Test cases for RobustValidator utility"""

    @pytest.mark.unit
    def test_validator_initialization(self):
        """Test RobustValidator initialization and patterns"""
        validator = RobustValidator()

        # Check that patterns exist
        assert hasattr(validator, "PATTERNS")
        assert isinstance(validator.PATTERNS, dict)

        # Check required patterns exist
        required_patterns = [
            "email",
            "name",
            "username",
            "password",
            "url",
            "token",
            "conversation_id",
            "message_id",
            "user_id",
        ]

        for pattern in required_patterns:
            assert pattern in validator.PATTERNS
            assert isinstance(validator.PATTERNS[pattern], str)

    @pytest.mark.unit
    def test_validator_limits(self):
        """Test validator limits configuration"""
        validator = RobustValidator()

        # Check that limits exist
        assert hasattr(validator, "LIMITS")
        assert isinstance(validator.LIMITS, dict)

        # Check required limits exist
        required_limits = [
            "name_min",
            "name_max",
            "message_max",
            "notes_max",
            "price_min",
            "price_max",
            "duration_min",
            "duration_max",
        ]

        for limit in required_limits:
            assert limit in validator.LIMITS
            assert isinstance(validator.LIMITS[limit], (int, float))

    @pytest.mark.unit
    def test_email_pattern_validation(self):
        """Test email pattern validation"""
        validator = RobustValidator()
        email_pattern = validator.PATTERNS["email"]

        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "test123@test-domain.com",
            "valid_email@123domain.br",
        ]

        for email in valid_emails:
            assert re.match(email_pattern, email), f"Valid email failed: {email}"

        # Invalid emails
        invalid_emails = ["invalid-email", "@example.com", "test@", "test@example", ""]

        for email in invalid_emails:
            assert not re.match(email_pattern, email), f"Invalid email passed: {email}"

    @pytest.mark.unit
    def test_name_pattern_validation(self):
        """Test name pattern validation"""
        validator = RobustValidator()
        name_pattern = validator.PATTERNS["name"]

        # Valid names
        valid_names = [
            "João Silva",
            "Maria Santos",
            "José",
            "Ana Maria",
            "João José da Silva",
            "María José",  # Accented characters
            "André",
            "Luís Carlos",
        ]

        for name in valid_names:
            assert re.match(name_pattern, name), f"Valid name failed: {name}"

        # Invalid names
        invalid_names = [
            "J",  # Too short
            "123João",  # Numbers
            "João@Silva",  # Special characters
            "",  # Empty
            "A" * 101,  # Too long
        ]

        for name in invalid_names:
            assert not re.match(name_pattern, name), f"Invalid name passed: {name}"

    @pytest.mark.unit
    def test_username_pattern_validation(self):
        """Test username pattern validation"""
        validator = RobustValidator()
        username_pattern = validator.PATTERNS["username"]

        # Valid usernames
        valid_usernames = [
            "user123",
            "admin_user",
            "test_123",
            "username",
            "user_name_123",
        ]

        for username in valid_usernames:
            assert re.match(
                username_pattern, username
            ), f"Valid username failed: {username}"

        # Invalid usernames
        invalid_usernames = [
            "us",  # Too short
            "user-name",  # Hyphen not allowed
            "user@name",  # @ not allowed
            "user name",  # Space not allowed
            "",  # Empty
            "a" * 31,  # Too long
        ]

        for username in invalid_usernames:
            assert not re.match(
                username_pattern, username
            ), f"Invalid username passed: {username}"

    @pytest.mark.unit
    def test_password_pattern_validation(self):
        """Test password pattern validation"""
        validator = RobustValidator()
        password_pattern = validator.PATTERNS["password"]

        # Valid passwords (must have uppercase, lowercase, digit, min 8 chars)
        valid_passwords = [
            "Password123",
            "SecurePass1",
            "MyPassword2024",
            "Test123456",
            "Admin@123",
        ]

        for password in valid_passwords:
            assert re.match(
                password_pattern, password
            ), f"Valid password failed: {password}"

        # Invalid passwords
        invalid_passwords = [
            "password",  # No uppercase or digit
            "PASSWORD",  # No lowercase or digit
            "Password",  # No digit
            "Pass123",  # Too short
            "12345678",  # No letters
            "",  # Empty
        ]

        for password in invalid_passwords:
            assert not re.match(
                password_pattern, password
            ), f"Invalid password passed: {password}"

    @pytest.mark.unit
    def test_url_pattern_validation(self):
        """Test URL pattern validation"""
        validator = RobustValidator()
        url_pattern = validator.PATTERNS["url"]

        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://test.com",
            "https://www.example.com",
            "https://api.example.com/v1/endpoint",
            "https://sub.domain.example.com",
        ]

        for url in valid_urls:
            assert re.match(url_pattern, url), f"Valid URL failed: {url}"

        # Invalid URLs
        invalid_urls = [
            "ftp://example.com",  # Wrong protocol
            "example.com",  # No protocol
            "https://",  # Incomplete
            "",  # Empty
            "not-a-url",  # Not a URL
        ]

        for url in invalid_urls:
            assert not re.match(url_pattern, url), f"Invalid URL passed: {url}"

    @pytest.mark.unit
    def test_id_pattern_validation(self):
        """Test ID pattern validation for various entity types"""
        validator = RobustValidator()

        id_patterns = [
            "conversation_id",
            "message_id",
            "user_id",
            "appointment_id",
            "service_id",
        ]

        # Valid IDs (numeric strings)
        valid_ids = ["1", "123", "999999", "1234567890"]

        # Invalid IDs
        invalid_ids = ["", "abc", "12abc", "-123", "12.34", " 123 "]

        for pattern_name in id_patterns:
            pattern = validator.PATTERNS[pattern_name]

            for valid_id in valid_ids:
                assert re.match(
                    pattern, valid_id
                ), f"Valid {pattern_name} failed: {valid_id}"

            for invalid_id in invalid_ids:
                assert not re.match(
                    pattern, invalid_id
                ), f"Invalid {pattern_name} passed: {invalid_id}"

    @pytest.mark.unit
    def test_token_pattern_validation(self):
        """Test token pattern validation"""
        validator = RobustValidator()
        token_pattern = validator.PATTERNS["token"]

        # Valid tokens
        valid_tokens = [
            "abcd123456",
            "token_123456",
            "ABC-123-DEF",
            "very_long_token_with_numbers_123456789",
            "EAABwzLixnjYBO1234567890",  # Facebook-style token
        ]

        for token in valid_tokens:
            assert re.match(token_pattern, token), f"Valid token failed: {token}"

        # Invalid tokens
        invalid_tokens = [
            "short",  # Too short
            "token@123",  # Invalid character
            "token 123",  # Space
            "",  # Empty
            "tok",  # Too short
        ]

        for token in invalid_tokens:
            assert not re.match(token_pattern, token), f"Invalid token passed: {token}"

    @pytest.mark.unit
    def test_limits_validation(self):
        """Test validator limits are reasonable"""
        validator = RobustValidator()
        limits = validator.LIMITS

        # Check name limits
        assert limits["name_min"] > 0
        assert limits["name_max"] > limits["name_min"]
        assert limits["name_min"] >= 2
        assert limits["name_max"] <= 255

        # Check message limits
        assert limits["message_max"] > 0
        assert limits["message_max"] >= 1000  # Should support reasonable messages

        # Check price limits
        assert limits["price_min"] >= 0
        assert limits["price_max"] > limits["price_min"]

        # Check duration limits
        assert limits["duration_min"] > 0
        assert limits["duration_max"] > limits["duration_min"]
        assert limits["duration_max"] <= 1440  # Max 24 hours

    @pytest.mark.unit
    def test_pattern_compilation(self):
        """Test that all regex patterns compile without errors"""
        validator = RobustValidator()

        for pattern_name, pattern in validator.PATTERNS.items():
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Pattern {pattern_name} failed to compile: {e}")

    @pytest.mark.unit
    def test_validation_error_class(self):
        """Test ValidationError exception class"""
        # Test that ValidationError can be raised and caught
        with pytest.raises(ValidationError):
            raise ValidationError("Test validation error")

        # Test with custom message
        error_message = "Custom validation error message"
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(error_message)

        assert str(exc_info.value) == error_message
        assert isinstance(exc_info.value, Exception)

    @pytest.mark.unit
    def test_patterns_coverage(self):
        """Test that patterns cover all necessary validation cases"""
        validator = RobustValidator()

        # Ensure all critical patterns are present
        critical_patterns = [
            "email",  # User communication
            "name",  # User identification
            "username",  # Admin accounts
            "password",  # Security
            "url",  # API endpoints
            "user_id",  # Database references
        ]

        for pattern in critical_patterns:
            assert pattern in validator.PATTERNS, f"Critical pattern {pattern} missing"
            assert len(validator.PATTERNS[pattern]) > 0, f"Pattern {pattern} is empty"
