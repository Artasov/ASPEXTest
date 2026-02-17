from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.booking import BookingCreateRequest, BookingResponse, BookingUpdateRequest
from app.schemas.table import (
    AvailableTablesResponse,
    TableCreateRequest,
    TableResponse,
    TablesListResponse,
    TableUpdateRequest,
)

__all__ = (
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "BookingCreateRequest",
    "BookingResponse",
    "BookingUpdateRequest",
    "AvailableTablesResponse",
    "TableCreateRequest",
    "TableResponse",
    "TableUpdateRequest",
    "TablesListResponse",
)
