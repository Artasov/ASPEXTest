import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import SecurityService
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import AuthService


@pytest.mark.asyncio
async def test_register_returns_token(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    payload = RegisterRequest(
        email="new@example.com",
        password="StrongPass123",
        phone_number="+79990000001",
        full_name="New User",
    )

    token_data = await auth_service.register(payload)

    assert token_data.access_token
    assert token_data.expires_in == 3600
    assert token_data.token_type == "bearer"
    created = await session.execute(select(User).filter_by(email="new@example.com"))
    model = created.scalar_one()
    assert model.role == User.ROLE_USER


@pytest.mark.asyncio
async def test_register_duplicate_email_raises_conflict(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    payload = RegisterRequest(
        email="dup@example.com",
        password="StrongPass123",
        phone_number="+79990000002",
        full_name="First User",
    )
    await auth_service.register(payload)

    duplicate_payload = RegisterRequest(
        email="dup@example.com",
        password="StrongPass123",
        phone_number="+79990000003",
        full_name="Second User",
    )

    with pytest.raises(ConflictError):
        await auth_service.register(duplicate_payload)


@pytest.mark.asyncio
async def test_login_invalid_password_raises_auth_error(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    register_payload = RegisterRequest(
        email="login@example.com",
        password="StrongPass123",
        phone_number="+79990000004",
        full_name="Login User",
    )
    await auth_service.register(register_payload)

    with pytest.raises(AuthenticationError):
        await auth_service.login(LoginRequest(email="login@example.com", password="BadPass123"))


@pytest.mark.asyncio
async def test_register_duplicate_phone_raises_conflict(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    await auth_service.register(
        RegisterRequest(
            email="phone-1@example.com",
            password="StrongPass123",
            phone_number="+79990000111",
            full_name="First",
        )
    )

    with pytest.raises(ConflictError):
        await auth_service.register(
            RegisterRequest(
                email="phone-2@example.com",
                password="StrongPass123",
                phone_number="+79990000111",
                full_name="Second",
            )
        )


@pytest.mark.asyncio
async def test_login_success_returns_token(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    await auth_service.register(
        RegisterRequest(
            email="ok@example.com",
            password="StrongPass123",
            phone_number="+79990000112",
            full_name="Ok User",
        )
    )

    token_data = await auth_service.login(LoginRequest(email="ok@example.com", password="StrongPass123"))

    assert token_data.access_token
    assert token_data.expires_in == 3600


@pytest.mark.asyncio
async def test_get_user_from_token_invalid_token_raises_auth_error(session: AsyncSession) -> None:
    auth_service = AuthService(session)

    with pytest.raises(AuthenticationError):
        await auth_service.get_user_from_token("not-a-jwt")


@pytest.mark.asyncio
async def test_get_user_from_token_missing_user_raises_auth_error(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    token = SecurityService.create_access_token(subject="999999")

    with pytest.raises(AuthenticationError):
        await auth_service.get_user_from_token(token)


@pytest.mark.asyncio
async def test_register_assigns_admin_role_from_admin_emails(session: AsyncSession) -> None:
    auth_service = AuthService(session)
    current_admin_emails = settings.ADMIN_EMAILS
    settings.ADMIN_EMAILS = "boss@example.com"
    payload = RegisterRequest(
        email="boss@example.com",
        password="StrongPass123",
        phone_number="+79990000555",
        full_name="Boss User",
    )
    try:
        await auth_service.register(payload)
    finally:
        settings.ADMIN_EMAILS = current_admin_emails

    created = await session.execute(select(User).filter_by(email="boss@example.com"))
    model = created.scalar_one()
    assert model.role == User.ROLE_ADMIN
