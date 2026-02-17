from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int, code: str):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, code="auth_error")


class AuthorizationError(AppException):
    def __init__(self, message: str = "Not enough permissions."):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, code="forbidden")


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource was not found."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, code="not_found")


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict detected."):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, code="conflict")


class BusinessRuleError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="business_rule_error",
        )


class ExceptionConfigurator:
    @staticmethod
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        payload = {"detail": exc.message, "error_code": exc.code}
        return JSONResponse(status_code=exc.status_code, content=payload)

    @staticmethod
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = {"detail": "Validation error.", "error_code": "validation_error", "errors": exc.errors()}
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @staticmethod
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        payload = {"detail": str(exc.detail), "error_code": "http_error"}
        return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)

    @staticmethod
    async def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        payload: dict[str, Any] = {
            "detail": "Unexpected server error.",
            "error_code": "unexpected_error",
            "exception_type": exc.__class__.__name__,
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

    @classmethod
    def register(cls, app: FastAPI) -> None:
        app.add_exception_handler(AppException, cls.app_exception_handler)
        app.add_exception_handler(RequestValidationError, cls.validation_exception_handler)
        app.add_exception_handler(HTTPException, cls.http_exception_handler)
        app.add_exception_handler(Exception, cls.unexpected_exception_handler)
