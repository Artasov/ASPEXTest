from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.table import TableRepository
from app.services.table import TableService


class BootstrapService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_repository = TableRepository(session)

    async def bootstrap_tables(self) -> None:
        total_tables = await self.table_repository.count()
        if total_tables > 0:
            return
        self.session.add_all(TableService.generate_default_tables())
        await self.session.commit()
