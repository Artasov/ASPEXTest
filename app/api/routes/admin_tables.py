from fastapi import APIRouter, status

from app.api.deps import AdminUserDep, CacheDep, SessionDep
from app.schemas.table import TableCreateRequest, TableResponse, TablesListResponse, TableUpdateRequest
from app.services.table import TableService

router = APIRouter(prefix="/admin/tables", tags=["Admin Tables"])


@router.get("/", response_model=TablesListResponse)
async def get_tables_list(
        _admin_user: AdminUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> TablesListResponse:
    table_service = TableService(session, cache_service)
    return await table_service.get_list()


@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
        payload: TableCreateRequest,
        _admin_user: AdminUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> TableResponse:
    table_service = TableService(session, cache_service)
    return await table_service.create(payload=payload)


@router.patch("/{table_id}", response_model=TableResponse)
async def update_table(
        table_id: int,
        payload: TableUpdateRequest,
        _admin_user: AdminUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> TableResponse:
    table_service = TableService(session, cache_service)
    return await table_service.update(table_id=table_id, payload=payload)


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
        table_id: int,
        _admin_user: AdminUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> None:
    table_service = TableService(session, cache_service)
    await table_service.delete(table_id=table_id)
