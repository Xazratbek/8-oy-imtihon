from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_course_staff_member
from app.apps.auth.models import User
from app.apps.courses.models import Category, Course, CourseModule, Lesson, LessonBlock
from app.apps.courses.schemas import (
    BlockCreate,
    BlockOut,
    CategoryCreate,
    CategoryOut,
    CourseCreate,
    CourseOut,
    CourseUpdate,
    LessonCreate,
    LessonOut,
    ModuleCreate,
    ModuleOut,
)
from app.apps.courses.service import CourseService
from app.apps.schools.models import SchoolMember
from app.common.deps import pagination
from app.common.schemas import Pagination
from app.db.session import get_db

router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    return CourseService(db)


@router.post("/categories", response_model=CategoryOut, summary="Category yaratish")
async def create_category(
    payload: CategoryCreate,
    school_id: UUID,
    user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
) -> Category:
    return await service.create_category(payload, school_id, user.id)


@router.post("", response_model=CourseOut, summary="Draft course yaratish")
async def create_course(
    payload: CourseCreate,
    user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
) -> Course:
    return await service.create_course(payload, user.id)


@router.get("", response_model=list[CourseOut], summary="Staff course list")
async def list_courses(
    school_id: UUID,
    user: User = Depends(get_current_user),
    page: Pagination = Depends(pagination),
    service: CourseService = Depends(get_course_service),
) -> list[Course]:
    return await service.list_courses(school_id, user.id, page)


@router.get("/{course_id}", response_model=CourseOut, summary="Course detail")
async def get_course(
    course_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Course:
    return await service.get_course(course_id)


@router.get("/{course_id}/tree", summary="Course module/lesson/block daraxti")
async def course_tree(
    course_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> dict:
    return await service.course_tree(course_id)


@router.patch("/{course_id}", response_model=CourseOut, summary="Course yangilash")
async def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Course:
    return await service.update_course(course_id, payload)


@router.post("/{course_id}/archive", response_model=CourseOut, summary="Course archive")
async def archive_course(
    course_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Course:
    return await service.archive_course(course_id)


@router.delete("/{course_id}", summary="Course delete")
async def delete_course(
    course_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> dict:
    return await service.delete_course(course_id)


@router.post("/{course_id}/modules", response_model=ModuleOut, summary="Module yaratish")
async def create_module(
    course_id: UUID,
    payload: ModuleCreate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> CourseModule:
    return await service.create_module(course_id, payload)


@router.patch("/{course_id}/modules/{module_id}", response_model=ModuleOut, summary="Module update/reorder")
async def update_module(
    course_id: UUID,
    module_id: UUID,
    payload: ModuleCreate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> CourseModule:
    return await service.update_module(course_id, module_id, payload)


@router.delete("/{course_id}/modules/{module_id}", summary="Module delete")
async def delete_module(
    course_id: UUID,
    module_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> dict:
    return await service.delete_module(course_id, module_id)


@router.post("/{course_id}/modules/{module_id}/lessons", response_model=LessonOut, summary="Lesson yaratish")
async def create_lesson(
    course_id: UUID,
    module_id: UUID,
    payload: LessonCreate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Lesson:
    return await service.create_lesson(course_id, module_id, payload)


@router.patch("/{course_id}/lessons/{lesson_id}", response_model=LessonOut, summary="Lesson update/reorder/publish")
async def update_lesson(
    course_id: UUID,
    lesson_id: UUID,
    payload: LessonCreate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Lesson:
    return await service.update_lesson(course_id, lesson_id, payload)


@router.delete("/{course_id}/lessons/{lesson_id}", summary="Lesson delete")
async def delete_lesson(
    course_id: UUID,
    lesson_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> dict:
    return await service.delete_lesson(course_id, lesson_id)


@router.post("/{course_id}/lessons/{lesson_id}/blocks", response_model=BlockOut, summary="Lesson block yaratish")
async def create_block(
    course_id: UUID,
    lesson_id: UUID,
    payload: BlockCreate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> LessonBlock:
    return await service.create_block(course_id, lesson_id, payload)


@router.patch("/{course_id}/lessons/{lesson_id}/blocks/{block_id}", response_model=BlockOut, summary="Block update/reorder")
async def update_block(
    course_id: UUID,
    lesson_id: UUID,
    block_id: UUID,
    payload: BlockCreate,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> LessonBlock:
    return await service.update_block(course_id, lesson_id, block_id, payload)


@router.delete("/{course_id}/lessons/{lesson_id}/blocks/{block_id}", summary="Block delete")
async def delete_block(
    course_id: UUID,
    lesson_id: UUID,
    block_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> dict:
    return await service.delete_block(course_id, lesson_id, block_id)


@router.post("/{course_id}/publish", response_model=CourseOut, summary="Course publish")
async def publish_course(
    course_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Course:
    return await service.publish_course(course_id)


@router.post("/{course_id}/unpublish", response_model=CourseOut, summary="Course publicdan olish")
async def unpublish_course(
    course_id: UUID,
    _: SchoolMember = Depends(get_course_staff_member),
    service: CourseService = Depends(get_course_service),
) -> Course:
    return await service.unpublish_course(course_id)

