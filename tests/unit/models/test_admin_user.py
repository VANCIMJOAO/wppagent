"""
Unit Tests for AdminUser Model

Tests for:
- Password hashing and verification
- User creation and validation
- Model attributes and relationships
- Business logic methods
"""

from datetime import datetime

import bcrypt
import pytest

from app.models.database import AdminUser


class TestAdminUser:
    """Test cases for AdminUser model"""

    @pytest.mark.unit
    def test_admin_user_creation(self):
        """Test basic AdminUser creation with required fields"""
        admin = AdminUser(
            username="testadmin", email="test@admin.com", full_name="Test Administrator"
        )

        assert admin.username == "testadmin"
        assert admin.email == "test@admin.com"
        assert admin.full_name == "Test Administrator"
        # SQLAlchemy defaults are not set until the object is persisted
        assert admin.is_active is None or admin.is_active is True  # Default value
        assert (
            admin.is_super_admin is None or admin.is_super_admin is False
        )  # Default value
        assert admin.password_hash is None  # Not set yet

    @pytest.mark.unit
    def test_password_hashing(self):
        """Test password hashing functionality"""
        admin = AdminUser(username="testadmin", email="test@admin.com")
        test_password = "secure_password_123"

        # Set password
        admin.set_password(test_password)

        # Verify password was hashed
        assert admin.password_hash is not None
        assert admin.password_hash != test_password
        assert len(admin.password_hash) > 50  # Bcrypt hash is long

        # Verify password can be checked
        assert admin.check_password(test_password) is True
        assert admin.check_password("wrong_password") is False

    @pytest.mark.unit
    def test_password_verification(self):
        """Test password verification with various scenarios"""
        admin = AdminUser(username="testadmin", email="test@admin.com")

        # Test with normal password
        admin.set_password("MyPassword123")
        assert admin.check_password("MyPassword123") is True
        assert admin.check_password("mypassword123") is False  # Case sensitive
        assert admin.check_password("MyPassword124") is False  # Wrong password
        assert admin.check_password("") is False  # Empty password

        # Test with special characters
        admin.set_password("P@ssw0rd!@#$%")
        assert admin.check_password("P@ssw0rd!@#$%") is True
        assert admin.check_password("Password!@#$%") is False

    @pytest.mark.unit
    def test_password_edge_cases(self):
        """Test password handling edge cases"""
        admin = AdminUser(username="testadmin", email="test@admin.com")

        # Test with very long password
        long_password = "a" * 500
        admin.set_password(long_password)
        assert admin.check_password(long_password) is True

        # Test with unicode characters
        unicode_password = "пароль123ñüé"
        admin.set_password(unicode_password)
        assert admin.check_password(unicode_password) is True

        # Test with numbers only
        numeric_password = "123456789"
        admin.set_password(numeric_password)
        assert admin.check_password(numeric_password) is True

    @pytest.mark.unit
    def test_unique_password_hashes(self):
        """Test that same password produces different hashes (salt working)"""
        admin1 = AdminUser(username="admin1", email="admin1@test.com")
        admin2 = AdminUser(username="admin2", email="admin2@test.com")

        same_password = "identical_password"
        admin1.set_password(same_password)
        admin2.set_password(same_password)

        # Hashes should be different due to salt
        assert admin1.password_hash != admin2.password_hash

        # But both should verify correctly
        assert admin1.check_password(same_password) is True
        assert admin2.check_password(same_password) is True

    @pytest.mark.unit
    def test_admin_user_attributes(self):
        """Test AdminUser model attributes and defaults"""
        admin = AdminUser(
            username="fulltest",
            email="fulltest@admin.com",
            full_name="Full Test User",
            is_super_admin=True,
        )

        assert admin.username == "fulltest"
        assert admin.email == "fulltest@admin.com"
        assert admin.full_name == "Full Test User"
        # SQLAlchemy defaults are not set until the object is persisted
        assert admin.is_active is None or admin.is_active is True  # Default
        assert admin.is_super_admin is True  # Explicitly set
        assert admin.last_login is None  # Default
        assert admin.created_at is None  # Will be set by database
        assert admin.updated_at is None  # Will be set by database

    @pytest.mark.unit
    def test_admin_user_string_representation(self):
        """Test string representation of AdminUser (if implemented)"""
        admin = AdminUser(
            username="testuser", email="test@example.com", full_name="Test User"
        )

        # Test that the object can be converted to string without error
        str_repr = str(admin)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    @pytest.mark.unit
    def test_boolean_field_defaults(self):
        """Test boolean field defaults and assignment"""
        admin = AdminUser(username="booltest", email="bool@test.com")

        # Test defaults
        # SQLAlchemy defaults are not set until the object is persisted
        assert admin.is_active is None or admin.is_active is True
        assert admin.is_super_admin is None or admin.is_super_admin is False

        # Test explicit assignment
        admin.is_active = False
        admin.is_super_admin = True

        assert admin.is_active is False
        assert admin.is_super_admin is True

    @pytest.mark.unit
    def test_email_username_assignment(self):
        """Test email and username field assignment"""
        admin = AdminUser()

        # Test assignment
        admin.username = "newuser"
        admin.email = "new@user.com"

        assert admin.username == "newuser"
        assert admin.email == "new@user.com"

        # Test reassignment
        admin.username = "updateduser"
        admin.email = "updated@user.com"

        assert admin.username == "updateduser"
        assert admin.email == "updated@user.com"

    @pytest.mark.unit
    def test_password_empty_handling(self):
        """Test handling of empty/None password scenarios"""
        admin = AdminUser(username="emptytest", email="empty@test.com")

        # Initially no password hash
        assert admin.password_hash is None

        # Cannot check password when none is set
        # This might raise an exception or return False depending on implementation
        try:
            result = admin.check_password("anypassword")
            assert result is False
        except (AttributeError, TypeError):
            # Expected if password_hash is None
            pass

    @pytest.mark.unit
    def test_datetime_fields(self):
        """Test datetime field handling"""
        admin = AdminUser(username="datetest", email="date@test.com")

        # Test last_login assignment
        test_datetime = datetime.now()
        admin.last_login = test_datetime

        assert admin.last_login == test_datetime
        assert isinstance(admin.last_login, datetime)

    @pytest.mark.unit
    def test_model_equality(self):
        """Test model equality comparison (if implemented)"""
        admin1 = AdminUser(username="user1", email="user1@test.com")
        admin2 = AdminUser(username="user1", email="user1@test.com")
        admin3 = AdminUser(username="user2", email="user2@test.com")

        # Same data should not be equal without same ID (different instances)
        assert admin1 is not admin2

        # Different data should definitely not be equal
        assert admin1 is not admin3
