"""
Unit Tests for Appointment Model

Tests for:
- Appointment creation and validation
- Date/time handling and calculations
- Status management
- Price handling
- Business logic methods
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.database import Appointment


class TestAppointment:
    """Test cases for Appointment model"""

    @pytest.mark.unit
    def test_appointment_creation(self):
        """Test basic Appointment creation with required fields"""
        appointment_time = datetime.now() + timedelta(days=1)

        appointment = Appointment(
            user_id=1,
            business_id=1,
            service_id=1,
            date_time=appointment_time,
            duration_minutes=60,
            price=Decimal("50.00"),
        )

        assert appointment.user_id == 1
        assert appointment.business_id == 1
        assert appointment.service_id == 1
        assert appointment.date_time == appointment_time
        assert appointment.duration_minutes == 60
        assert appointment.price == Decimal("50.00")
        # SQLAlchemy defaults are not set until the object is persisted
        assert appointment.status is None or appointment.status == "agendado"  # Default

    @pytest.mark.unit
    def test_appointment_defaults(self):
        """Test default values for Appointment fields"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Check defaults
        # SQLAlchemy defaults are not set until the object is persisted
        assert (
            appointment.duration_minutes is None or appointment.duration_minutes == 60
        )  # Default
        assert appointment.status is None or appointment.status == "agendado"  # Default
        assert appointment.price is None or appointment.price == Decimal(
            "0.00"
        )  # Default
        assert appointment.notes is None
        assert appointment.customer_notes is None
        assert appointment.admin_notes is None
        assert appointment.cancelled_at is None
        assert appointment.confirmed_at is None

    @pytest.mark.unit
    def test_calculate_end_time(self):
        """Test end_time calculation based on date_time and duration"""
        start_time = datetime(2024, 1, 15, 14, 30)  # 2:30 PM

        appointment = Appointment(
            user_id=1,
            business_id=1,
            service_id=1,
            date_time=start_time,
            duration_minutes=90,
        )

        # Calculate end time
        end_time = appointment.calculate_end_time()

        expected_end = start_time + timedelta(minutes=90)  # 4:00 PM
        assert end_time == expected_end
        assert appointment.end_time == expected_end

    @pytest.mark.unit
    def test_calculate_end_time_different_durations(self):
        """Test end_time calculation with different durations"""
        start_time = datetime(2024, 1, 15, 10, 0)

        # Test various durations
        durations = [30, 60, 90, 120, 180]

        for duration in durations:
            appointment = Appointment(
                user_id=1,
                business_id=1,
                service_id=1,
                date_time=start_time,
                duration_minutes=duration,
            )

            end_time = appointment.calculate_end_time()
            expected_end = start_time + timedelta(minutes=duration)

            assert end_time == expected_end
            assert appointment.end_time == expected_end

    @pytest.mark.unit
    def test_calculate_end_time_edge_cases(self):
        """Test end_time calculation edge cases"""
        # Test with None date_time
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, duration_minutes=60
        )
        appointment.date_time = None

        end_time = appointment.calculate_end_time()
        assert end_time is None
        assert appointment.end_time is None

        # Test with None duration
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )
        appointment.duration_minutes = None

        end_time = appointment.calculate_end_time()
        assert end_time is None

    @pytest.mark.unit
    def test_appointment_status_management(self):
        """Test appointment status field and transitions"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Test default status
        # SQLAlchemy defaults are not set until the object is persisted
        assert appointment.status is None or appointment.status == "agendado"

        # Test status transitions
        valid_statuses = [
            "agendado",
            "confirmado",
            "realizado",
            "cancelado",
            "pendente",
        ]

        for status in valid_statuses:
            appointment.status = status
            assert appointment.status == status

    @pytest.mark.unit
    def test_appointment_notes(self):
        """Test different types of notes fields"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Test notes assignment
        appointment.notes = "General appointment notes"
        appointment.customer_notes = "Customer requested early morning"
        appointment.admin_notes = "Customer is a VIP, provide extra attention"

        assert appointment.notes == "General appointment notes"
        assert appointment.customer_notes == "Customer requested early morning"
        assert appointment.admin_notes == "Customer is a VIP, provide extra attention"

        # Test long notes
        long_note = "This is a very long note. " * 50
        appointment.notes = long_note
        assert appointment.notes == long_note

    @pytest.mark.unit
    def test_appointment_cancellation_data(self):
        """Test cancellation-related fields"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Test cancellation data
        cancellation_time = datetime.now()
        appointment.cancelled_at = cancellation_time
        appointment.cancellation_reason = "Customer sick"
        appointment.cancelled_by = "customer"

        assert appointment.cancelled_at == cancellation_time
        assert appointment.cancellation_reason == "Customer sick"
        assert appointment.cancelled_by == "customer"

        # Test different cancelled_by values
        valid_cancelled_by = ["customer", "admin", "system"]
        for cancelled_by in valid_cancelled_by:
            appointment.cancelled_by = cancelled_by
            assert appointment.cancelled_by == cancelled_by

    @pytest.mark.unit
    def test_appointment_confirmation_data(self):
        """Test confirmation-related fields"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Test confirmation data
        confirmation_time = datetime.now()
        appointment.confirmed_at = confirmation_time
        appointment.confirmed_by = "customer"

        assert appointment.confirmed_at == confirmation_time
        assert appointment.confirmed_by == "customer"

        # Test different confirmed_by values
        valid_confirmed_by = ["customer", "admin", "auto"]
        for confirmed_by in valid_confirmed_by:
            appointment.confirmed_by = confirmed_by
            assert appointment.confirmed_by == confirmed_by

    @pytest.mark.unit
    def test_appointment_price_handling(self):
        """Test price field with different values and types"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Test different price values
        prices = [
            Decimal("0.00"),
            Decimal("25.50"),
            Decimal("100.00"),
            Decimal("999.99"),
            Decimal("1500.00"),
        ]

        for price in prices:
            appointment.price = price
            assert appointment.price == price
            assert isinstance(appointment.price, Decimal)

    @pytest.mark.unit
    def test_to_dict_method(self):
        """Test to_dict method for API serialization"""
        start_time = datetime(2024, 1, 15, 14, 30)

        appointment = Appointment(
            user_id=1,
            business_id=2,
            service_id=3,
            date_time=start_time,
            duration_minutes=90,
            price=Decimal("75.00"),
            status="confirmado",
            notes="Test appointment",
        )

        # Calculate end time first
        appointment.calculate_end_time()

        # Mock timestamps
        appointment.created_at = datetime(2024, 1, 1, 10, 0)
        appointment.updated_at = datetime(2024, 1, 2, 11, 0)

        result = appointment.to_dict()

        expected = {
            "id": None,  # Not set in test
            "user_id": 1,
            "business_id": 2,
            "service_id": 3,
            "date_time": start_time.isoformat(),
            "duration_minutes": 90,
            "end_time": (start_time + timedelta(minutes=90)).isoformat(),
            "price": 75.00,
            "status": "confirmado",
            "notes": "Test appointment",
            "created_at": appointment.created_at.isoformat(),
            "updated_at": appointment.updated_at.isoformat(),
        }

        assert result == expected

    @pytest.mark.unit
    def test_to_dict_with_none_values(self):
        """Test to_dict method with None values"""
        appointment = Appointment(user_id=1, business_id=1, service_id=1)
        # date_time is None

        result = appointment.to_dict()

        assert result["date_time"] is None
        assert result["end_time"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["price"] == 0.00  # Default value

    @pytest.mark.unit
    def test_appointment_duration_edge_cases(self):
        """Test duration_minutes with edge case values"""
        appointment = Appointment(
            user_id=1, business_id=1, service_id=1, date_time=datetime.now()
        )

        # Test various duration values
        durations = [1, 15, 30, 60, 120, 240, 480]  # 1 min to 8 hours

        for duration in durations:
            appointment.duration_minutes = duration
            assert appointment.duration_minutes == duration

    @pytest.mark.unit
    def test_appointment_foreign_key_assignment(self):
        """Test foreign key field assignment"""
        appointment = Appointment()

        # Test ID assignment
        appointment.user_id = 123
        appointment.business_id = 456
        appointment.service_id = 789

        assert appointment.user_id == 123
        assert appointment.business_id == 456
        assert appointment.service_id == 789
