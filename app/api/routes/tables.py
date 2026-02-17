from datetime import date, time

from fastapi import APIRouter, Query

from app.api.deps import CacheDep, CurrentUserDep, SessionDep
from app.schemas.table import AvailableTablesResponse
from app.services.table import TableService

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.get("/available", response_model=AvailableTablesResponse)
async def get_available_tables(
        _current_user: CurrentUserDep,
        session: SessionDep,
        cache_service: CacheDep,
        slot_date: date = Query(alias="date"),
        slot_time: time = Query(alias="time"),
        guests: int = Query(default=1, ge=1, le=20),
) -> AvailableTablesResponse:
    table_service = TableService(session, cache_service)
    return await table_service.get_available(slot_date=slot_date, slot_time=slot_time, guests=guests)
