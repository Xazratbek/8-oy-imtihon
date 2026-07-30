from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course, Lesson, LessonBlock
from app.apps.media.models import VideoAsset
from app.apps.schools.models import SchoolMember


class MediaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_member(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(select(SchoolMember).where(SchoolMember.school_id == school_id, SchoolMember.user_id == user_id, SchoolMember.is_active.is_(True)))
        return result.scalar_one_or_none()

    async def get_asset(self, video_id: UUID) -> VideoAsset | None:
        return await self.db.get(VideoAsset, video_id)

    async def get_course(self, course_id: UUID) -> Course | None:
        return await self.db.get(Course, course_id)

    async def get_lesson(self, lesson_id: UUID) -> Lesson | None:
        return await self.db.get(Lesson, lesson_id)

    def add(self, entity):
        self.db.add(entity)
        return entity

    def add_block(self, lesson_id: UUID, block_type: str, title: str, content: str, file_url: str) -> LessonBlock:
        return self.add(
            LessonBlock(
                lesson_id=lesson_id,
                block_type=block_type,
                title=title,
                content=content,
                file_url=file_url,
                sort_order=0,
            )
        )

