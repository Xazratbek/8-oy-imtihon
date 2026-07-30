from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Category, Course, CourseModule, Lesson, LessonBlock
from app.apps.messenger.models import ChatChannel, ChatMember
from app.apps.schools.models import SchoolMember
from app.common.schemas import Pagination


class CourseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_staff_member(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(
            select(SchoolMember).where(
                SchoolMember.school_id == school_id,
                SchoolMember.user_id == user_id,
                SchoolMember.is_active.is_(True),
                SchoolMember.role.in_(("owner", "admin", "instructor", "curator")),
            )
        )
        return result.scalar_one_or_none()

    async def category_by_slug(self, school_id: UUID, slug: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.school_id == school_id, Category.slug == slug))
        return result.scalar_one_or_none()

    async def course_by_slug(self, school_id: UUID, slug: str) -> Course | None:
        result = await self.db.execute(select(Course).where(Course.school_id == school_id, Course.slug == slug))
        return result.scalar_one_or_none()

    async def get_course(self, course_id: UUID) -> Course | None:
        return await self.db.get(Course, course_id)

    async def get_module(self, module_id: UUID) -> CourseModule | None:
        return await self.db.get(CourseModule, module_id)

    async def get_lesson(self, lesson_id: UUID) -> Lesson | None:
        return await self.db.get(Lesson, lesson_id)

    async def get_block(self, block_id: UUID) -> LessonBlock | None:
        return await self.db.get(LessonBlock, block_id)

    async def list_courses(self, school_id: UUID, page: Pagination) -> list[Course]:
        result = await self.db.execute(select(Course).where(Course.school_id == school_id).limit(page.limit).offset(page.offset))
        return list(result.scalars())

    async def list_modules(self, course_id: UUID) -> list[CourseModule]:
        result = await self.db.execute(select(CourseModule).where(CourseModule.course_id == course_id).order_by(CourseModule.sort_order))
        return list(result.scalars())

    async def list_lessons(self, course_id: UUID) -> list[Lesson]:
        result = await self.db.execute(select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.sort_order))
        return list(result.scalars())

    async def list_blocks(self, course_id: UUID) -> list[LessonBlock]:
        result = await self.db.execute(
            select(LessonBlock)
            .join(Lesson, LessonBlock.lesson_id == Lesson.id)
            .where(Lesson.course_id == course_id)
            .order_by(LessonBlock.sort_order)
        )
        return list(result.scalars())

    async def count_modules(self, course_id: UUID) -> int:
        return await self.db.scalar(select(func.count(CourseModule.id)).where(CourseModule.course_id == course_id)) or 0

    async def count_published_lessons(self, course_id: UUID) -> int:
        return await self.db.scalar(select(func.count(Lesson.id)).where(Lesson.course_id == course_id, Lesson.status == "published")) or 0

    def create_category(self, school_id: UUID, **data) -> Category:
        category = Category(school_id=school_id, **data)
        self.db.add(category)
        return category

    async def create_course(self, created_by: UUID, **data) -> Course:
        course = Course(**data, created_by=created_by)
        self.db.add(course)
        await self.db.flush()
        return course

    async def create_course_chat(self, course: Course, user_id: UUID) -> None:
        chat = ChatChannel(school_id=course.school_id, course_id=course.id, channel_type="course_group", title=f"{course.title} chat")
        self.db.add(chat)
        await self.db.flush()
        self.db.add(ChatMember(channel_id=chat.id, user_id=user_id, role="moderator"))

    def create_module(self, course_id: UUID, **data) -> CourseModule:
        module = CourseModule(course_id=course_id, **data)
        self.db.add(module)
        return module

    def create_lesson(self, course_id: UUID, module_id: UUID, **data) -> Lesson:
        lesson = Lesson(course_id=course_id, module_id=module_id, **data)
        self.db.add(lesson)
        return lesson

    def create_block(self, lesson_id: UUID, **data) -> LessonBlock:
        block = LessonBlock(lesson_id=lesson_id, **data)
        self.db.add(block)
        return block

    async def delete(self, entity) -> None:
        await self.db.delete(entity)

