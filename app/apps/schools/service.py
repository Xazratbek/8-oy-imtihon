from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.schools.repository import SchoolRepository
from app.apps.schools.schemas import MemberCreate, MemberUpdate, SchoolCreate, SchoolUpdate
from app.common.exceptions import ConflictError, NotFoundError
from app.common.schemas import Pagination


class SchoolService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SchoolRepository(db)

    async def create_school(self, payload: SchoolCreate, user_id: UUID):
        if await self.repo.get_by_slug(payload.slug):
            raise ConflictError("Slug band")
        school = await self.repo.create_school(**payload.model_dump())
        self.repo.add_member(school.id, user_id, "owner")
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def list_schools(self, user_id: UUID, page: Pagination):
        return await self.repo.list_user_schools(user_id, page)

    async def get_school(self, school_id: UUID):
        school = await self.repo.get_school(school_id)
        if not school:
            raise NotFoundError("School topilmadi")
        return school

    async def update_school(self, school_id: UUID, payload: SchoolUpdate):
        school = await self.get_school(school_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(school, key, value)
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def list_members(self, school_id: UUID):
        return await self.repo.list_members(school_id)

    async def add_member(self, school_id: UUID, payload: MemberCreate):
        if not await self.repo.get_user(payload.user_id):
            raise NotFoundError("User topilmadi")
        if await self.repo.get_member_by_user(school_id, payload.user_id):
            raise ConflictError("User allaqachon member")
        member = self.repo.add_member(school_id, payload.user_id, payload.role)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def update_member(self, school_id: UUID, member_id: UUID, payload: MemberUpdate):
        member = await self.repo.get_member(member_id)
        if not member or member.school_id != school_id:
            raise NotFoundError("Member topilmadi")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(member, key, value)
        await self.db.commit()
        await self.db.refresh(member)
        return member

