from datetime import datetime
from typing import Protocol

from app.tasks.booking import send_booking_created_notification


class NotificationServiceProtocol(Protocol):
    def send_booking_created(self, booking_id: int, email: str, start_at: datetime, table_name: str) -> None: ...


class NotificationService:
    @staticmethod
    def send_booking_created(booking_id: int, email: str, start_at: datetime, table_name: str) -> None:
        send_booking_created_notification.delay(
            booking_id=booking_id,
            email=email,
            start_at=start_at.isoformat(),
            table_name=table_name,
        )
