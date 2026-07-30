from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_school_member
from app.apps.auth.models import User
from app.apps.media.models import VideoAsset
from app.apps.media.schemas import VideoAssetOut, VideoInitRequest
from app.apps.media.service import MediaService
from app.apps.schools.models import SchoolMember
from app.db.session import get_db

router = APIRouter(prefix="/media", tags=["Media"])


def get_media_service(db: AsyncSession = Depends(get_db)) -> MediaService:
    return MediaService(db)


@router.post("/videos/vimeo/init", response_model=VideoAssetOut, summary="Vimeo video upload init")
async def init_vimeo_video(
    payload: VideoInitRequest,
    user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> VideoAsset:
    return await service.init_vimeo_video(payload, user.id)


@router.get("/videos/{video_id}", response_model=VideoAssetOut, summary="Video status")
async def video_status(
    video_id: UUID,
    member: SchoolMember = Depends(require_school_member),
    service: MediaService = Depends(get_media_service),
) -> VideoAsset:
    return await service.video_status(video_id, member.school_id)


@router.post("/files/r2/presign", summary="R2 fayl upload URL")
async def r2_presign(
    school_id: UUID,
    key: str = Query(..., description="Masalan covers/course-1.png"),
    content_type: str = Query("application/octet-stream"),
    _: SchoolMember = Depends(require_school_member),
    service: MediaService = Depends(get_media_service),
) -> dict:
    return service.r2_presign(school_id, key, content_type)


@router.post("/files/r2/upload", summary="R2 faylni backend orqali upload qilish")
async def r2_upload(
    school_id: UUID = Form(...),
    course_id: UUID = Form(...),
    lesson_id: UUID = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> dict:
    return await service.r2_upload(school_id, course_id, lesson_id, file, user.id)

