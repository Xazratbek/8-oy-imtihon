from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.analytics.repository import AnalyticsRepository
from app.common.exceptions import ForbiddenError


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)

    async def require_owner_or_admin(self, school_id: UUID, user_id: UUID) -> None:
        if not await self.repo.get_owner_or_admin(school_id, user_id):
            raise ForbiddenError("Owner/admin access kerak")

    async def dashboard(self, school_id: UUID, user_id: UUID, from_: datetime | None = None, to: datetime | None = None) -> dict:
        await self.require_owner_or_admin(school_id, user_id)
        return await self.repo.dashboard(school_id, from_, to)

