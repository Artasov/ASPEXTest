import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.booking.send_booking_created_notification")
def send_booking_created_notification(
        booking_id: int,
        email: str,
        start_at: str,
        table_name: str,
) -> None:
    logger.info(
        "Booking notification task processed.",
        extra={
            "booking_id": booking_id,
            "email": email,
            "start_at": start_at,
            "table_name": table_name,
        },
    )
