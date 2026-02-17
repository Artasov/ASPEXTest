from datetime import datetime
from typing import Any

from app.services.cache import CacheServiceProtocol
from app.services.notification import NotificationServiceProtocol


class FakeCacheService(CacheServiceProtocol):
    def __init__(self):
        self.storage: dict[str, Any] = {}
        self.invalidated_prefixes: list[str] = []

    async def get_json(self, key: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        return self.storage.get(key)

    async def set_json(self, key: str, payload: dict[str, Any] | list[dict[str, Any]], ttl: int) -> None:
        self.storage[key] = payload

    async def invalidate_prefix(self, prefix: str) -> None:
        self.invalidated_prefixes.append(prefix)
        keys_to_delete = [item for item in self.storage if item.startswith(prefix)]
        for key in keys_to_delete:
            self.storage.pop(key, None)


class FakeNotificationService(NotificationServiceProtocol):
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def send_booking_created(self, booking_id: int, email: str, start_at: datetime, table_name: str) -> None:
        self.calls.append(
            {
                "booking_id": booking_id,
                "email": email,
                "start_at": start_at,
                "table_name": table_name,
            }
        )
