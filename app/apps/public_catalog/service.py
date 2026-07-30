from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.public_catalog.repository import PublicCatalogRepository
from app.common.schemas import Pagination


class PublicCatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = PublicCatalogRepository(db)

    async def public_courses(self, school_id: UUID, page: Pagination):
        return await self.repo.public_courses(school_id, page)

