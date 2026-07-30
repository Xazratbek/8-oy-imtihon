from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.auth.models import User
from app.apps.schools.models import School, SchoolMember
from app.common.schemas import Pagination


class SchoolRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_slug(self, slug: str) -> School | None:
        result = await self.db.execute(select(School).where(School.slug == slug))
        return result.scalar_one_or_none()

    async def get_school(self, school_id: UUID) -> School | None:
        return await self.db.get(School, school_id)

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def create_school(self, **data) -> School:
        school = School(**data)
        self.db.add(school)
        await self.db.flush()
        return school

    def add_member(self, school_id: UUID, user_id: UUID, role: str) -> SchoolMember:
        member = SchoolMember(school_id=school_id, user_id=user_id, role=role)
        self.db.add(member)
        return member

    async def list_user_schools(self, user_id: UUID, page: Pagination) -> list[School]:
        result = await self.db.execute(
            select(School)
            .join(SchoolMember, SchoolMember.school_id == School.id)
            .where(SchoolMember.user_id == user_id, SchoolMember.is_active.is_(True))
            .limit(page.limit)
            .offset(page.offset)
        )
        return list(result.scalars())

    async def list_members(self, school_id: UUID) -> list[SchoolMember]:
        result = await self.db.execute(select(SchoolMember).where(SchoolMember.school_id == school_id))
        return list(result.scalars())

    async def get_member(self, member_id: UUID) -> SchoolMember | None:
        return await self.db.get(SchoolMember, member_id)

    async def get_member_by_user(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(select(SchoolMember).where(SchoolMember.school_id == school_id, SchoolMember.user_id == user_id))
        return result.scalar_one_or_none()

