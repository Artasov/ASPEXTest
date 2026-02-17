from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError


class SecurityService:
    _pwd_context = CryptContext(schemes=("bcrypt",), deprecated="auto")

    @classmethod
    def hash_password(cls, password: str) -> str:
        return cls._pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls._pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def create_access_token(cls, subject: str, expires_minutes: int | None = None) -> str:
        expire_minutes = expires_minutes or settings.JWT_EXPIRE_MINUTES
        expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=expire_minutes)
        payload: dict[str, Any] = {"sub": subject, "exp": expires_at}
        jwt_module = import_module("jose.jwt")
        return jwt_module.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @classmethod
    def decode_access_token(cls, token: str) -> dict[str, Any]:
        jwt_module = import_module("jose.jwt")
        jwt_error = import_module("jose.exceptions").JWTError
        try:
            payload = jwt_module.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt_error as error:
            raise AuthenticationError("Access token is invalid.") from error

        subject = payload.get("sub")
        if subject is None:
            raise AuthenticationError("Access token payload is invalid.")

        return payload
