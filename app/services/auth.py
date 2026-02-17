from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SettingsService, settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import SecurityService
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        exists = await self.user_repository.get_by_email(payload.email)
        if exists is not None:
            raise ConflictError("User with this email already exists.")
        phone_exists = await self.user_repository.get_by_phone_number(payload.phone_number)
        if phone_exists is not None:
            raise ConflictError("User with this phone number already exists.")

        hashed_password = SecurityService.hash_password(payload.password)
        role = User.ROLE_ADMIN if payload.email.lower() in SettingsService.get_admin_emails() else User.ROLE_USER
        user = await self.user_repository.create(
            email=payload.email,
            phone_number=payload.phone_number,
            full_name=payload.full_name,
            hashed_password=hashed_password,
            role=role,
        )
        await self.session.commit()
        return self.create_token_response(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if user is None:
            raise AuthenticationError("Email or password is invalid.")

        is_valid = SecurityService.verify_password(payload.password, user.hashed_password)
        if not is_valid:
            raise AuthenticationError("Email or password is invalid.")

        return self.create_token_response(user)

    async def get_user_from_token(self, access_token: str) -> User:
        token_payload = SecurityService.decode_access_token(access_token)
        try:
            user_id = int(token_payload["sub"])
        except (TypeError, ValueError) as error:
            raise AuthenticationError("Access token payload is invalid.") from error
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("User from access token was not found.")
        return user

    @staticmethod
    def create_token_response(user: User) -> TokenResponse:
        token = SecurityService.create_access_token(subject=str(user.id))
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        )
