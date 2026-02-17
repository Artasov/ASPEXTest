from datetime import date, time, timedelta, timezone

from app.services.slot import BookingSlotService


def test_can_book_time_boundaries() -> None:
    slot_date = date(2026, 2, 14)
    assert BookingSlotService.can_book_time(slot_date, time(12, 0))
    assert BookingSlotService.can_book_time(slot_date, time(20, 0))
    assert not BookingSlotService.can_book_time(slot_date, time(11, 59))
    assert not BookingSlotService.can_book_time(slot_date, time(20, 1))


def test_can_book_time_with_timezone_aware_input() -> None:
    slot_date = date(2026, 2, 14)
    assert BookingSlotService.can_book_time(slot_date, time(13, 0, tzinfo=timezone.utc))


def test_build_slot_returns_utc_interval() -> None:
    start_at, end_at = BookingSlotService.build_slot(
        slot_date=date(2026, 2, 14),
        slot_time=time(13, 0, tzinfo=timezone.utc),
    )

    assert start_at.isoformat() == "2026-02-14T13:00:00+00:00"
    assert end_at.isoformat() == "2026-02-14T15:00:00+00:00"


def test_build_slot_converts_aware_offset_to_utc() -> None:
    start_at, end_at = BookingSlotService.build_slot(
        slot_date=date(2026, 2, 14),
        slot_time=time(13, 0, tzinfo=timezone(timedelta(hours=3))),
    )

    assert start_at.isoformat() == "2026-02-14T10:00:00+00:00"
    assert end_at.isoformat() == "2026-02-14T12:00:00+00:00"
