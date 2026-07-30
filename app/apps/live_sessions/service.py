from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.live_sessions.models import LiveSession
from app.apps.live_sessions.repository import LiveSessionRepository
from app.apps.live_sessions.schemas import LiveSessionCreate
from app.common.exceptions import ForbiddenError, NotFoundError


class LiveSessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LiveSessionRepository(db)

    async def assert_course_staff(self, course_id: UUID, user_id: UUID):
        course = await self.repo.get_course(course_id)
        if not course:
            raise NotFoundError("Course topilmadi")
        if not await self.repo.get_staff(course.school_id, user_id):
            raise ForbiddenError("Staff access kerak")
        return course

    async def assert_live_access(self, course_id: UUID, user_id: UUID):
        course = await self.repo.get_course(course_id)
        if not course:
            raise NotFoundError("Course topilmadi")
        staff = await self.repo.get_staff(course.school_id, user_id)
        enrolled = await self.repo.get_enrollment(course_id, user_id)
        if not staff and not enrolled:
            raise ForbiddenError("Live sessions access yo'q")

    async def create_live(self, payload: LiveSessionCreate, user_id: UUID) -> LiveSession:
        await self.assert_course_staff(payload.course_id, user_id)
        session = self.repo.add(LiveSession(**payload.model_dump(), host_id=user_id, status="scheduled"))
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def list_live(self, course_id: UUID, user_id: UUID) -> list[LiveSession]:
        await self.assert_live_access(course_id, user_id)
        return await self.repo.list_live(course_id)

    async def join_live(self, session_id: UUID, user_id: UUID) -> dict:
        session = await self.repo.get_session(session_id)
        if not session:
            raise NotFoundError("Live session topilmadi")
        await self.assert_live_access(session.course_id, user_id)
        return {"room_url": session.room_url, "provider": session.provider, "status": session.status}

    async def finish_live(self, session_id: UUID, user_id: UUID) -> LiveSession:
        session = await self.repo.get_session(session_id)
        if not session:
            raise NotFoundError("Live session topilmadi")
        await self.assert_course_staff(session.course_id, user_id)
        session.status = "finished"
        await self.db.commit()
        await self.db.refresh(session)
        return session

