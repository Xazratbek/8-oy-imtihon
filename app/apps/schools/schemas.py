from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas import ORMModel


class SchoolCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    logo_url: str | None = None
    cover_url: str | None = None
    primary_color: str = "#2563eb"
    secondary_color: str = "#111827"
    contact_phone: str | None = None
    contact_telegram: str | None = None
    timezone: str = "Asia/Tashkent"
    currency: str = "UZS"
    settings: dict = Field(default_factory=dict)


class SchoolUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    contact_phone: str | None = None
    contact_telegram: str | None = None
    timezone: str | None = None
    currency: str | None = None
    settings: dict | None = None
    is_active: bool | None = None


class SchoolOut(ORMModel):
    id: UUID
    name: str
    slug: str
    description: str
    logo_url: str | None = None
    cover_url: str | None = None
    primary_color: str
    secondary_color: str
    timezone: str
    currency: str
    settings: dict
    is_active: bool


class MemberCreate(BaseModel):
    user_id: UUID
    role: str = "student"


class MemberUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class MemberOut(ORMModel):
    id: UUID
    school_id: UUID
    user_id: UUID
    role: str
    is_active: bool
