from datetime import date, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.table import RestaurantTable
from app.repositories.table import TableRepository
from app.schemas.table import (
    AvailableTablesResponse,
    TableCreateRequest,
    TableResponse,
    TablesListResponse,
    TableUpdateRequest,
)
from app.services.cache import CacheServiceProtocol
from app.services.slot import BookingSlotService


class TableService:
    def __init__(self, session: AsyncSession, cache_service: CacheServiceProtocol):
        self.session = session
        self.table_repository = TableRepository(session)
        self.cache_service = cache_service

    async def get_available(self, slot_date: date, slot_time: time, guests: int) -> AvailableTablesResponse:
        if not BookingSlotService.can_book_time(slot_date, slot_time):
            raise BusinessRuleError(
                f"Booking is available from {settings.WORKDAY_START_HOUR}:00 "
                f"to {settings.WORKDAY_END_HOUR - settings.BOOKING_SLOT_HOURS}:00."
            )
        cache_key = self.get_available_cache_key(slot_date, slot_time, guests)
        cached_tables = await self.cache_service.get_json(cache_key)
        if cached_tables is not None:
            table_models = [TableResponse.model_validate(item) for item in cached_tables]
            return AvailableTablesResponse(
                date=slot_date,
                time=slot_time,
                guests=guests,
                slot_hours=settings.BOOKING_SLOT_HOURS,
                tables=table_models,
            )

        start_at, end_at = BookingSlotService.build_slot(slot_date, slot_time)
        tables = await self.table_repository.list_available(start_at=start_at, end_at=end_at, guests=guests)
        table_models = [TableResponse.model_validate(item) for item in tables]
        await self.cache_service.set_json(
            cache_key,
            [table.model_dump(mode="json") for table in table_models],
            ttl=settings.CACHE_TTL_SECONDS,
        )
        return AvailableTablesResponse(
            date=slot_date,
            time=slot_time,
            guests=guests,
            slot_hours=settings.BOOKING_SLOT_HOURS,
            tables=table_models,
        )

    async def get_list(self) -> TablesListResponse:
        items = await self.table_repository.get_list()
        return TablesListResponse(items=[TableResponse.model_validate(item) for item in items])

    async def create(self, payload: TableCreateRequest) -> TableResponse:
        name = payload.name.strip()
        if await self.table_repository.get_by_name(name) is not None:
            raise ConflictError("Table with this name already exists.")
        table = await self.table_repository.create(name=name, seats=payload.seats)
        await self.session.commit()
        await self.invalidate_available_cache()
        return TableResponse.model_validate(table)

    async def update(self, table_id: int, payload: TableUpdateRequest) -> TableResponse:
        table = await self.table_repository.get_by_id(table_id)
        if table is None:
            raise NotFoundError("Table was not found.")
        name = payload.name.strip()
        table_with_name = await self.table_repository.get_by_name(name)
        if table_with_name is not None and table_with_name.id != table.id:
            raise ConflictError("Table with this name already exists.")

        updated = await self.table_repository.update(table=table, name=name, seats=payload.seats)
        await self.session.commit()
        await self.invalidate_available_cache()
        return TableResponse.model_validate(updated)

    async def delete(self, table_id: int) -> None:
        table = await self.table_repository.get_by_id(table_id)
        if table is None:
            raise NotFoundError("Table was not found.")
        try:
            await self.table_repository.delete(table)
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise ConflictError("Table cannot be deleted while bookings exist.") from error
        await self.invalidate_available_cache()

    @staticmethod
    def generate_default_tables() -> list[RestaurantTable]:
        defaults: list[tuple[int, int]] = [
            (2, settings.TABLES_FOR_2),
            (3, settings.TABLES_FOR_3),
            (6, settings.TABLES_FOR_6),
        ]
        tables: list[RestaurantTable] = []
        for seats, count in defaults:
            for position in range(1, count + 1):
                tables.append(RestaurantTable(name=f"T{seats}-{position}", seats=seats))
        return tables

    @staticmethod
    def get_available_cache_key(slot_date: date, slot_time: time, guests: int) -> str:
        time_chunk = slot_time.strftime("%H:%M")
        return f"tables:available:{slot_date.isoformat()}:{time_chunk}:g{guests}"

    async def invalidate_available_cache(self) -> None:
        await self.cache_service.invalidate_prefix("tables:available:")
