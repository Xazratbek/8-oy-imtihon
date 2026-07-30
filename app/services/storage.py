from urllib.parse import quote

import boto3

from app.core.config import settings


class R2StorageService:
    def _client(self):
        endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )

    def presigned_upload_url(self, key: str, content_type: str, expires_in: int = 3600) -> dict:
        if not settings.r2_account_id or not settings.r2_access_key_id or not settings.r2_secret_access_key:
            return {"upload_url": "", "public_url": "", "note": "R2 env sozlanmagan"}
        clean_key = key.lstrip("/")
        upload_url = self._client().generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.r2_bucket, "Key": clean_key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        public_url = f"{settings.r2_public_base_url.rstrip('/')}/{quote(clean_key)}" if settings.r2_public_base_url else ""
        return {"upload_url": upload_url, "public_url": public_url}

    def upload_bytes(self, key: str, content: bytes, content_type: str) -> dict:
        if not settings.r2_account_id or not settings.r2_access_key_id or not settings.r2_secret_access_key:
            return {"public_url": "", "note": "R2 env sozlanmagan"}
        clean_key = key.lstrip("/")
        self._client().put_object(
            Bucket=settings.r2_bucket,
            Key=clean_key,
            Body=content,
            ContentType=content_type,
        )
        public_url = f"{settings.r2_public_base_url.rstrip('/')}/{quote(clean_key)}" if settings.r2_public_base_url else ""
        return {"public_url": public_url, "key": clean_key}
