from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    code: str = "OK"
    payload: T | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    code: str
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    code: str = "OK"
    items: list[T]
    total: int
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Pagination(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
