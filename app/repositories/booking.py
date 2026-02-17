from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        statement = select(Booking).filter_by(id=booking_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_or_future_for_user(self, user_id: int, now_at: datetime) -> list[Booking]:
        statement = (
            select(Booking)
            .filter_by(user_id=user_id)
            .where(Booking.canceled_at.is_(None))
            .where(Booking.end_at >= now_at)
            .order_by(Booking.start_at.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def has_overlap(
            self,
            table_id: int,
            start_at: datetime,
            end_at: datetime,
            exclude_booking_id: int | None = None,
    ) -> bool:
        statement = (
            select(Booking.id)
            .filter_by(table_id=table_id)
            .where(Booking.canceled_at.is_(None))
            .where(Booking.start_at < end_at)
            .where(Booking.end_at > start_at)
        )
        if exclude_booking_id is not None:
            statement = statement.where(Booking.id.notin_([exclude_booking_id]))
        result = await self.session.execute(statement.limit(1))
        return result.scalar_one_or_none() is not None

    async def create(self, user_id: int, table_id: int, start_at: datetime, end_at: datetime) -> Booking:
        booking = Booking(user_id=user_id, table_id=table_id, start_at=start_at, end_at=end_at)
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def update_slot(self, booking: Booking, start_at: datetime, end_at: datetime) -> Booking:
        booking.start_at = start_at
        booking.end_at = end_at
        await self.session.flush()
        return booking

    async def cancel(self, booking: Booking, canceled_at: datetime) -> Booking:
        booking.canceled_at = canceled_at
        await self.session.flush()
        return booking
