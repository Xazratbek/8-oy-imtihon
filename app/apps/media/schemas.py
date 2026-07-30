from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas import ORMModel


class VideoInitRequest(BaseModel):
    school_id: UUID
    title: str
    file_size: int | None = None


class VideoAssetOut(ORMModel):
    id: UUID
    school_id: UUID
    provider: str
    provider_video_id: str | None = None
    title: str
    status: str
    thumbnail_url: str | None = None
    embed_url: str | None = None
    player_url: str | None = None
    raw: dict = Field(default_factory=dict)
