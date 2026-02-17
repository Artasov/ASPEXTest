from datetime import datetime

from sqlalchemy import Select, and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.table import RestaurantTable


class TableRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, table_id: int) -> RestaurantTable | None:
        statement = select(RestaurantTable).filter_by(id=table_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> RestaurantTable | None:
        statement = select(RestaurantTable).filter_by(name=name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_list(self) -> list[RestaurantTable]:
        statement: Select[tuple[RestaurantTable]] = (
            select(RestaurantTable).order_by(RestaurantTable.seats.asc(), RestaurantTable.id.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def count(self) -> int:
        statement = select(func.count(RestaurantTable.id))
        result = await self.session.execute(statement)
        return int(result.scalar_one())

    async def add_many(self, tables: list[RestaurantTable]) -> None:
        self.session.add_all(tables)
        await self.session.flush()

    async def create(self, name: str, seats: int) -> RestaurantTable:
        table = RestaurantTable(name=name, seats=seats)
        self.session.add(table)
        await self.session.flush()
        return table

    async def update(self, table: RestaurantTable, name: str, seats: int) -> RestaurantTable:
        table.name = name
        table.seats = seats
        await self.session.flush()
        return table

    async def delete(self, table: RestaurantTable) -> None:
        await self.session.delete(table)
        await self.session.flush()

    async def list_available(
            self,
            start_at: datetime,
            end_at: datetime,
            guests: int,
    ) -> list[RestaurantTable]:
        overlap_exists = exists(
            select(1).where(
                and_(
                    Booking.table_id == RestaurantTable.id,
                    Booking.canceled_at.is_(None),
                    Booking.start_at < end_at,
                    Booking.end_at > start_at,
                )
            )
        )
        statement: Select[tuple[RestaurantTable]] = (
            select(RestaurantTable)
            .where(RestaurantTable.seats >= guests)
            .where(~overlap_exists)
            .order_by(RestaurantTable.seats.asc(), RestaurantTable.id.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
