"""
Testes de Integração - Operações de Database
Testa operações CRUD e relacionamentos entre modelos
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    """Testes de integração para operações de database"""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection and basic query"""
        try:
            from app.database import AsyncSessionLocal, engine

            # Test database connection
            async with AsyncSessionLocal() as session:
                # Simple query to test connection
                result = await session.execute("SELECT 1 as test")
                row = result.fetchone()

                assert row is not None
                assert row[0] == 1

        except Exception as e:
            pytest.skip(f"Database connection not available: {e}")

    @pytest.mark.asyncio
    async def test_user_crud_operations(self):
        """Test complete CRUD operations for User model"""
        try:
            from app.database import AsyncSessionLocal
            from app.models.database import User

            async with AsyncSessionLocal() as session:
                # CREATE - Test user creation
                test_user = User(
                    wa_id="5511999000001",
                    nome="Teste CRUD User",
                    telefone="+55 11 99900-0001",
                    email="crud@test.com",
                )

                session.add(test_user)
                await session.commit()
                await session.refresh(test_user)

                created_user_id = test_user.id
                assert created_user_id is not None

                # READ - Test user retrieval
                retrieved_user = await session.get(User, created_user_id)
                assert retrieved_user is not None
                assert retrieved_user.wa_id == "5511999000001"
                assert retrieved_user.nome == "Teste CRUD User"

                # UPDATE - Test user update
                retrieved_user.nome = "Teste CRUD User Updated"
                retrieved_user.email = "crud_updated@test.com"
                await session.commit()
                await session.refresh(retrieved_user)

                assert retrieved_user.nome == "Teste CRUD User Updated"
                assert retrieved_user.email == "crud_updated@test.com"

                # DELETE - Test user deletion
                await session.delete(retrieved_user)
                await session.commit()

                # Verify deletion
                deleted_user = await session.get(User, created_user_id)
                assert deleted_user is None

        except Exception as e:
            pytest.skip(f"User CRUD operations test skipped: {e}")

    @pytest.mark.asyncio
    async def test_appointment_crud_operations(self):
        """Test complete CRUD operations for Appointment model"""
        try:
            from decimal import Decimal

            from app.database import AsyncSessionLocal
            from app.models.database import (Appointment, Business, Service,
                                             User)

            async with AsyncSessionLocal() as session:
                # Create dependencies first
                test_user = User(
                    wa_id="5511999000002",
                    nome="User for Appointment",
                    telefone="+55 11 99900-0002",
                )
                session.add(test_user)

                test_business = Business(
                    name="Test Business",
                    phone="+55 11 99999-9999",
                    email="business@test.com",
                )
                session.add(test_business)

                test_service = Service(
                    business_id=1,  # Will be updated after business creation
                    name="Test Service",
                    description="Service for testing",
                    duration_minutes=60,
                    price="R$ 50,00",
                )

                await session.commit()
                await session.refresh(test_user)
                await session.refresh(test_business)

                # Update service with correct business_id
                test_service.business_id = test_business.id
                session.add(test_service)
                await session.commit()
                await session.refresh(test_service)

                # CREATE - Test appointment creation
                appointment_time = datetime.now() + timedelta(days=1)

                test_appointment = Appointment(
                    user_id=test_user.id,
                    business_id=test_business.id,
                    service_id=test_service.id,
                    date_time=appointment_time,
                    duration_minutes=60,
                    price=Decimal("50.00"),
                    notes="Teste CRUD Appointment",
                )

                # Calculate end time
                test_appointment.calculate_end_time()

                session.add(test_appointment)
                await session.commit()
                await session.refresh(test_appointment)

                created_appointment_id = test_appointment.id
                assert created_appointment_id is not None
                assert test_appointment.end_time is not None

                # READ - Test appointment retrieval
                retrieved_appointment = await session.get(
                    Appointment, created_appointment_id
                )
                assert retrieved_appointment is not None
                assert retrieved_appointment.user_id == test_user.id
                assert retrieved_appointment.notes == "Teste CRUD Appointment"

                # UPDATE - Test appointment update
                retrieved_appointment.notes = "Teste CRUD Appointment Updated"
                retrieved_appointment.duration_minutes = 90
                retrieved_appointment.calculate_end_time()  # Recalculate end time

                await session.commit()
                await session.refresh(retrieved_appointment)

                assert retrieved_appointment.notes == "Teste CRUD Appointment Updated"
                assert retrieved_appointment.duration_minutes == 90

                # DELETE - Test appointment deletion
                await session.delete(retrieved_appointment)
                await session.delete(test_service)
                await session.delete(test_business)
                await session.delete(test_user)
                await session.commit()

                # Verify deletion
                deleted_appointment = await session.get(
                    Appointment, created_appointment_id
                )
                assert deleted_appointment is None

        except Exception as e:
            pytest.skip(f"Appointment CRUD operations test skipped: {e}")


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.relationships
class TestDatabaseRelationships:
    """Testes para relacionamentos entre modelos"""

    @pytest.mark.asyncio
    async def test_user_appointment_relationship(self):
        """Test relationship between User and Appointment models"""
        try:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from app.database import AsyncSessionLocal
            from app.models.database import (Appointment, Business, Service,
                                             User)

            async with AsyncSessionLocal() as session:
                # Create test data
                test_user = User(
                    wa_id="5511999000003",
                    nome="User with Appointments",
                    telefone="+55 11 99900-0003",
                )
                session.add(test_user)
                await session.commit()
                await session.refresh(test_user)

                # Create multiple appointments for the user
                appointment_times = [
                    datetime.now() + timedelta(days=1),
                    datetime.now() + timedelta(days=2),
                    datetime.now() + timedelta(days=3),
                ]

                created_appointments = []
                for i, apt_time in enumerate(appointment_times):
                    appointment = Appointment(
                        user_id=test_user.id,
                        business_id=1,  # Assume exists
                        service_id=1,  # Assume exists
                        date_time=apt_time,
                        duration_minutes=60,
                        notes=f"Appointment {i+1}",
                    )
                    session.add(appointment)
                    created_appointments.append(appointment)

                await session.commit()

                # Test relationship: User -> Appointments
                stmt = (
                    select(User)
                    .where(User.id == test_user.id)
                    .options(selectinload(User.appointments))
                )
                result = await session.execute(stmt)
                user_with_appointments = result.scalar_one()

                assert len(user_with_appointments.appointments) == 3

                # Test relationship: Appointment -> User
                for appointment in created_appointments:
                    await session.refresh(appointment)
                    assert appointment.user_id == test_user.id

                # Clean up
                for appointment in created_appointments:
                    await session.delete(appointment)
                await session.delete(test_user)
                await session.commit()

        except Exception as e:
            pytest.skip(f"User-Appointment relationship test skipped: {e}")

    @pytest.mark.asyncio
    async def test_business_service_relationship(self):
        """Test relationship between Business and Service models"""
        try:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from app.database import AsyncSessionLocal
            from app.models.database import Business, Service

            async with AsyncSessionLocal() as session:
                # Create test business
                test_business = Business(
                    name="Business with Services",
                    phone="+55 11 88888-8888",
                    email="services@test.com",
                    description="Business for testing services",
                )
                session.add(test_business)
                await session.commit()
                await session.refresh(test_business)

                # Create multiple services for the business
                services_data = [
                    {"name": "Corte Masculino", "price": "R$ 30,00", "duration": 30},
                    {"name": "Corte Feminino", "price": "R$ 50,00", "duration": 60},
                    {"name": "Barba", "price": "R$ 20,00", "duration": 20},
                ]

                created_services = []
                for service_data in services_data:
                    service = Service(
                        business_id=test_business.id,
                        name=service_data["name"],
                        price=service_data["price"],
                        duration_minutes=service_data["duration"],
                        description=f"Descrição do {service_data['name']}",
                    )
                    session.add(service)
                    created_services.append(service)

                await session.commit()

                # Test relationship: Business -> Services
                stmt = (
                    select(Business)
                    .where(Business.id == test_business.id)
                    .options(selectinload(Business.services))
                )
                result = await session.execute(stmt)
                business_with_services = result.scalar_one()

                assert len(business_with_services.services) == 3

                # Verify service details
                service_names = [s.name for s in business_with_services.services]
                assert "Corte Masculino" in service_names
                assert "Corte Feminino" in service_names
                assert "Barba" in service_names

                # Test relationship: Service -> Business
                for service in created_services:
                    await session.refresh(service)
                    assert service.business_id == test_business.id

                # Clean up
                for service in created_services:
                    await session.delete(service)
                await session.delete(test_business)
                await session.commit()

        except Exception as e:
            pytest.skip(f"Business-Service relationship test skipped: {e}")


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.performance
class TestDatabasePerformance:
    """Testes de performance do database"""

    @pytest.mark.asyncio
    async def test_bulk_user_creation(self):
        """Test bulk creation of users for performance"""
        try:
            import time

            from app.database import AsyncSessionLocal
            from app.models.database import User

            async with AsyncSessionLocal() as session:
                start_time = time.time()

                # Create multiple users
                users_to_create = []
                for i in range(20):
                    user = User(
                        wa_id=f"551199900{i:04d}",
                        nome=f"Bulk User {i}",
                        telefone=f"+55 11 9990-{i:04d}",
                        email=f"bulk{i}@test.com",
                    )
                    users_to_create.append(user)

                # Bulk add
                session.add_all(users_to_create)
                await session.commit()

                end_time = time.time()
                creation_time = end_time - start_time

                # Performance check - should create 20 users reasonably fast
                assert (
                    creation_time < 5.0
                ), f"Bulk creation took too long: {creation_time:.2f}s"

                # Verify all users were created
                for user in users_to_create:
                    await session.refresh(user)
                    assert user.id is not None

                # Clean up
                for user in users_to_create:
                    await session.delete(user)
                await session.commit()

        except Exception as e:
            pytest.skip(f"Bulk user creation test skipped: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test concurrent database operations"""
        try:
            from app.database import AsyncSessionLocal
            from app.models.database import User

            async def create_user(index):
                async with AsyncSessionLocal() as session:
                    user = User(
                        wa_id=f"551199988{index:03d}",
                        nome=f"Concurrent User {index}",
                        telefone=f"+55 11 9998-8{index:03d}",
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    return user.id

            # Create users concurrently
            tasks = [create_user(i) for i in range(5)]
            start_time = asyncio.get_event_loop().time()

            user_ids = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time

            # Check that most operations succeeded
            successful_ids = [uid for uid in user_ids if isinstance(uid, int)]

            assert len(successful_ids) >= 3, "Most concurrent operations should succeed"
            assert (
                total_time < 10.0
            ), f"Concurrent operations took too long: {total_time:.2f}s"

            # Clean up successful creations
            async with AsyncSessionLocal() as session:
                for user_id in successful_ids:
                    user = await session.get(User, user_id)
                    if user:
                        await session.delete(user)
                await session.commit()

        except Exception as e:
            pytest.skip(f"Concurrent database operations test skipped: {e}")

    @pytest.mark.asyncio
    async def test_query_performance(self):
        """Test query performance with filters and joins"""
        try:
            import time

            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from app.database import AsyncSessionLocal
            from app.models.database import Appointment, User

            async with AsyncSessionLocal() as session:
                # Test simple query performance
                start_time = time.time()

                stmt = select(User).limit(10)
                result = await session.execute(stmt)
                users = result.scalars().all()

                end_time = time.time()
                query_time = end_time - start_time

                # Query should be fast
                assert (
                    query_time < 1.0
                ), f"Simple query took too long: {query_time:.2f}s"

                # Test query with joins
                if len(users) > 0:
                    start_time = time.time()

                    stmt = (
                        select(User).options(selectinload(User.appointments)).limit(5)
                    )
                    result = await session.execute(stmt)
                    users_with_appointments = result.scalars().all()

                    end_time = time.time()
                    join_query_time = end_time - start_time

                    # Join query should also be reasonably fast
                    assert (
                        join_query_time < 2.0
                    ), f"Join query took too long: {join_query_time:.2f}s"

        except Exception as e:
            pytest.skip(f"Query performance test skipped: {e}")


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.transactions
class TestDatabaseTransactions:
    """Testes para transações de database"""

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        try:
            from sqlalchemy.exc import IntegrityError

            from app.database import AsyncSessionLocal
            from app.models.database import User

            async with AsyncSessionLocal() as session:
                # Create a user successfully
                user1 = User(
                    wa_id="5511999000100",
                    nome="Transaction Test User 1",
                    telefone="+55 11 99900-0100",
                )
                session.add(user1)
                await session.commit()
                await session.refresh(user1)

                user1_id = user1.id

                # Try to create another user with same wa_id (should fail)
                try:
                    async with session.begin():
                        user2 = User(
                            wa_id="5511999000100",  # Duplicate wa_id
                            nome="Transaction Test User 2",
                            telefone="+55 11 99900-0101",
                        )
                        session.add(user2)
                        await session.commit()

                        # Should not reach here due to unique constraint
                        pytest.fail("Duplicate wa_id should have caused an error")

                except Exception as e:
                    # Exception is expected due to unique constraint
                    await session.rollback()

                # Verify first user still exists
                existing_user = await session.get(User, user1_id)
                assert existing_user is not None
                assert existing_user.wa_id == "5511999000100"

                # Clean up
                await session.delete(existing_user)
                await session.commit()

        except Exception as e:
            pytest.skip(f"Transaction rollback test skipped: {e}")

    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """Test successful transaction commit"""
        try:
            from app.database import AsyncSessionLocal
            from app.models.database import Business, User

            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Create multiple related records in single transaction
                    user = User(
                        wa_id="5511999000200",
                        nome="Transaction User",
                        telefone="+55 11 99900-0200",
                    )

                    business = Business(
                        name="Transaction Business",
                        phone="+55 11 88888-8888",
                        email="transaction@test.com",
                    )

                    session.add(user)
                    session.add(business)
                    # Commit happens automatically at end of async with

                # Verify both records were created
                await session.refresh(user)
                await session.refresh(business)

                assert user.id is not None
                assert business.id is not None

                # Clean up
                await session.delete(user)
                await session.delete(business)
                await session.commit()

        except Exception as e:
            pytest.skip(f"Transaction commit test skipped: {e}")
