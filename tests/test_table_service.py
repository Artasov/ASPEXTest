from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError
from app.models.booking import Booking
from app.services.table import TableService
from tests.fakes import FakeCacheService


@pytest.mark.asyncio
async def test_get_available_tables_respects_guest_count(
        session: AsyncSession,
        default_tables: list,
) -> None:
    cache_service = FakeCacheService()
    table_service = TableService(session, cache_service)

    response = await table_service.get_available(slot_date=date.today(), slot_time=time(13, 0), guests=3)

    assert len(response.tables) == 9
    assert all(item.seats >= 3 for item in response.tables)

    second_response = await table_service.get_available(
        slot_date=date.today(),
        slot_time=time(13, 0),
        guests=3,
    )
    assert len(second_response.tables) == 9
    assert cache_service.storage


@pytest.mark.asyncio
async def test_get_available_tables_outside_working_hours_raises(
        session: AsyncSession,
        default_tables: list,
) -> None:
    cache_service = FakeCacheService()
    table_service = TableService(session, cache_service)

    with pytest.raises(BusinessRuleError):
        await table_service.get_available(slot_date=date.today(), slot_time=time(11, 30), guests=2)


@pytest.mark.asyncio
async def test_get_available_tables_excludes_booked_table(
        session: AsyncSession,
        default_tables: list,
) -> None:
    table = default_tables[0]
    slot_date = date.today() + timedelta(days=1)
    slot_time = time(13, 0)
    start_at = datetime.combine(slot_date, slot_time).replace(tzinfo=timezone.utc)
    booking = Booking(
        user_id=1,
        table_id=table.id,
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
    )
    session.add(booking)
    await session.commit()

    cache_service = FakeCacheService()
    table_service = TableService(session, cache_service)
    response = await table_service.get_available(slot_date=slot_date, slot_time=slot_time, guests=2)

    table_ids = {item.id for item in response.tables}
    assert table.id not in table_ids


@pytest.mark.asyncio
async def test_get_available_tables_with_timezone_aware_time(
        session: AsyncSession,
        default_tables: list,
) -> None:
    cache_service = FakeCacheService()
    table_service = TableService(session, cache_service)

    response = await table_service.get_available(
        slot_date=date.today() + timedelta(days=1),
        slot_time=time(13, 0, tzinfo=timezone.utc),
        guests=2,
    )

    assert response.tables
