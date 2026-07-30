from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course
from app.apps.courses.schemas import CourseOut
from app.apps.public_catalog.service import PublicCatalogService
from app.common.deps import pagination
from app.common.schemas import Pagination
from app.db.session import get_db

router = APIRouter(prefix="/public/courses", tags=["Public catalog"])


def get_public_catalog_service(db: AsyncSession = Depends(get_db)) -> PublicCatalogService:
    return PublicCatalogService(db)


@router.get("", response_model=list[CourseOut], summary="Published kurslar katalogi")
async def public_courses(
    school_id: UUID,
    page: Pagination = Depends(pagination),
    service: PublicCatalogService = Depends(get_public_catalog_service),
) -> list[Course]:
    return await service.public_courses(school_id, page)

