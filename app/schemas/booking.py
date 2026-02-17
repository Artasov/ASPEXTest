from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.schemas.table import TableResponse


class BookingCreateRequest(BaseModel):
    table_id: int
    date: date
    time: time


class BookingUpdateRequest(BaseModel):
    date: date
    time: time


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_at: datetime
    end_at: datetime
    canceled_at: datetime | None
    created_at: datetime
    table: TableResponse


class BookingsListResponse(BaseModel):
    items: list[BookingResponse]
