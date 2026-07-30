from uuid import UUID

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class VideoAsset(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "video_assets"

    school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40), default="vimeo")
    provider_video_id: Mapped[str | None] = mapped_column(String(255), index=True)
    project_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="processing")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    embed_url: Mapped[str | None] = mapped_column(String(500))
    player_url: Mapped[str | None] = mapped_column(String(500))
    privacy: Mapped[str] = mapped_column(String(40), default="private")
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
