from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.apps.auth.models import User
from app.apps.payments.models import Product
from app.apps.payments.schemas import CheckoutOut, CheckoutRequest, ProductCreate, ProductOut
from app.apps.payments.service import PaymentService
from app.db.session import get_db

router = APIRouter(tags=["Payments"])


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/products", response_model=ProductOut, summary="Product yaratish")
async def create_product(
    payload: ProductCreate,
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> Product:
    return await service.create_product(payload, user.id)


@router.get("/products", response_model=list[ProductOut], summary="Active productlar")
async def list_products(school_id: UUID, service: PaymentService = Depends(get_payment_service)) -> list[Product]:
    return await service.list_products(school_id)


@router.patch("/products/{product_id}", response_model=ProductOut, summary="Product yangilash")
async def update_product(
    product_id: UUID,
    payload: ProductCreate,
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> Product:
    return await service.update_product(product_id, payload, user.id)


@router.delete("/products/{product_id}", summary="Product delete")
async def delete_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    return await service.delete_product(product_id, user.id)


@router.post("/checkout/sessions", response_model=CheckoutOut, summary="Stripe Checkout Session")
async def create_checkout(
    payload: CheckoutRequest,
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> CheckoutOut:
    return await service.create_checkout(payload, user.id)


@router.post("/payments/stripe/webhook", summary="Stripe webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    return await service.process_stripe_webhook(await request.body(), stripe_signature)

