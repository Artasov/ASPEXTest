from fastapi import APIRouter, status

from app.api.deps import CacheDep, CurrentUserDep, SessionDep
from app.schemas.booking import (
    BookingCreateRequest,
    BookingResponse,
    BookingsListResponse,
    BookingUpdateRequest,
)
from app.services.booking import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
        payload: BookingCreateRequest,
        current_user: CurrentUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> BookingResponse:
    booking_service = BookingService(session, cache_service)
    booking = await booking_service.create(user=current_user, payload=payload)
    return BookingResponse.model_validate(booking)


@router.get("/my", response_model=BookingsListResponse)
async def get_my_bookings(
        current_user: CurrentUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> BookingsListResponse:
    booking_service = BookingService(session, cache_service)
    bookings = await booking_service.get_my(user_id=current_user.id)
    return BookingsListResponse(items=[BookingResponse.model_validate(item) for item in bookings])


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
        booking_id: int,
        payload: BookingUpdateRequest,
        current_user: CurrentUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> BookingResponse:
    booking_service = BookingService(session, cache_service)
    booking = await booking_service.update(
        user_id=current_user.id,
        booking_id=booking_id,
        payload=payload,
    )
    return BookingResponse.model_validate(booking)


@router.delete("/{booking_id}", response_model=BookingResponse)
async def cancel_booking(
        booking_id: int,
        current_user: CurrentUserDep,
        session: SessionDep,
        cache_service: CacheDep,
) -> BookingResponse:
    booking_service = BookingService(session, cache_service)
    booking = await booking_service.cancel(user_id=current_user.id, booking_id=booking_id)
    return BookingResponse.model_validate(booking)
