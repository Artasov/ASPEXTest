from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ASPEX Booking API"
    APP_ENV: str = "local"
    APP_DEBUG: bool = False
    API_PREFIX: str = ""
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = Field(default="change-me", min_length=16)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    ADMIN_EMAILS: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:adminadmin@localhost:5432/aspex_booking"
    DATABASE_SYNC_URL: str = "postgresql+psycopg://postgres:adminadmin@localhost:5432/aspex_booking"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    CACHE_TTL_SECONDS: int = 120
    BOOKING_SLOT_HOURS: int = 2
    CANCEL_DEADLINE_MINUTES: int = 60
    WORKDAY_START_HOUR: int = 12
    WORKDAY_END_HOUR: int = 22
    RESTAURANT_TIMEZONE: str = "UTC"

    TABLES_FOR_2: int = 7
    TABLES_FOR_3: int = 6
    TABLES_FOR_6: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


class SettingsProvider:
    _settings: Settings | None = None

    @classmethod
    def get(cls) -> Settings:
        if cls._settings is None:
            cls._settings = Settings()
        return cls._settings


settings = SettingsProvider.get()


class SettingsService:
    @staticmethod
    def get_admin_emails() -> set[str]:
        raw_value = settings.ADMIN_EMAILS.strip()
        if not raw_value:
            return set()
        return {item.strip().lower() for item in raw_value.split(",") if item.strip()}
