from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ExceptionConfigurator
from app.core.logging import LoggingConfigurator
from app.db.session import database_session_manager
from app.services.bootstrap import BootstrapService
from app.services.cache import RedisClientProvider


class AppFactory:
    @staticmethod
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        LoggingConfigurator.configure()
        async with database_session_manager.session_context() as session:
            await BootstrapService(session).bootstrap_tables()
        yield
        await RedisClientProvider.close()
        await database_session_manager.close()

    @classmethod
    def create_app(cls) -> FastAPI:
        fastapi_app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG, lifespan=cls.lifespan)
        ExceptionConfigurator.register(fastapi_app)
        fastapi_app.include_router(api_router, prefix=settings.API_PREFIX)
        Instrumentator(excluded_handlers=["/metrics"]).instrument(fastapi_app).expose(
            fastapi_app,
            include_in_schema=False,
        )
        return fastapi_app


app = AppFactory.create_app()
