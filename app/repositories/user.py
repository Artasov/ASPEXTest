from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).filter_by(id=user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).filter_by(email=email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_phone_number(self, phone_number: str) -> User | None:
        statement = select(User).filter_by(phone_number=phone_number)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
            self,
            email: str,
            phone_number: str,
            full_name: str,
            hashed_password: str,
            role: str = User.ROLE_USER,
    ) -> User:
        user = User(
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
        )
        self.session.add(user)
        await self.session.flush()
        return user
