from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.messenger.models import ChatChannel, ChatMember, ChatMessage, ChatMessageRead
from app.common.schemas import Pagination


class MessengerRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_chat_member(self, channel_id: UUID, user_id: UUID) -> ChatMember | None:
        result = await self.db.execute(
            select(ChatMember).where(ChatMember.channel_id == channel_id, ChatMember.user_id == user_id, ChatMember.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def list_chats(self, user_id: UUID) -> list[ChatChannel]:
        result = await self.db.execute(select(ChatChannel).join(ChatMember, ChatMember.channel_id == ChatChannel.id).where(ChatMember.user_id == user_id))
        return list(result.scalars())

    async def list_messages(self, channel_id: UUID, page: Pagination) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.channel_id == channel_id).order_by(ChatMessage.created_at.desc()).limit(page.limit).offset(page.offset)
        )
        return list(result.scalars())

    async def latest_message(self, channel_id: UUID) -> ChatMessage | None:
        result = await self.db.execute(select(ChatMessage).where(ChatMessage.channel_id == channel_id).order_by(ChatMessage.created_at.desc()))
        return result.scalar_one_or_none()

    async def get_read_marker(self, channel_id: UUID, user_id: UUID) -> ChatMessageRead | None:
        result = await self.db.execute(select(ChatMessageRead).where(ChatMessageRead.channel_id == channel_id, ChatMessageRead.user_id == user_id))
        return result.scalar_one_or_none()

    def add(self, entity):
        self.db.add(entity)
        return entity

