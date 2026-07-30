from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class ChatChannel(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "chat_channels"

    school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[UUID | None] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    channel_type: Mapped[str] = mapped_column(String(40), default="school_group")
    title: Mapped[str] = mapped_column(String(255))


class ChatMember(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "chat_members"
    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_chat_member"),)

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("chat_channels.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(30), default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ChatMessage(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("chat_channels.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)


class ChatMessageRead(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "chat_message_reads"
    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_chat_read"),)

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("chat_channels.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    last_read_message_id: Mapped[UUID | None] = mapped_column(ForeignKey("chat_messages.id", ondelete="SET NULL"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
