from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, BusinessRuleError, ConflictError, NotFoundError
from app.models.booking import Booking
from app.schemas.booking import BookingCreateRequest, BookingUpdateRequest
from app.services.booking import BookingService
from tests.fakes import FakeCacheService, FakeNotificationService


@pytest.mark.asyncio
async def test_create_booking_success(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    cache_service = FakeCacheService()
    notification_service = FakeNotificationService()
    service = BookingService(
        session=session,
        cache_service=cache_service,
        notification_service=notification_service,
    )
    table = default_tables[0]
    payload = BookingCreateRequest(
        table_id=table.id,
        date=date.today() + timedelta(days=1),
        time=time(13, 0),
    )

    booking = await service.create(user=user, payload=payload)

    assert booking.id is not None
    assert booking.table_id == table.id
    assert notification_service.calls
    assert cache_service.invalidated_prefixes == ["tables:available:"]


@pytest.mark.asyncio
async def test_create_booking_overlap_raises_conflict(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    cache_service = FakeCacheService()
    notification_service = FakeNotificationService()
    service = BookingService(
        session=session,
        cache_service=cache_service,
        notification_service=notification_service,
    )
    table = default_tables[1]
    payload = BookingCreateRequest(
        table_id=table.id,
        date=date.today() + timedelta(days=2),
        time=time(14, 0),
    )
    await service.create(user=user, payload=payload)

    with pytest.raises(ConflictError):
        await service.create(user=user, payload=payload)


@pytest.mark.asyncio
async def test_cancel_booking_too_late_raises_business_error(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    table = default_tables[2]
    start_at = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
    end_at = start_at + timedelta(hours=2)
    booking = Booking(user_id=user.id, table_id=table.id, start_at=start_at, end_at=end_at)
    session.add(booking)
    await session.commit()

    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )

    with pytest.raises(BusinessRuleError):
        await service.cancel(user_id=user.id, booking_id=booking.id)


@pytest.mark.asyncio
async def test_update_booking_changes_slot(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )
    table = default_tables[3]
    created = await service.create(
        user=user,
        payload=BookingCreateRequest(
            table_id=table.id,
            date=date.today() + timedelta(days=3),
            time=time(13, 0),
        ),
    )

    updated = await service.update(
        user_id=user.id,
        booking_id=created.id,
        payload=BookingUpdateRequest(
            date=date.today() + timedelta(days=3),
            time=time(15, 0),
        ),
    )

    assert updated.start_at.hour == 15
    assert updated.end_at.hour == 17


@pytest.mark.asyncio
async def test_create_booking_missing_table_raises_not_found(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )

    with pytest.raises(NotFoundError):
        await service.create(
            user=user,
            payload=BookingCreateRequest(
                table_id=9999,
                date=date.today() + timedelta(days=1),
                time=time(13, 0),
            ),
        )


@pytest.mark.asyncio
async def test_create_booking_in_past_raises_business_rule(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )
    table = default_tables[0]

    with pytest.raises(BusinessRuleError):
        await service.create(
            user=user,
            payload=BookingCreateRequest(
                table_id=table.id,
                date=date.today() - timedelta(days=1),
                time=time(13, 0),
            ),
        )


@pytest.mark.asyncio
async def test_update_booking_overlap_raises_conflict(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )
    table = default_tables[4]
    first = await service.create(
        user=user,
        payload=BookingCreateRequest(
            table_id=table.id,
            date=date.today() + timedelta(days=2),
            time=time(13, 0),
        ),
    )
    second = await service.create(
        user=user,
        payload=BookingCreateRequest(
            table_id=table.id,
            date=date.today() + timedelta(days=2),
            time=time(16, 0),
        ),
    )

    with pytest.raises(ConflictError):
        await service.update(
            user_id=user.id,
            booking_id=second.id,
            payload=BookingUpdateRequest(
                date=first.start_at.date(),
                time=time(13, 0),
            ),
        )


@pytest.mark.asyncio
async def test_cancel_booking_success_sets_canceled_at(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    cache_service = FakeCacheService()
    service = BookingService(
        session=session,
        cache_service=cache_service,
        notification_service=FakeNotificationService(),
    )
    table = default_tables[5]
    booking = await service.create(
        user=user,
        payload=BookingCreateRequest(
            table_id=table.id,
            date=date.today() + timedelta(days=4),
            time=time(13, 0),
        ),
    )

    canceled = await service.cancel(user_id=user.id, booking_id=booking.id)

    assert canceled.canceled_at is not None
    assert "tables:available:" in cache_service.invalidated_prefixes


@pytest.mark.asyncio
async def test_cancel_booking_already_canceled_raises_conflict(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )
    table = default_tables[6]
    booking = await service.create(
        user=user,
        payload=BookingCreateRequest(
            table_id=table.id,
            date=date.today() + timedelta(days=4),
            time=time(14, 0),
        ),
    )
    await service.cancel(user_id=user.id, booking_id=booking.id)

    with pytest.raises(ConflictError):
        await service.cancel(user_id=user.id, booking_id=booking.id)


@pytest.mark.asyncio
async def test_update_booking_other_user_raises_authorization(
        session: AsyncSession,
        user,
        user_two,
        default_tables,
) -> None:
    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )
    table = default_tables[7]
    booking = await service.create(
        user=user,
        payload=BookingCreateRequest(
            table_id=table.id,
            date=date.today() + timedelta(days=3),
            time=time(13, 0),
        ),
    )

    with pytest.raises(AuthorizationError):
        await service.update(
            user_id=user_two.id,
            booking_id=booking.id,
            payload=BookingUpdateRequest(
                date=date.today() + timedelta(days=3),
                time=time(15, 0),
            ),
        )


@pytest.mark.asyncio
async def test_get_my_returns_only_active_and_future(
        session: AsyncSession,
        user,
        default_tables,
) -> None:
    table = default_tables[8]
    active_start = datetime.now(tz=timezone.utc) + timedelta(days=1)
    active_end = active_start + timedelta(hours=2)
    past_start = datetime.now(tz=timezone.utc) - timedelta(days=2)
    past_end = past_start + timedelta(hours=2)
    canceled_start = datetime.now(tz=timezone.utc) + timedelta(days=2)
    canceled_end = canceled_start + timedelta(hours=2)
    session.add_all(
        [
            Booking(user_id=user.id, table_id=table.id, start_at=active_start, end_at=active_end),
            Booking(user_id=user.id, table_id=table.id, start_at=past_start, end_at=past_end),
            Booking(
                user_id=user.id,
                table_id=table.id,
                start_at=canceled_start,
                end_at=canceled_end,
                canceled_at=datetime.now(tz=timezone.utc),
            ),
        ]
    )
    await session.commit()

    service = BookingService(
        session=session,
        cache_service=FakeCacheService(),
        notification_service=FakeNotificationService(),
    )
    items = await service.get_my(user_id=user.id)

    assert len(items) == 1
    assert items[0].start_at == active_start.replace(tzinfo=None)
