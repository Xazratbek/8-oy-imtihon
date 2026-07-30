from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.schemas import ORMModel


class CategoryCreate(BaseModel):
    name: str
    slug: str
    sort_order: int = 0


class CategoryOut(ORMModel):
    id: UUID
    school_id: UUID
    name: str
    slug: str
    sort_order: int


class CourseCreate(BaseModel):
    school_id: UUID
    category_id: UUID | None = None
    title: str
    slug: str
    short_description: str = ""
    description: str = ""
    cover_url: str | None = None
    price_amount: float = 0
    currency: str = "UZS"
    level: str = "beginner"
    language: str = "uz"
    estimated_duration_minutes: int = 0


class CourseUpdate(BaseModel):
    category_id: UUID | None = None
    title: str | None = None
    short_description: str | None = None
    description: str | None = None
    cover_url: str | None = None
    status: str | None = None
    price_amount: float | None = None
    currency: str | None = None
    level: str | None = None
    language: str | None = None
    estimated_duration_minutes: int | None = None


class CourseOut(ORMModel):
    id: UUID
    school_id: UUID
    category_id: UUID | None = None
    title: str
    slug: str
    short_description: str
    description: str
    cover_url: str | None = None
    status: str
    price_amount: float
    currency: str
    level: str
    language: str
    estimated_duration_minutes: int
    published_at: datetime | None = None


class ModuleCreate(BaseModel):
    title: str
    description: str = ""
    sort_order: int = 0


class ModuleOut(ORMModel):
    id: UUID
    course_id: UUID
    title: str
    description: str
    sort_order: int


class LessonCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "draft"
    is_preview: bool = False
    sort_order: int = 0


class LessonOut(ORMModel):
    id: UUID
    module_id: UUID
    course_id: UUID
    title: str
    description: str
    status: str
    is_preview: bool
    sort_order: int


class BlockCreate(BaseModel):
    block_type: str
    title: str = ""
    content: str = ""
    file_url: str | None = None
    video_asset_id: UUID | None = None
    quiz_id: UUID | None = None
    homework_id: UUID | None = None
    sort_order: int = 0


class BlockOut(ORMModel):
    id: UUID
    lesson_id: UUID
    block_type: str
    title: str
    content: str
    file_url: str | None = None
    video_asset_id: UUID | None = None
    sort_order: int
