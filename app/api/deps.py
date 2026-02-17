from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.db.session import database_session_manager
from app.models.user import User
from app.services.auth import AuthService
from app.services.cache import CacheService, RedisClientProvider


class SessionDependency:
    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        async with database_session_manager.session_context() as session:
            yield session


class CacheDependency:
    async def __call__(self) -> CacheService:
        return CacheService(RedisClientProvider.get_client())


session_dependency = SessionDependency()
cache_dependency = CacheDependency()


class CurrentUserDependency:
    _bearer = HTTPBearer(auto_error=False)

    async def __call__(
            self,
            credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
            session: Annotated[AsyncSession, Depends(session_dependency)],
    ) -> User:
        if credentials is None:
            raise AuthenticationError("Authorization header is missing.")
        auth_service = AuthService(session)
        return await auth_service.get_user_from_token(credentials.credentials)


current_user_dependency = CurrentUserDependency()


class AdminUserDependency:
    async def __call__(self, current_user: Annotated[User, Depends(current_user_dependency)]) -> User:
        if current_user.has_role(User.ROLE_ADMIN):
            return current_user
        raise AuthorizationError("Admin role is required.")


admin_user_dependency = AdminUserDependency()

SessionDep = Annotated[AsyncSession, Depends(session_dependency)]
CacheDep = Annotated[CacheService, Depends(cache_dependency)]
CurrentUserDep = Annotated[User, Depends(current_user_dependency)]
AdminUserDep = Annotated[User, Depends(admin_user_dependency)]
