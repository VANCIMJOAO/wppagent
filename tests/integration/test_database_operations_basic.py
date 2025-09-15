"""
Basic Database Integration Tests - Fixed for pytest-asyncio compatibility.
Simplified fixtures and test structure to avoid framework conflicts.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
# Database imports
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import AsyncSessionLocal, engine
from app.models.database import (AdminUser, Appointment, Business, CompanyInfo,
                                 Conversation, Message, Service, User)

# Test timeout protection
pytestmark = pytest.mark.timeout(180)


class TestDatabaseConnectionBasic:
    """Basic database connection tests without async fixtures."""

    @pytest.mark.asyncio
    async def test_database_connection_async(self):
        """Test basic database connection asynchronously."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")


class TestModelCreationBasic:
    """Test model creation without complex async fixtures."""

    def test_user_model_creation(self):
        """Test creating a User model instance"""
        unique_suffix = str(uuid.uuid4())[:8]

        user = User(
            nome=f"João da Silva {unique_suffix}",
            telefone=f"+551199999{random.randint(1000, 9999)}",
            wa_id=f"5511999999999{unique_suffix[:4]}",
        )

        assert user.nome == f"João da Silva {unique_suffix}"
        assert user.telefone.startswith("+5511")
        assert user.wa_id.startswith("5511")

    def test_appointment_model_creation(self):
        """Test creating an Appointment model instance"""
        unique_suffix = str(uuid.uuid4())[:8]

        appointment = Appointment(
            user_id=1,
            business_id=1,
            service_id=1,
            date_time=datetime.utcnow() + timedelta(days=1),
            duration_minutes=60,
            status="agendado",
            notes=f"Test appointment {unique_suffix}",
        )

        assert appointment.user_id == 1
        assert appointment.business_id == 1
        assert appointment.service_id == 1
        assert appointment.duration_minutes == 60
        assert appointment.status == "agendado"
        assert appointment.notes == f"Test appointment {unique_suffix}"

    def test_business_model_creation(self):
        """Test creating a Business model instance"""
        unique_suffix = str(uuid.uuid4())[:8]

        business = Business(
            name=f"Business Test {unique_suffix}",
            phone=f"+551199999{random.randint(1000, 9999)}",
            email=f"business{unique_suffix}@test.com",
            address=f"Test Address {unique_suffix}",
        )

        assert business.name == f"Business Test {unique_suffix}"
        assert business.phone.startswith("+5511")
        assert business.email == f"business{unique_suffix}@test.com"
        assert business.address == f"Test Address {unique_suffix}"


