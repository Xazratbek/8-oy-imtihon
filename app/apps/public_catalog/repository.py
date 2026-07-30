from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course
from app.common.schemas import Pagination


class PublicCatalogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def public_courses(self, school_id: UUID, page: Pagination) -> list[Course]:
        result = await self.db.execute(
            select(Course).where(Course.school_id == school_id, Course.status == "published").limit(page.limit).offset(page.offset)
        )
        return list(result.scalars())

