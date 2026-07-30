import asyncio
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.deps import pagination
from app.common.exceptions import ForbiddenError
from app.common.schemas import Pagination
from app.core.config import settings
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal, get_db
from app.apps.auth.models import User
from app.apps.messenger.models import ChatChannel, ChatMessage
from app.apps.messenger.schemas import ChatOut, MessageCreate, MessageOut
from app.apps.messenger.service import MessengerService

router = APIRouter(prefix="/chats", tags=["Messenger"])
ws_router = APIRouter(tags=["Messenger"])


def get_messenger_service(db: AsyncSession = Depends(get_db)) -> MessengerService:
    return MessengerService(db)


@router.get("", response_model=list[ChatOut], summary="Mening chatlarim")
async def list_chats(user: User = Depends(get_current_user), service: MessengerService = Depends(get_messenger_service)) -> list[ChatChannel]:
    return await service.list_chats(user.id)


@router.get("/{channel_id}/messages", response_model=list[MessageOut], summary="Message history")
async def messages(
    channel_id: UUID,
    user: User = Depends(get_current_user),
    page: Pagination = Depends(pagination),
    service: MessengerService = Depends(get_messenger_service),
) -> list[ChatMessage]:
    return await service.messages(channel_id, user.id, page)


@router.post("/{channel_id}/messages", response_model=MessageOut, summary="Message yuborish")
async def send_message(
    channel_id: UUID,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    service: MessengerService = Depends(get_messenger_service),
) -> ChatMessage:
    return await service.send_message(channel_id, user.id, payload.body)


@router.post("/{channel_id}/read", summary="Read marker")
async def mark_read(channel_id: UUID, user: User = Depends(get_current_user), service: MessengerService = Depends(get_messenger_service)) -> dict:
    return await service.mark_read(channel_id, user.id)


@ws_router.websocket("/ws/chats/{channel_id}")
async def chat_ws(websocket: WebSocket, channel_id: UUID, token: str) -> None:
    await websocket.accept()
    try:
        payload = decode_token(token, "access")
        user_id = UUID(payload["sub"])
    except Exception:
        await websocket.close(code=1008)
        return
    async with AsyncSessionLocal() as db:
        try:
            await MessengerService(db).assert_chat_member(channel_id, user_id)
        except ForbiddenError:
            await websocket.close(code=1008)
            return
    client = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(f"chat:{channel_id}")

    async def receive_loop() -> None:
        while True:
            data = await websocket.receive_text()
            async with AsyncSessionLocal() as db:
                await MessengerService(db).send_message(channel_id, user_id, data)

    async def publish_loop() -> None:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])

    try:
        await asyncio.gather(receive_loop(), publish_loop())
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"chat:{channel_id}")
        await pubsub.aclose()
        await client.aclose()
