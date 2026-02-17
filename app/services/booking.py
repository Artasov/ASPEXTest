from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthorizationError, BusinessRuleError, ConflictError, NotFoundError
from app.models.booking import Booking
from app.models.user import User
from app.repositories.booking import BookingRepository
from app.repositories.table import TableRepository
from app.schemas.booking import BookingCreateRequest, BookingUpdateRequest
from app.services.cache import CacheServiceProtocol
from app.services.notification import NotificationService, NotificationServiceProtocol
from app.services.slot import BookingSlotService
from app.services.table import TableService


class BookingService:
    def __init__(
            self,
            session: AsyncSession,
            cache_service: CacheServiceProtocol,
            notification_service: NotificationServiceProtocol | None = None,
    ):
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.table_repository = TableRepository(session)
        self.table_service = TableService(session, cache_service)
        self.notification_service = notification_service or NotificationService()

    async def create(self, user: User, payload: BookingCreateRequest) -> Booking:
        if not BookingSlotService.can_book_time(payload.date, payload.time):
            raise BusinessRuleError(
                f"Booking is available from {settings.WORKDAY_START_HOUR}:00 "
                f"to {settings.WORKDAY_END_HOUR - settings.BOOKING_SLOT_HOURS}:00."
            )

        table = await self.table_repository.get_by_id(payload.table_id)
        if table is None:
            raise NotFoundError("Table was not found.")

        start_at, end_at = BookingSlotService.build_slot(payload.date, payload.time)
        if start_at <= datetime.now(tz=timezone.utc):
            raise BusinessRuleError("Booking start must be in the future.")

        has_overlap = await self.booking_repository.has_overlap(
            table_id=table.id,
            start_at=start_at,
            end_at=end_at,
        )
        if has_overlap:
            raise ConflictError("The table is already booked in the selected time slot.")

        booking = await self.booking_repository.create(
            user_id=user.id,
            table_id=table.id,
            start_at=start_at,
            end_at=end_at,
        )
        booking.table = table
        await self.session.commit()
        await self.table_service.invalidate_available_cache()
        self.notification_service.send_booking_created(
            booking_id=booking.id,
            email=user.email,
            start_at=booking.start_at,
            table_name=table.name,
        )
        return booking

    async def get_my(self, user_id: int) -> list[Booking]:
        now_at = datetime.now(tz=timezone.utc)
        return await self.booking_repository.get_active_or_future_for_user(user_id=user_id, now_at=now_at)

    async def update(self, user_id: int, booking_id: int, payload: BookingUpdateRequest) -> Booking:
        booking = await self.get_owned_booking(user_id=user_id, booking_id=booking_id)
        if booking.is_canceled:
            raise ConflictError("Canceled booking cannot be changed.")

        if not BookingSlotService.can_book_time(payload.date, payload.time):
            raise BusinessRuleError(
                f"Booking is available from {settings.WORKDAY_START_HOUR}:00 "
                f"to {settings.WORKDAY_END_HOUR - settings.BOOKING_SLOT_HOURS}:00."
            )

        start_at, end_at = BookingSlotService.build_slot(payload.date, payload.time)
        if start_at <= datetime.now(tz=timezone.utc):
            raise BusinessRuleError("Booking start must be in the future.")

        has_overlap = await self.booking_repository.has_overlap(
            table_id=booking.table_id,
            start_at=start_at,
            end_at=end_at,
            exclude_booking_id=booking.id,
        )
        if has_overlap:
            raise ConflictError("The table is already booked in the selected time slot.")

        updated = await self.booking_repository.update_slot(
            booking=booking,
            start_at=start_at,
            end_at=end_at,
        )
        await self.session.commit()
        await self.table_service.invalidate_available_cache()
        return updated

    async def cancel(self, user_id: int, booking_id: int) -> Booking:
        booking = await self.get_owned_booking(user_id=user_id, booking_id=booking_id)
        if booking.is_canceled:
            raise ConflictError("Booking was already canceled.")

        now_at = datetime.now(tz=timezone.utc)
        deadline_at = booking.start_at - timedelta(minutes=settings.CANCEL_DEADLINE_MINUTES)
        if now_at > deadline_at:
            raise BusinessRuleError("Booking cancellation is allowed only 1 hour before start.")

        canceled = await self.booking_repository.cancel(booking=booking, canceled_at=now_at)
        await self.session.commit()
        await self.table_service.invalidate_available_cache()
        return canceled

    async def get_owned_booking(self, user_id: int, booking_id: int) -> Booking:
        booking = await self.booking_repository.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking was not found.")
        if booking.user_id != user_id:
            raise AuthorizationError("This booking belongs to another user.")
        return booking
