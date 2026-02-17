from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class AvailableTablesQuery(BaseModel):
    date: date
    time: time
    guests: int = Field(default=1, ge=1, le=20)


class TableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    seats: int


class TableCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    seats: int = Field(ge=1, le=20)


class TableUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    seats: int = Field(ge=1, le=20)


class TablesListResponse(BaseModel):
    items: list[TableResponse]


class AvailableTablesResponse(BaseModel):
    date: date
    time: time
    guests: int
    slot_hours: int
    tables: list[TableResponse]
