from datetime import UTC, datetime
from uuid import UUID

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.learning.models import Enrollment
from app.apps.messenger.models import ChatMember
from app.apps.payments.models import Invoice, Payment, PaymentWebhookEvent, Product, ProductCourse
from app.apps.payments.repository import PaymentRepository
from app.apps.payments.schemas import CheckoutOut, CheckoutRequest, ProductCreate
from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.config import settings


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PaymentRepository(db)

    async def assert_school_owner(self, school_id: UUID, user_id: UUID) -> None:
        if not await self.repo.get_owner_or_admin(school_id, user_id):
            raise ForbiddenError("Owner/admin access kerak")

    async def create_product(self, payload: ProductCreate, user_id: UUID) -> Product:
        await self.assert_school_owner(payload.school_id, user_id)
        product = self.repo.add(Product(**payload.model_dump(exclude={"course_ids"})))
        await self.db.flush()
        await self._replace_product_courses(product, payload.course_ids, payload.school_id)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def list_products(self, school_id: UUID) -> list[Product]:
        return await self.repo.list_products(school_id)

    async def update_product(self, product_id: UUID, payload: ProductCreate, user_id: UUID) -> Product:
        product = await self.repo.get_product(product_id)
        if not product:
            raise NotFoundError("Product topilmadi")
        await self.assert_school_owner(product.school_id, user_id)
        for key, value in payload.model_dump(exclude={"course_ids", "school_id"}).items():
            setattr(product, key, value)
        for link in await self.repo.list_product_courses(product.id):
            await self.repo.delete(link)
        await self.db.flush()
        await self._replace_product_courses(product, payload.course_ids, product.school_id)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: UUID, user_id: UUID) -> dict:
        product = await self.repo.get_product(product_id)
        if not product:
            raise NotFoundError("Product topilmadi")
        await self.assert_school_owner(product.school_id, user_id)
        await self.repo.delete(product)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"deleted": True}}

    async def create_checkout(self, payload: CheckoutRequest, user_id: UUID) -> CheckoutOut:
        product = await self.repo.get_product(payload.product_id)
        if not product or product.status != "active":
            raise NotFoundError("Active product topilmadi")
        invoice = self.repo.add(
            Invoice(
                school_id=product.school_id,
                product_id=product.id,
                user_id=user_id,
                amount=product.price_amount,
                currency=product.currency,
                status="pending",
            )
        )
        await self.db.flush()
        if not settings.stripe_secret_key or settings.stripe_secret_key == "sk_test_change_me":
            raise ConflictError("STRIPE_SECRET_KEY .env ichida real test key bo'lishi kerak")
        stripe.api_key = settings.stripe_secret_key
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            line_items=[
                {
                    "price_data": {
                        "currency": product.currency.lower(),
                        "unit_amount": int(float(product.price_amount) * 100),
                        "product_data": {"name": product.title},
                    },
                    "quantity": 1,
                }
            ],
            metadata={"invoice_id": str(invoice.id), "product_id": str(product.id), "user_id": str(user_id)},
        )
        invoice.stripe_session_id = session.id
        await self.db.commit()
        return CheckoutOut(invoice_id=invoice.id, checkout_url=session.url)

    async def process_stripe_webhook(self, raw_body: bytes, stripe_signature: str | None) -> dict:
        if not settings.stripe_webhook_secret or settings.stripe_webhook_secret == "whsec_change_me":
            raise ConflictError("STRIPE_WEBHOOK_SECRET .env ichida real webhook secret bo'lishi kerak")
        event = stripe.Webhook.construct_event(raw_body, stripe_signature, settings.stripe_webhook_secret)
        event_id = event["id"]
        if await self.repo.get_webhook_event(event_id):
            return {"success": True, "code": "OK", "payload": {"duplicate": True}}
        webhook = self.repo.add(PaymentWebhookEvent(provider="stripe", event_id=event_id, event_type=event["type"], payload=event))
        if event["type"] == "checkout.session.completed":
            await self._handle_checkout_completed(event)
        webhook.processed_at = datetime.now(UTC)
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"processed": True}}

    async def _replace_product_courses(self, product: Product, course_ids: list[UUID], school_id: UUID) -> None:
        for course_id in course_ids:
            course = await self.repo.get_course(course_id)
            if not course or course.school_id != school_id:
                raise NotFoundError("Course product schooliga tegishli emas")
            self.repo.add(ProductCourse(product_id=product.id, course_id=course_id))

    async def _handle_checkout_completed(self, event) -> None:
        session = event["data"]["object"]
        invoice_id = session.get("metadata", {}).get("invoice_id")
        invoice = await self.repo.get_invoice(invoice_id)
        if not invoice:
            return
        invoice.status = "paid"
        self.repo.add(
            Payment(
                invoice_id=invoice.id,
                provider="stripe",
                provider_payment_id=session.get("payment_intent"),
                amount=invoice.amount,
                currency=invoice.currency,
                status="paid",
            )
        )
        await self._grant_enrollments(invoice)

    async def _grant_enrollments(self, invoice: Invoice) -> None:
        for row in await self.repo.list_product_courses(invoice.product_id):
            if await self.repo.enrollment_exists(row.course_id, invoice.user_id):
                continue
            self.repo.add(
                Enrollment(
                    school_id=invoice.school_id,
                    course_id=row.course_id,
                    user_id=invoice.user_id,
                    invoice_id=invoice.id,
                    status="active",
                    started_at=datetime.now(UTC),
                )
            )
            channel = await self.repo.get_course_chat(row.course_id)
            if channel:
                self.repo.add(ChatMember(channel_id=channel.id, user_id=invoice.user_id, role="member"))

