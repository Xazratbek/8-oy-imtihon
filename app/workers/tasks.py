import asyncio
import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.apps.auth.models import RefreshToken
from app.apps.exports.models import ExportJob
from app.apps.media.models import VideoAsset
from app.db.session import AsyncSessionLocal
from app.services.video import VimeoService
from app.workers.celery_app import celery_app


@celery_app.task
def send_test_email(email: str, subject: str = "Test") -> dict:
    return {"email": email, "subject": subject, "sent": True}


@celery_app.task
def send_payment_notification(invoice_id: str) -> dict:
    return {"invoice_id": invoice_id, "notification": "queued"}


@celery_app.task
def send_password_reset_email(email: str) -> dict:
    return {"email": email, "reset_email": "queued"}


@celery_app.task
def cleanup_expired_refresh_tokens() -> dict:
    async def run() -> dict:
        async with AsyncSessionLocal() as db:
            rows = await db.execute(select(RefreshToken).where(RefreshToken.expires_at < datetime.now(UTC), RefreshToken.revoked_at.is_(None)))
            count = 0
            for token in rows.scalars():
                token.revoked_at = datetime.now(UTC)
                count += 1
            await db.commit()
            return {"revoked": count}

    return asyncio.run(run())


@celery_app.task
def generate_export(job_id: str) -> dict:
    async def run() -> dict:
        async with AsyncSessionLocal() as db:
            job = await db.get(ExportJob, UUID(job_id))
            if not job:
                return {"error": "job not found"}
            job.status = "running"
            await db.commit()
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            path = export_dir / f"{job.id}.{job.file_format}"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["type", "school_id", "created_at"])
                writer.writerow([job.export_type, job.school_id, datetime.now(UTC).isoformat()])
            job.status = "done"
            job.result_url = str(path)
            await db.commit()
            return {"job_id": job_id, "status": "done", "path": str(path)}

    return asyncio.run(run())


@celery_app.task
def poll_vimeo_video(video_asset_id: str) -> dict:
    async def run() -> dict:
        async with AsyncSessionLocal() as db:
            asset = await db.get(VideoAsset, UUID(video_asset_id))
            if not asset or not asset.provider_video_id:
                return {"status": "missing"}
            data = await VimeoService().get_status(asset.provider_video_id)
            for key, value in data.items():
                setattr(asset, key, value)
            await db.commit()
            return {"video_asset_id": video_asset_id, "status": asset.status}

    return asyncio.run(run())
