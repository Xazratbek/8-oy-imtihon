from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles, require_school_member
from app.apps.auth.models import User
from app.apps.schools.models import School, SchoolMember
from app.apps.schools.schemas import MemberCreate, MemberOut, MemberUpdate, SchoolCreate, SchoolOut, SchoolUpdate
from app.apps.schools.service import SchoolService
from app.common.deps import pagination
from app.common.schemas import Pagination
from app.db.session import get_db

router = APIRouter(prefix="/schools", tags=["Schools"])


def get_school_service(db: AsyncSession = Depends(get_db)) -> SchoolService:
    return SchoolService(db)


@router.post("", response_model=SchoolOut, summary="School yaratish")
async def create_school(
    payload: SchoolCreate,
    user: User = Depends(get_current_user),
    service: SchoolService = Depends(get_school_service),
) -> School:
    return await service.create_school(payload, user.id)


@router.get("", response_model=list[SchoolOut], summary="User schoollari")
async def list_schools(
    user: User = Depends(get_current_user),
    page: Pagination = Depends(pagination),
    service: SchoolService = Depends(get_school_service),
) -> list[School]:
    return await service.list_schools(user.id, page)


@router.get("/{school_id}", response_model=SchoolOut, summary="School detail")
async def get_school(
    school_id: UUID,
    _: SchoolMember = Depends(require_school_member),
    service: SchoolService = Depends(get_school_service),
) -> School:
    return await service.get_school(school_id)


@router.patch("/{school_id}", response_model=SchoolOut, summary="School sozlamalarini yangilash")
async def update_school(
    school_id: UUID,
    payload: SchoolUpdate,
    _: SchoolMember = Depends(require_roles("owner", "admin")),
    service: SchoolService = Depends(get_school_service),
) -> School:
    return await service.update_school(school_id, payload)


@router.get("/{school_id}/members", response_model=list[MemberOut], summary="School memberlari")
async def list_members(
    school_id: UUID,
    _: SchoolMember = Depends(require_roles("owner", "admin")),
    service: SchoolService = Depends(get_school_service),
) -> list[SchoolMember]:
    return await service.list_members(school_id)


@router.post("/{school_id}/members", response_model=MemberOut, summary="Member qo'shish")
async def add_member(
    school_id: UUID,
    payload: MemberCreate,
    _: SchoolMember = Depends(require_roles("owner", "admin")),
    service: SchoolService = Depends(get_school_service),
) -> SchoolMember:
    return await service.add_member(school_id, payload)


@router.patch("/{school_id}/members/{member_id}", response_model=MemberOut, summary="Member role/status yangilash")
async def update_member(
    school_id: UUID,
    member_id: UUID,
    payload: MemberUpdate,
    _: SchoolMember = Depends(require_roles("owner", "admin")),
    service: SchoolService = Depends(get_school_service),
) -> SchoolMember:
    return await service.update_member(school_id, member_id, payload)

