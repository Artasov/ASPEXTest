from logging.config import dictConfig

from app.core.config import settings


class LoggingConfigurator:
    @classmethod
    def configure(cls) -> None:
        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "json": {
                        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                        "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
                    },
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "formatter": "json",
                        "stream": "ext://sys.stdout",
                    }
                },
                "root": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["default"],
                },
            }
        )
