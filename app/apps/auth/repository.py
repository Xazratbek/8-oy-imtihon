from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.auth.models import OAuthAccount, RefreshToken, User


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def create_user(self, **data) -> User:
        user = User(**data)
        self.db.add(user)
        await self.db.flush()
        return user

    async def create_refresh_token(self, user_id, hashed: str, expires_at: datetime) -> RefreshToken:
        row = RefreshToken(user_id=user_id, token_hash=hashed, expires_at=expires_at)
        self.db.add(row)
        return row

    async def get_refresh_token(self, hashed: str) -> RefreshToken | None:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
        return result.scalar_one_or_none()

    async def get_oauth_account(self, provider: str, provider_user_id: str) -> OAuthAccount | None:
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    def add_oauth_account(self, user_id, provider: str, provider_user_id: str, email: str) -> None:
        self.db.add(OAuthAccount(user_id=user_id, provider=provider, provider_user_id=provider_user_id, email=email))

