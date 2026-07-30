import httpx

from app.core.config import settings


class VimeoService:
    async def init_upload(self, title: str, file_size: int | None = None) -> dict:
        if not settings.vimeo_access_token:
            return {
                "provider_video_id": None,
                "status": "processing",
                "player_url": None,
                "embed_url": None,
                "raw": {"note": "VIMEO_ACCESS_TOKEN sozlanmagan, local metadata yaratildi"},
            }
        payload: dict = {"name": title, "privacy": {"view": "disable"}}
        if file_size:
            payload["upload"] = {"approach": "tus", "size": file_size}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                settings.vimeo_upload_url,
                headers={"Authorization": f"Bearer {settings.vimeo_access_token}"},
                json=payload,
            )
            if response.status_code == 401:
                return {
                    "provider_video_id": None,
                    "status": "error",
                    "player_url": None,
                    "embed_url": None,
                    "raw": {"error": "Vimeo token yaroqsiz yoki upload scope yo'q"},
                }
            response.raise_for_status()
            data = response.json()
        video_id = data.get("uri", "").rstrip("/").split("/")[-1] or None
        return {
            "provider_video_id": video_id,
            "status": "processing",
            "player_url": data.get("link"),
            "embed_url": data.get("player_embed_url"),
            "raw": data,
        }

    async def get_status(self, provider_video_id: str) -> dict:
        if not settings.vimeo_access_token:
            return {"status": "processing", "raw": {"note": "VIMEO_ACCESS_TOKEN sozlanmagan"}}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://api.vimeo.com/videos/{provider_video_id}",
                headers={"Authorization": f"Bearer {settings.vimeo_access_token}"},
            )
            if response.status_code == 401:
                return {"status": "error", "raw": {"error": "Vimeo token yaroqsiz yoki video read scope yo'q"}}
            response.raise_for_status()
            data = response.json()
        transcode = data.get("transcode", {}).get("status")
        status = "ready" if transcode == "complete" else "error" if transcode == "error" else "processing"
        return {
            "status": status,
            "duration_seconds": data.get("duration") or 0,
            "thumbnail_url": (data.get("pictures", {}).get("sizes") or [{}])[-1].get("link"),
            "player_url": data.get("link"),
            "embed_url": data.get("player_embed_url"),
            "raw": data,
        }
