from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.schemas import ORMModel


class LiveSessionCreate(BaseModel):
    course_id: UUID
    title: str
    starts_at: datetime
    ends_at: datetime
    room_url: str
    provider: str = "jitsi"


class LiveSessionOut(ORMModel):
    id: UUID
    course_id: UUID
    host_id: UUID
    title: str
    starts_at: datetime
    ends_at: datetime
    provider: str
    room_url: str
    status: str
