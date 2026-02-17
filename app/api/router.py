from fastapi import APIRouter

from app.api.routes.admin_tables import router as admin_tables_router
from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.tables import router as tables_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tables_router)
api_router.include_router(bookings_router)
api_router.include_router(admin_tables_router)
