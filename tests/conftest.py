from collections.abc import AsyncGenerator
from typing import Any, Callable

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import cache_dependency, session_dependency
from app.api.router import api_router
from app.core.exceptions import ExceptionConfigurator
from app.db.base import Base
from app.models.table import RestaurantTable
from app.models.user import User
from app.services.table import TableService
from tests.fakes import FakeCacheService


class TestFastAPI(FastAPI):
    dependency_overrides: dict[Callable[..., Any], Callable[..., Any]]


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_maker() as db_session:
        yield db_session

    await engine.dispose()


@pytest.fixture
async def default_tables(session: AsyncSession) -> list[RestaurantTable]:
    tables = TableService.generate_default_tables()
    session.add_all(tables)
    await session.commit()
    return tables


@pytest.fixture
async def user(session: AsyncSession) -> User:
    model = User(
        email="test@example.com",
        phone_number="+70000000000",
        full_name="Test User",
        hashed_password="hashed",
        role=User.ROLE_USER,
    )
    session.add(model)
    await session.commit()
    return model


@pytest.fixture
async def user_two(session: AsyncSession) -> User:
    model = User(
        email="test2@example.com",
        phone_number="+70000000001",
        full_name="Test User Two",
        hashed_password="hashed",
        role=User.ROLE_USER,
    )
    session.add(model)
    await session.commit()
    return model


@pytest.fixture
async def api_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_maker() as db_session:
        db_session.add_all(TableService.generate_default_tables())
        await db_session.commit()
        yield db_session

    await engine.dispose()


@pytest.fixture
def api_cache_service() -> FakeCacheService:
    return FakeCacheService()


@pytest.fixture
async def api_client(
        api_session: AsyncSession,
        api_cache_service: FakeCacheService,
        monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    test_app = TestFastAPI()
    ExceptionConfigurator.register(test_app)
    test_app.include_router(api_router)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        yield api_session

    async def override_cache() -> FakeCacheService:
        return api_cache_service

    monkeypatch.setattr(
        "app.services.notification.send_booking_created_notification.delay",
        lambda **kwargs: None,
    )

    test_app.dependency_overrides[session_dependency] = override_session
    test_app.dependency_overrides[cache_dependency] = override_cache

    async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://testserver",
    ) as client:
        yield client

    test_app.dependency_overrides.clear()
