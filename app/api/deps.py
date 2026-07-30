from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.auth.models import User
from app.apps.courses.models import Course, Lesson
from app.apps.learning.models import Enrollment
from app.apps.schools.models import SchoolMember
from app.common.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = decode_token(token, "access")
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise UnauthorizedError("Token yaroqsiz") from exc
    user = await db.get(User, user_id)
    if not user or user.status != "active":
        raise UnauthorizedError("User topilmadi yoki bloklangan")
    return user


async def require_school_member(school_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> SchoolMember:
    result = await db.execute(
        select(SchoolMember).where(
            SchoolMember.school_id == school_id,
            SchoolMember.user_id == user.id,
            SchoolMember.is_active.is_(True),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ForbiddenError("Bu schoolga access yo'q")
    return member


def require_roles(*roles: str):
    async def checker(member: SchoolMember = Depends(require_school_member)) -> SchoolMember:
        if member.role not in roles:
            raise ForbiddenError("Bu amal uchun role yetarli emas")
        return member

    return checker


async def require_course_access(
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise NotFoundError("Lesson topilmadi")
    if lesson.is_preview:
        return lesson
    enrollment = await db.execute(
        select(Enrollment).where(
            Enrollment.course_id == lesson.course_id,
            Enrollment.user_id == user.id,
            Enrollment.status == "active",
        )
    )
    if not enrollment.scalar_one_or_none():
        raise ForbiddenError("Kursga yozilmagansiz")
    return lesson


async def get_course_staff_member(
    course_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SchoolMember:
    course = await db.get(Course, course_id)
    if not course:
        raise NotFoundError("Course topilmadi")
    result = await db.execute(
        select(SchoolMember).where(
            SchoolMember.school_id == course.school_id,
            SchoolMember.user_id == user.id,
            SchoolMember.is_active.is_(True),
            SchoolMember.role.in_(("owner", "admin", "instructor", "curator")),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ForbiddenError("Course staff access kerak")
    return member
