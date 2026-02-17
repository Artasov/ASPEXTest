from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


class BookingSlotService:
    @classmethod
    def get_restaurant_timezone(cls) -> ZoneInfo:
        return ZoneInfo(settings.RESTAURANT_TIMEZONE)

    @classmethod
    def get_normalized_time(cls, slot_time: time) -> time:
        return slot_time.replace(tzinfo=None)

    @classmethod
    def get_restaurant_datetime(cls, slot_date: date, slot_time: time) -> datetime:
        restaurant_timezone = cls.get_restaurant_timezone()
        normalized_time = cls.get_normalized_time(slot_time)
        if slot_time.tzinfo is None:
            return datetime.combine(slot_date, normalized_time, tzinfo=restaurant_timezone)
        source_datetime = datetime.combine(slot_date, normalized_time, tzinfo=slot_time.tzinfo)
        return source_datetime.astimezone(restaurant_timezone)

    @classmethod
    def build_slot(cls, slot_date: date, slot_time: time) -> tuple[datetime, datetime]:
        restaurant_start = cls.get_restaurant_datetime(slot_date, slot_time)
        restaurant_end = restaurant_start + timedelta(hours=settings.BOOKING_SLOT_HOURS)
        return restaurant_start.astimezone(timezone.utc), restaurant_end.astimezone(timezone.utc)

    @classmethod
    def can_book_time(cls, slot_date: date, slot_time: time) -> bool:
        restaurant_timezone = cls.get_restaurant_timezone()
        restaurant_start = cls.get_restaurant_datetime(slot_date, slot_time)
        workday_start = datetime.combine(
            restaurant_start.date(),
            time(hour=settings.WORKDAY_START_HOUR),
            tzinfo=restaurant_timezone,
        )
        workday_end = datetime.combine(
            restaurant_start.date(),
            time(hour=settings.WORKDAY_END_HOUR),
            tzinfo=restaurant_timezone,
        )
        latest_start = workday_end - timedelta(hours=settings.BOOKING_SLOT_HOURS)
        return workday_start <= restaurant_start <= latest_start
