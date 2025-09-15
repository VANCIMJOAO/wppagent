"""
Unit Tests for User Model

Tests for:
- User creation and validation
- WhatsApp ID handling
- User data management
- Model relationships
"""

from datetime import datetime

import pytest

from app.models.database import User


class TestUser:
    """Test cases for User model"""

    @pytest.mark.unit
    def test_user_creation(self):
        """Test basic User creation with required fields"""
        user = User(
            wa_id="5511999888777",
            nome="João Silva",
            telefone="+55 11 99988-8777",
            email="joao@example.com",
        )

        assert user.wa_id == "5511999888777"
        assert user.nome == "João Silva"
        assert user.telefone == "+55 11 99988-8777"
        assert user.email == "joao@example.com"
        assert user.created_at is None  # Will be set by database
        assert user.updated_at is None  # Will be set by database

    @pytest.mark.unit
    def test_user_minimal_creation(self):
        """Test User creation with only required field (wa_id)"""
        user = User(wa_id="5511987654321")

        assert user.wa_id == "5511987654321"
        assert user.nome is None
        assert user.telefone is None
        assert user.email is None

    @pytest.mark.unit
    def test_wa_id_variations(self):
        """Test different WhatsApp ID formats"""
        # Standard Brazilian format
        user1 = User(wa_id="5511999887766")
        assert user1.wa_id == "5511999887766"

        # International format
        user2 = User(wa_id="1234567890123")
        assert user2.wa_id == "1234567890123"

        # Short format
        user3 = User(wa_id="123456789")
        assert user3.wa_id == "123456789"

    @pytest.mark.unit
    def test_user_data_assignment(self):
        """Test user data field assignment and updates"""
        user = User(wa_id="5511123456789")

        # Initial assignment
        user.nome = "Maria Santos"
        user.telefone = "+55 11 1234-5678"
        user.email = "maria@test.com"

        assert user.nome == "Maria Santos"
        assert user.telefone == "+55 11 1234-5678"
        assert user.email == "maria@test.com"

        # Update data
        user.nome = "Maria Silva Santos"
        user.email = "maria.silva@test.com"

        assert user.nome == "Maria Silva Santos"
        assert user.email == "maria.silva@test.com"

    @pytest.mark.unit
    def test_user_string_representation(self):
        """Test User string representation"""
        user = User(wa_id="5511999888777", nome="Test User")

        str_repr = str(user)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    @pytest.mark.unit
    def test_user_email_validation_format(self):
        """Test email format handling (basic validation)"""
        user = User(wa_id="5511123456789")

        # Valid email formats
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numeric-domain.com",
        ]

        for email in valid_emails:
            user.email = email
            assert user.email == email

    @pytest.mark.unit
    def test_user_phone_formats(self):
        """Test different phone format handling"""
        user = User(wa_id="5511123456789")

        # Different phone formats
        phone_formats = [
            "+55 11 99999-8888",
            "5511999998888",
            "+551199999-8888",
            "(11) 99999-8888",
            "11 999998888",
        ]

        for phone in phone_formats:
            user.telefone = phone
            assert user.telefone == phone

    @pytest.mark.unit
    def test_user_name_handling(self):
        """Test name field handling with various formats"""
        user = User(wa_id="5511123456789")

        # Different name formats
        names = [
            "João",
            "Maria Silva",
            "José de Souza Santos",
            "Ana-Maria",
            "João O'Connor",
            "李小明",  # Chinese characters
            "José María Aznar",  # Accented characters
        ]

        for name in names:
            user.nome = name
            assert user.nome == name

    @pytest.mark.unit
    def test_user_empty_fields(self):
        """Test handling of empty string fields"""
        user = User(wa_id="5511123456789")

        # Test empty strings
        user.nome = ""
        user.telefone = ""
        user.email = ""

        assert user.nome == ""
        assert user.telefone == ""
        assert user.email == ""

        # Test None assignment
        user.nome = None
        user.telefone = None
        user.email = None

        assert user.nome is None
        assert user.telefone is None
        assert user.email is None

    @pytest.mark.unit
    def test_user_field_lengths(self):
        """Test field length handling"""
        user = User(wa_id="5511123456789")

        # Test long name (within reasonable limits)
        long_name = "A" * 250  # Assuming 255 char limit
        user.nome = long_name
        assert user.nome == long_name

        # Test long phone
        long_phone = "+" + "1" * 19  # Assuming 20 char limit
        user.telefone = long_phone
        assert user.telefone == long_phone

        # Test long email (within reasonable limits)
        long_email = "a" * 240 + "@example.com"  # Assuming 255 char limit
        user.email = long_email
        assert user.email == long_email
