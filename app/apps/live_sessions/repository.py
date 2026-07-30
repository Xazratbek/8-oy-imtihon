from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course
from app.apps.learning.models import Enrollment
from app.apps.live_sessions.models import LiveSession
from app.apps.schools.models import SchoolMember


class LiveSessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_course(self, course_id: UUID) -> Course | None:
        return await self.db.get(Course, course_id)

    async def get_session(self, session_id: UUID) -> LiveSession | None:
        return await self.db.get(LiveSession, session_id)

    async def get_staff(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(
            select(SchoolMember).where(
                SchoolMember.school_id == school_id,
                SchoolMember.user_id == user_id,
                SchoolMember.role.in_(("owner", "admin", "instructor", "curator")),
                SchoolMember.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_enrollment(self, course_id: UUID, user_id: UUID) -> Enrollment | None:
        result = await self.db.execute(select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.user_id == user_id, Enrollment.status == "active"))
        return result.scalar_one_or_none()

    async def list_live(self, course_id: UUID) -> list[LiveSession]:
        result = await self.db.execute(select(LiveSession).where(LiveSession.course_id == course_id))
        return list(result.scalars())

    def add(self, entity):
        self.db.add(entity)
        return entity

