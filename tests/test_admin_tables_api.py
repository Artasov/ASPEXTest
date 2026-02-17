import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SecurityService
from app.models.user import User


@pytest.mark.asyncio
async def test_admin_tables_forbidden_for_regular_user(
        api_client: AsyncClient,
) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={
            "email": "regular-user@example.com",
            "password": "StrongPass123",
            "phone_number": "+79990000771",
            "full_name": "Regular User",
        },
    )
    token = register_response.json()["access_token"]
    response = await api_client.get(
        "/admin/tables/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "forbidden"


@pytest.mark.asyncio
async def test_admin_tables_crud_flow(
        api_client: AsyncClient,
        api_session: AsyncSession,
) -> None:
    admin = User(
        email="admin-user@example.com",
        phone_number="+79990000772",
        full_name="Admin User",
        hashed_password="hashed",
        role=User.ROLE_ADMIN,
    )
    api_session.add(admin)
    await api_session.commit()
    admin_token = SecurityService.create_access_token(subject=str(admin.id))
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_response = await api_client.post(
        "/admin/tables/",
        json={"name": "T9-1", "seats": 9},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "T9-1"
    assert created["seats"] == 9

    list_response = await api_client.get("/admin/tables/", headers=headers)
    assert list_response.status_code == 200
    table_ids = {item["id"] for item in list_response.json()["items"]}
    assert created["id"] in table_ids

    update_response = await api_client.patch(
        f"/admin/tables/{created['id']}",
        json={"name": "T9-2", "seats": 10},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "T9-2"
    assert update_response.json()["seats"] == 10

    delete_response = await api_client.delete(f"/admin/tables/{created['id']}", headers=headers)
    assert delete_response.status_code == 204
