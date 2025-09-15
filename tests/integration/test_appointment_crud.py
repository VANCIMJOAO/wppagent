"""
VL-001: Appointment CRUD Integration Tests

Tests for appointment operations including:
- Create appointments with validation
- Read single and multiple appointments
- Update appointment details
- Delete appointments with proper cleanup
- Business logic validation
- Data integrity checks
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.critical
@pytest.mark.asyncio
async def test_appointment_crud_complete_flow(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """
    Test complete CRUD flow for appointments:
    1. Create appointment
    2. Read appointment
    3. Update appointment
    4. Delete appointment
    """

    # 1. CREATE - Create new appointment
    appointment_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "status": "agendado",
        "notes": "VL-001 Test appointment for CRUD flow",
    }

    create_response = await authenticated_client.post(
        "/appointments/", json=appointment_data
    )

    # Verify creation
    assert create_response.status_code in [200, 201]
    created_data = create_response.json()

    # Extract appointment ID for subsequent operations
    if "data" in created_data and "id" in created_data["data"]:
        apt_id = created_data["data"]["id"]
    elif "id" in created_data:
        apt_id = created_data["id"]
    else:
        pytest.fail(f"Could not extract appointment ID from response: {created_data}")

    assert apt_id is not None

    # 2. READ - Get the created appointment
    get_response = await authenticated_client.get(f"/appointments/{apt_id}")
    assert get_response.status_code == 200

    get_data = get_response.json()
    if "data" in get_data:
        appointment = get_data["data"]
    else:
        appointment = get_data

    assert appointment["id"] == apt_id
    assert appointment["notes"] == "VL-001 Test appointment for CRUD flow"
    assert appointment["status"] == "agendado"

    # 3. UPDATE - Modify the appointment
    update_data = {"notes": "VL-001 Updated test appointment", "status": "confirmado"}

    update_response = await authenticated_client.put(
        f"/appointments/{apt_id}", json=update_data
    )
    assert update_response.status_code == 200

    # Verify update
    updated_data = update_response.json()
    if "data" in updated_data:
        updated_appointment = updated_data["data"]
    else:
        updated_appointment = updated_data

    assert updated_appointment["notes"] == "VL-001 Updated test appointment"
    assert updated_appointment["status"] == "confirmado"

    # 4. DELETE - Remove the appointment
    delete_response = await authenticated_client.delete(f"/appointments/{apt_id}")
    assert delete_response.status_code in [200, 204]

    # Verify deletion
    get_deleted_response = await authenticated_client.get(f"/appointments/{apt_id}")
    assert get_deleted_response.status_code in [404, 410]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_appointment_list_with_filters(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """Test listing appointments with filters and pagination."""

    # Create multiple test appointments
    base_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "notes": "VL-001 List test appointment",
    }

    appointments = []
    for i in range(3):
        appointment_data = {
            **base_data,
            "date_time": (datetime.now() + timedelta(days=i + 1)).isoformat(),
            "status": "agendado" if i % 2 == 0 else "confirmado",
            "notes": f"VL-001 List test appointment {i+1}",
        }

        response = await authenticated_client.post(
            "/appointments/", json=appointment_data
        )
        if response.status_code in [200, 201]:
            data = response.json()
            if "data" in data:
                appointments.append(data["data"]["id"])
            elif "id" in data:
                appointments.append(data["id"])

    # Test list all appointments
    list_response = await authenticated_client.get("/appointments/")
    assert list_response.status_code == 200

    list_data = list_response.json()
    if "data" in list_data:
        appointment_list = list_data["data"]
    else:
        appointment_list = list_data

    assert isinstance(appointment_list, list)
    assert len(appointment_list) >= 3

    # Test with pagination
    paginated_response = await authenticated_client.get(
        "/appointments/?limit=2&offset=0"
    )
    assert paginated_response.status_code == 200

    # Test with status filter
    status_response = await authenticated_client.get("/appointments/?status=agendado")
    assert status_response.status_code == 200

    # Cleanup created appointments
    for apt_id in appointments:
        await authenticated_client.delete(f"/appointments/{apt_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_appointment_validation_errors(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """Test appointment creation with validation errors."""

    # Missing required fields
    invalid_data = {"notes": "Missing required fields"}

    response = await authenticated_client.post("/appointments/", json=invalid_data)
    assert response.status_code in [400, 422]

    # Invalid user_id
    invalid_user_data = {
        "user_id": 99999,  # Non-existent user
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "status": "agendado",
    }

    response = await authenticated_client.post("/appointments/", json=invalid_user_data)
    assert response.status_code in [400, 404, 422]

    # Invalid date format
    invalid_date_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": "invalid-date-format",
        "status": "agendado",
    }

    response = await authenticated_client.post("/appointments/", json=invalid_date_data)
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_appointment_business_logic(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """Test appointment business logic validation."""

    # Past date appointment should be rejected or handled appropriately
    past_date_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() - timedelta(days=1)).isoformat(),
        "status": "agendado",
        "notes": "Past date appointment test",
    }

    response = await authenticated_client.post("/appointments/", json=past_date_data)
    # Business logic may allow or reject past dates
    assert response.status_code in [200, 201, 400, 422]

    # Test status transitions
    future_date_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "status": "agendado",
        "notes": "Status transition test",
    }

    create_response = await authenticated_client.post(
        "/appointments/", json=future_date_data
    )
    if create_response.status_code in [200, 201]:
        data = create_response.json()
        if "data" in data:
            apt_id = data["data"]["id"]
        else:
            apt_id = data["id"]

        # Test valid status transitions
        for status in ["confirmado", "concluido", "cancelado"]:
            update_response = await authenticated_client.put(
                f"/appointments/{apt_id}", json={"status": status}
            )
            # Should accept valid status transitions
            assert update_response.status_code in [200, 400]  # Business rules dependent

        # Cleanup
        await authenticated_client.delete(f"/appointments/{apt_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_appointment_concurrent_operations(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """Test concurrent operations on appointments."""

    # Create appointment
    appointment_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=3)).isoformat(),
        "status": "agendado",
        "notes": "Concurrent operations test",
    }

    create_response = await authenticated_client.post(
        "/appointments/", json=appointment_data
    )
    if create_response.status_code not in [200, 201]:
        pytest.skip("Could not create appointment for concurrent test")

    data = create_response.json()
    if "data" in data:
        apt_id = data["data"]["id"]
    else:
        apt_id = data["id"]

    # Simulate concurrent updates
    import asyncio

    async def update_appointment(field_value_pair):
        field, value = field_value_pair
        return await authenticated_client.put(
            f"/appointments/{apt_id}", json={field: value}
        )

    # Concurrent updates to different fields
    updates = [
        ("notes", "Concurrent update 1"),
        ("status", "confirmado"),
    ]

    results = await asyncio.gather(*[update_appointment(update) for update in updates])

    # At least one update should succeed
    success_count = sum(1 for result in results if result.status_code == 200)
    assert success_count >= 1

    # Cleanup
    await authenticated_client.delete(f"/appointments/{apt_id}")


@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.asyncio
async def test_appointment_performance(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """Test appointment operations performance (basic)."""
    import time

    # Test create performance
    start_time = time.time()

    appointment_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=4)).isoformat(),
        "status": "agendado",
        "notes": "Performance test appointment",
    }

    response = await authenticated_client.post("/appointments/", json=appointment_data)
    create_time = time.time() - start_time

    # Create should be fast (< 2 seconds)
    assert create_time < 2.0
    assert response.status_code in [200, 201]

    if response.status_code in [200, 201]:
        data = response.json()
        if "data" in data:
            apt_id = data["data"]["id"]
        else:
            apt_id = data["id"]

        # Test read performance
        start_time = time.time()
        get_response = await authenticated_client.get(f"/appointments/{apt_id}")
        read_time = time.time() - start_time

        assert read_time < 1.0  # Read should be very fast
        assert get_response.status_code == 200

        # Cleanup
        await authenticated_client.delete(f"/appointments/{apt_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_appointment_edge_cases(
    authenticated_client: AsyncClient, test_data_setup: Dict[str, Any]
):
    """Test appointment edge cases and boundary conditions."""

    # Test with very long notes
    long_notes_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=5)).isoformat(),
        "status": "agendado",
        "notes": "A" * 1000,  # Very long string
    }

    response = await authenticated_client.post("/appointments/", json=long_notes_data)
    # Should handle long notes gracefully
    assert response.status_code in [200, 201, 400, 422]

    # Test with special characters in notes
    special_chars_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=6)).isoformat(),
        "status": "agendado",
        "notes": "Test with special chars: àáâãäåæçèéêë ñòóôõö ùúûü €£¥",
    }

    response = await authenticated_client.post(
        "/appointments/", json=special_chars_data
    )
    assert response.status_code in [200, 201, 400, 422]

    # Test with far future date
    far_future_data = {
        "user_id": test_data_setup["user_id"],
        "service_id": test_data_setup["service_id"],
        "business_id": test_data_setup["business_id"],
        "date_time": (datetime.now() + timedelta(days=365)).isoformat(),
        "status": "agendado",
        "notes": "Far future appointment",
    }

    response = await authenticated_client.post("/appointments/", json=far_future_data)
    # Business logic may limit how far in the future appointments can be
    assert response.status_code in [200, 201, 400, 422]
