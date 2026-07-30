from datetime import UTC, datetime
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.messenger.models import ChatMessage, ChatMessageRead
from app.apps.messenger.repository import MessengerRepository
from app.common.exceptions import ForbiddenError
from app.common.schemas import Pagination
from app.core.config import settings


class MessengerService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MessengerRepository(db)

    async def assert_chat_member(self, channel_id: UUID, user_id: UUID):
        member = await self.repo.get_chat_member(channel_id, user_id)
        if not member:
            raise ForbiddenError("Chat member emassiz")
        return member

    async def list_chats(self, user_id: UUID):
        return await self.repo.list_chats(user_id)

    async def messages(self, channel_id: UUID, user_id: UUID, page: Pagination):
        await self.assert_chat_member(channel_id, user_id)
        return await self.repo.list_messages(channel_id, page)

    async def send_message(self, channel_id: UUID, user_id: UUID, body: str) -> ChatMessage:
        await self.assert_chat_member(channel_id, user_id)
        message = self.repo.add(ChatMessage(channel_id=channel_id, sender_id=user_id, body=body))
        await self.db.commit()
        await self.db.refresh(message)
        await self.publish_message(channel_id, message.id, user_id, body)
        return message

    async def mark_read(self, channel_id: UUID, user_id: UUID) -> dict:
        await self.assert_chat_member(channel_id, user_id)
        last = await self.repo.latest_message(channel_id)
        row = await self.repo.get_read_marker(channel_id, user_id)
        if not row:
            row = self.repo.add(ChatMessageRead(channel_id=channel_id, user_id=user_id))
        row.last_read_message_id = last.id if last else None
        row.read_at = datetime.now(UTC)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"read": True}}

    async def publish_message(self, channel_id: UUID, message_id: UUID, user_id: UUID, body: str) -> None:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await client.publish(f"chat:{channel_id}", f"{message_id}|{user_id}|{body}")
        finally:
            await client.aclose()

