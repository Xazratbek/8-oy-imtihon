from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.repository import CourseRepository
from app.apps.courses.schemas import (
    BlockCreate,
    BlockOut,
    CategoryCreate,
    CourseCreate,
    CourseOut,
    CourseUpdate,
    LessonCreate,
    LessonOut,
    ModuleCreate,
    ModuleOut,
)
from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.common.schemas import Pagination


class CourseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CourseRepository(db)

    async def assert_school_staff(self, school_id: UUID, user_id: UUID):
        member = await self.repo.get_staff_member(school_id, user_id)
        if not member:
            raise ForbiddenError("School staff access kerak")
        return member

    async def create_category(self, payload: CategoryCreate, school_id: UUID, user_id: UUID):
        await self.assert_school_staff(school_id, user_id)
        if await self.repo.category_by_slug(school_id, payload.slug):
            raise ConflictError("Category slug band")
        category = self.repo.create_category(school_id, **payload.model_dump())
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def create_course(self, payload: CourseCreate, user_id: UUID):
        await self.assert_school_staff(payload.school_id, user_id)
        if await self.repo.course_by_slug(payload.school_id, payload.slug):
            raise ConflictError("Course slug band")
        course = await self.repo.create_course(user_id, **payload.model_dump())
        await self.repo.create_course_chat(course, user_id)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def list_courses(self, school_id: UUID, user_id: UUID, page: Pagination):
        await self.assert_school_staff(school_id, user_id)
        return await self.repo.list_courses(school_id, page)

    async def get_course(self, course_id: UUID):
        course = await self.repo.get_course(course_id)
        if not course:
            raise NotFoundError("Course topilmadi")
        return course

    async def course_tree(self, course_id: UUID) -> dict:
        course = await self.get_course(course_id)
        modules = await self.repo.list_modules(course_id)
        lessons = await self.repo.list_lessons(course_id)
        blocks = await self.repo.list_blocks(course_id)
        return {
            "course": CourseOut.model_validate(course).model_dump(mode="json"),
            "modules": [
                {
                    **ModuleOut.model_validate(module).model_dump(mode="json"),
                    "lessons": [
                        {
                            **LessonOut.model_validate(lesson).model_dump(mode="json"),
                            "blocks": [
                                BlockOut.model_validate(block).model_dump(mode="json")
                                for block in blocks
                                if block.lesson_id == lesson.id
                            ],
                        }
                        for lesson in lessons
                        if lesson.module_id == module.id
                    ],
                }
                for module in modules
            ],
        }

    async def update_course(self, course_id: UUID, payload: CourseUpdate):
        course = await self.get_course(course_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(course, key, value)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def archive_course(self, course_id: UUID):
        course = await self.get_course(course_id)
        course.status = "archived"
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def delete_course(self, course_id: UUID) -> dict:
        course = await self.get_course(course_id)
        await self.repo.delete(course)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"deleted": True}}

    async def create_module(self, course_id: UUID, payload: ModuleCreate):
        module = self.repo.create_module(course_id, **payload.model_dump())
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def update_module(self, course_id: UUID, module_id: UUID, payload: ModuleCreate):
        module = await self.repo.get_module(module_id)
        if not module or module.course_id != course_id:
            raise NotFoundError("Module topilmadi")
        for key, value in payload.model_dump().items():
            setattr(module, key, value)
        await self.db.commit()
        await self.db.refresh(module)
        return module

    async def delete_module(self, course_id: UUID, module_id: UUID) -> dict:
        module = await self.repo.get_module(module_id)
        if not module or module.course_id != course_id:
            raise NotFoundError("Module topilmadi")
        await self.repo.delete(module)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"deleted": True}}

    async def create_lesson(self, course_id: UUID, module_id: UUID, payload: LessonCreate):
        module = await self.repo.get_module(module_id)
        if not module or module.course_id != course_id:
            raise NotFoundError("Module topilmadi")
        lesson = self.repo.create_lesson(course_id, module_id, **payload.model_dump())
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def update_lesson(self, course_id: UUID, lesson_id: UUID, payload: LessonCreate):
        lesson = await self.repo.get_lesson(lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise NotFoundError("Lesson topilmadi")
        for key, value in payload.model_dump().items():
            setattr(lesson, key, value)
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def delete_lesson(self, course_id: UUID, lesson_id: UUID) -> dict:
        lesson = await self.repo.get_lesson(lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise NotFoundError("Lesson topilmadi")
        await self.repo.delete(lesson)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"deleted": True}}

    async def create_block(self, course_id: UUID, lesson_id: UUID, payload: BlockCreate):
        lesson = await self.repo.get_lesson(lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise NotFoundError("Lesson topilmadi")
        block = self.repo.create_block(lesson_id, **payload.model_dump())
        await self.db.commit()
        await self.db.refresh(block)
        return block

    async def update_block(self, course_id: UUID, lesson_id: UUID, block_id: UUID, payload: BlockCreate):
        lesson = await self.repo.get_lesson(lesson_id)
        block = await self.repo.get_block(block_id)
        if not lesson or lesson.course_id != course_id or not block or block.lesson_id != lesson_id:
            raise NotFoundError("Block topilmadi")
        for key, value in payload.model_dump().items():
            setattr(block, key, value)
        await self.db.commit()
        await self.db.refresh(block)
        return block

    async def delete_block(self, course_id: UUID, lesson_id: UUID, block_id: UUID) -> dict:
        lesson = await self.repo.get_lesson(lesson_id)
        block = await self.repo.get_block(block_id)
        if not lesson or lesson.course_id != course_id or not block or block.lesson_id != lesson_id:
            raise NotFoundError("Block topilmadi")
        await self.repo.delete(block)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"deleted": True}}

    async def publish_course(self, course_id: UUID):
        course = await self.get_course(course_id)
        if not await self.repo.count_modules(course_id) or not await self.repo.count_published_lessons(course_id):
            raise ConflictError("Publish uchun kamida 1 module va 1 published lesson kerak")
        course.status = "published"
        course.published_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def unpublish_course(self, course_id: UUID):
        course = await self.get_course(course_id)
        course.status = "draft"
        course.published_at = None
        await self.db.commit()
        await self.db.refresh(course)
        return course

