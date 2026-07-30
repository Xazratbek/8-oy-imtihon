from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas import ORMModel


class ProductCreate(BaseModel):
    school_id: UUID
    title: str
    description: str = ""
    price_amount: float = 0
    currency: str = "UZS"
    status: str = "active"
    course_ids: list[UUID] = Field(default_factory=list)


class ProductOut(ORMModel):
    id: UUID
    school_id: UUID
    title: str
    description: str
    price_amount: float
    currency: str
    status: str


class CheckoutRequest(BaseModel):
    product_id: UUID
    success_url: str = "http://localhost:3000/success"
    cancel_url: str = "http://localhost:3000/cancel"


class CheckoutOut(BaseModel):
    invoice_id: UUID
    checkout_url: str