class TestDatabaseOperationsBasic:
    """Test database operations with simplified async handling."""

    @pytest.mark.asyncio
    async def test_user_crud_operations(self):
        """Test User CRUD operations"""
        unique_suffix = str(uuid.uuid4())[:8]

        async with AsyncSessionLocal() as session:
            # Create
            user = User(
                nome=f"Test User {unique_suffix}",
                telefone=f"+551199999{random.randint(1000, 9999)}",
                wa_id=f"5511999999999{unique_suffix[:4]}",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Read
            found_user = await session.get(User, user.id)
            assert found_user is not None
            assert found_user.nome == f"Test User {unique_suffix}"

            # Update
            found_user.nome = f"Updated User {unique_suffix}"
            await session.commit()
            await session.refresh(found_user)
            assert found_user.nome == f"Updated User {unique_suffix}"

            # Delete
            await session.delete(found_user)
            await session.commit()

            # Verify deletion
            deleted_user = await session.get(User, user.id)
            assert deleted_user is None

    @pytest.mark.asyncio
    async def test_appointment_crud_operations(self):
        """Test Appointment CRUD operations"""
        unique_suffix = str(uuid.uuid4())[:8]

        async with AsyncSessionLocal() as session:
            # First create a user and business for the appointment
            user = User(
                nome=f"Appointment User {unique_suffix}",
                telefone=f"+551199999{random.randint(1000, 9999)}",
                wa_id=f"5511999999999{unique_suffix[:4]}",
            )
            session.add(user)

            business = Business(
                name=f"Test Business {unique_suffix}",
                phone=f"+551199999{random.randint(1000, 9999)}",
                email=f"business{unique_suffix}@test.com",
            )
            session.add(business)

            await session.commit()
            await session.refresh(user)
            await session.refresh(business)

            service = Service(
                business_id=business.id,  # Add required business_id
                name=f"Test Service {unique_suffix}",
                duration_minutes=60,
                price=100.00,  # Use Decimal/float format for numeric database field
            )
            session.add(service)
            await session.commit()
            await session.refresh(service)

            # Create appointment
            appointment = Appointment(
                user_id=user.id,
                business_id=business.id,
                service_id=service.id,
                date_time=datetime.utcnow() + timedelta(days=1),
                duration_minutes=60,
                status="agendado",
                notes=f"Test appointment {unique_suffix}",
            )
            session.add(appointment)
            await session.commit()
            await session.refresh(appointment)

            # Read
            found_appointment = await session.get(Appointment, appointment.id)
            assert found_appointment is not None
            assert found_appointment.status == "agendado"

            # Update
            found_appointment.status = "confirmado"
            await session.commit()
            await session.refresh(found_appointment)
            assert found_appointment.status == "confirmado"

            # Delete (cleanup)
            await session.delete(found_appointment)
            await session.delete(user)
            await session.delete(business)
            await session.delete(service)
            await session.commit()

    @pytest.mark.asyncio
    async def test_unique_constraint_handling(self):
        """Test handling of unique constraint violations"""
        unique_suffix = str(uuid.uuid4())[:8]
        wa_id = f"5511999999999{unique_suffix[:4]}"

        async with AsyncSessionLocal() as session:
            # Create first user
            user1 = User(
                nome=f"User One {unique_suffix}",
                telefone=f"+551199999{random.randint(1000, 9999)}",
                wa_id=wa_id,
            )
            session.add(user1)
            await session.commit()

            try:
                # Try to create second user with same wa_id
                user2 = User(
                    nome=f"User Two {unique_suffix}",
                    telefone=f"+551199999{random.randint(1000, 9999)}",
                    wa_id=wa_id,  # Duplicate wa_id
                )
                session.add(user2)
                await session.commit()

                # Should not reach here
                pytest.fail("Expected IntegrityError for duplicate wa_id")

            except IntegrityError:
                # Expected behavior
                await session.rollback()

            # Cleanup
            await session.delete(user1)
            await session.commit()


class TestTransactionHandlingBasic:
    """Test transaction handling without complex fixtures."""

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        unique_suffix = str(uuid.uuid4())[:8]

        async with AsyncSessionLocal() as session:
            try:
                # Create user
                user = User(
                    nome=f"Transaction User {unique_suffix}",
                    telefone=f"+551199999{random.randint(1000, 9999)}",
                    wa_id=f"5511999999999{unique_suffix[:4]}",
                )
                session.add(user)

                # Force an error (intentionally cause constraint violation)
                user2 = User(
                    nome=f"Duplicate User {unique_suffix}",
                    telefone=f"+551199999{random.randint(1000, 9999)}",
                    wa_id=user.wa_id,  # Same wa_id
                )
                session.add(user2)

                # This should fail
                await session.commit()

            except IntegrityError:
                # Expected error - rollback
                await session.rollback()

                # Verify no users were created
                result = await session.execute(
                    text("SELECT COUNT(*) FROM users WHERE wa_id = :wa_id"),
                    {"wa_id": user.wa_id},
                )
                count = result.scalar()
                assert count == 0

    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """Test successful transaction commit"""
        unique_suffix = str(uuid.uuid4())[:8]

        async with AsyncSessionLocal() as session:
            # Create user
            user = User(
                nome=f"Commit User {unique_suffix}",
                telefone=f"+551199999{random.randint(1000, 9999)}",
                wa_id=f"5511999999999{unique_suffix[:4]}",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Verify user exists
            found_user = await session.get(User, user.id)
            assert found_user is not None
            assert found_user.nome == f"Commit User {unique_suffix}"

            # Cleanup
            await session.delete(found_user)
            await session.commit()
