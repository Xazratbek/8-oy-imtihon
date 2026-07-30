from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.schemas import ORMModel


class MessageCreate(BaseModel):
    body: str


class ChatOut(ORMModel):
    id: UUID
    school_id: UUID
    course_id: UUID | None = None
    channel_type: str
    title: str


class MessageOut(ORMModel):
    id: UUID
    channel_id: UUID
    sender_id: UUID
    body: str
    created_at: datetime
