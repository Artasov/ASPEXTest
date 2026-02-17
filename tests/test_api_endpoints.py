from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.user import User
from tests.fakes import FakeCacheService


@pytest.mark.asyncio
async def test_auth_register_and_login_flow(api_client: AsyncClient) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-user@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000200",
            "full_name": "Api User",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["access_token"]

    login_response = await api_client.post(
        "/auth/login",
        json={"email": "api-user@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_bookings_my_requires_auth(api_client: AsyncClient) -> None:
    response = await api_client.get("/bookings/my")

    assert response.status_code == 401
    assert response.json()["error_code"] == "auth_error"


@pytest.mark.asyncio
async def test_tables_available_with_auth_returns_items(api_client: AsyncClient) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-table@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000201",
            "full_name": "Api Table",
        },
    )
    token = register_response.json()["access_token"]

    response = await api_client.get(
        "/tables/available",
        params={
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time": "13:00:00",
            "guests": 2,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()["tables"]) == 16


@pytest.mark.asyncio
async def test_create_booking_and_get_my(
        api_client: AsyncClient,
        api_cache_service: FakeCacheService,
) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-booking@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000202",
            "full_name": "Api Booking",
        },
    )
    token = register_response.json()["access_token"]
    booking_response = await api_client.post(
        "/bookings/",
        json={
            "table_id": 1,
            "date": (date.today() + timedelta(days=2)).isoformat(),
            "time": "13:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert booking_response.status_code == 201

    my_response = await api_client.get(
        "/bookings/my",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert my_response.status_code == 200
    assert len(my_response.json()["items"]) == 1
    assert "tables:available:" in api_cache_service.invalidated_prefixes


@pytest.mark.asyncio
async def test_create_booking_with_timezone_aware_time(api_client: AsyncClient) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-tz@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000203",
            "full_name": "Api TZ",
        },
    )
    token = register_response.json()["access_token"]

    response = await api_client.post(
        "/bookings/",
        json={
            "table_id": 2,
            "date": (date.today() + timedelta(days=3)).isoformat(),
            "time": "13:00:00+00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["id"]


@pytest.mark.asyncio
async def test_create_booking_overlap_returns_conflict(api_client: AsyncClient) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-overlap@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000204",
            "full_name": "Api Overlap",
        },
    )
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "table_id": 3,
        "date": (date.today() + timedelta(days=4)).isoformat(),
        "time": "14:00:00",
    }

    first = await api_client.post("/bookings/", json=payload, headers=headers)
    assert first.status_code == 201

    second = await api_client.post("/bookings/", json=payload, headers=headers)
    assert second.status_code == 409
    assert second.json()["error_code"] == "conflict"


@pytest.mark.asyncio
async def test_update_booking_of_other_user_forbidden(api_client: AsyncClient) -> None:
    user_one_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-owner@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000205",
            "full_name": "Api Owner",
        },
    )
    user_one_token = user_one_response.json()["access_token"]
    create_response = await api_client.post(
        "/bookings/",
        json={
            "table_id": 4,
            "date": (date.today() + timedelta(days=5)).isoformat(),
            "time": "13:00:00",
        },
        headers={"Authorization": f"Bearer {user_one_token}"},
    )
    booking_id = create_response.json()["id"]

    user_two_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-another@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000206",
            "full_name": "Api Another",
        },
    )
    user_two_token = user_two_response.json()["access_token"]

    update_response = await api_client.patch(
        f"/bookings/{booking_id}",
        json={
            "date": (date.today() + timedelta(days=5)).isoformat(),
            "time": "15:00:00",
        },
        headers={"Authorization": f"Bearer {user_two_token}"},
    )

    assert update_response.status_code == 403
    assert update_response.json()["error_code"] == "forbidden"


@pytest.mark.asyncio
async def test_cancel_booking_too_late_returns_business_error(
        api_client: AsyncClient,
        api_session: AsyncSession,
) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "api-cancel@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000207",
            "full_name": "Api Cancel",
        },
    )
    token = register_response.json()["access_token"]

    user_result = await api_session.execute(select(User).filter_by(email="api-cancel@example.com"))
    user_model = user_result.scalar_one()
    start_at = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
    booking = Booking(
        user_id=user_model.id,
        table_id=5,
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
    )
    api_session.add(booking)
    await api_session.commit()

    response = await api_client.delete(
        f"/bookings/{booking.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "business_rule_error"
