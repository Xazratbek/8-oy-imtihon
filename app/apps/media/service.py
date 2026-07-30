from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.media.models import VideoAsset
from app.apps.media.repository import MediaRepository
from app.apps.media.schemas import VideoInitRequest
from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.storage import R2StorageService
from app.services.video import VimeoService


class MediaService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MediaRepository(db)

    async def require_school_member(self, school_id: UUID, user_id: UUID) -> None:
        if not await self.repo.get_member(school_id, user_id):
            raise ForbiddenError("Bu schoolga access yo'q")

    async def init_vimeo_video(self, payload: VideoInitRequest, user_id: UUID) -> VideoAsset:
        await self.require_school_member(payload.school_id, user_id)
        data = await VimeoService().init_upload(payload.title, payload.file_size)
        asset = self.repo.add(
            VideoAsset(
                school_id=payload.school_id,
                provider="vimeo",
                provider_video_id=data.get("provider_video_id"),
                title=payload.title,
                status=data.get("status", "processing"),
                player_url=data.get("player_url"),
                embed_url=data.get("embed_url"),
                raw=data.get("raw", {}),
            )
        )
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def video_status(self, video_id: UUID, school_id: UUID) -> VideoAsset:
        asset = await self.repo.get_asset(video_id)
        if not asset or asset.school_id != school_id:
            raise NotFoundError("Video topilmadi")
        if asset.provider_video_id:
            data = await VimeoService().get_status(asset.provider_video_id)
            for key in ("status", "duration_seconds", "thumbnail_url", "player_url", "embed_url", "raw"):
                if key in data:
                    setattr(asset, key, data[key])
            await self.db.commit()
            await self.db.refresh(asset)
        return asset

    def r2_presign(self, school_id: UUID, key: str, content_type: str) -> dict:
        return R2StorageService().presigned_upload_url(f"{school_id}/{key}", content_type)

    async def r2_upload(self, school_id: UUID, course_id: UUID, lesson_id: UUID, file: UploadFile, user_id: UUID) -> dict:
        await self.require_school_member(school_id, user_id)
        course = await self.repo.get_course(course_id)
        if not course or course.school_id != school_id:
            raise NotFoundError("Course topilmadi")
        lesson = await self.repo.get_lesson(lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise NotFoundError("Lesson topilmadi")
        content = await file.read()
        if not content:
            raise ConflictError("Fayl bo'sh")
        content_type = file.content_type or "application/octet-stream"
        safe_name = "".join(character if character.isalnum() or character in (".", "-", "_") else "-" for character in (file.filename or "file")).strip("-") or "file"
        key = f"{school_id}/courses/{course_id}/{lesson_id}/{safe_name}"
        uploaded = R2StorageService().upload_bytes(key, content, content_type)
        if uploaded.get("note"):
            raise ConflictError(uploaded["note"])
        block = self.repo.add_block(
            lesson_id,
            "video" if content_type.startswith("video/") else "file",
            lesson.title,
            file.filename or "",
            uploaded.get("public_url") or uploaded.get("key"),
        )
        await self.db.commit()
        await self.db.refresh(block)
        return {"block_id": str(block.id), "file_url": block.file_url, "filename": file.filename, "content_type": content_type}

