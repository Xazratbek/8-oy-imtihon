from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course
from app.apps.learning.models import Enrollment
from app.apps.messenger.models import ChatChannel, ChatMember
from app.apps.payments.models import Invoice, PaymentWebhookEvent, Product, ProductCourse
from app.apps.schools.models import SchoolMember


class PaymentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_owner_or_admin(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(
            select(SchoolMember).where(
                SchoolMember.school_id == school_id,
                SchoolMember.user_id == user_id,
                SchoolMember.is_active.is_(True),
                SchoolMember.role.in_(("owner", "admin")),
            )
        )
        return result.scalar_one_or_none()

    async def get_course(self, course_id: UUID) -> Course | None:
        return await self.db.get(Course, course_id)

    async def get_product(self, product_id: UUID) -> Product | None:
        return await self.db.get(Product, product_id)

    async def list_products(self, school_id: UUID) -> list[Product]:
        result = await self.db.execute(select(Product).where(Product.school_id == school_id, Product.status == "active"))
        return list(result.scalars())

    async def list_product_courses(self, product_id: UUID) -> list[ProductCourse]:
        result = await self.db.execute(select(ProductCourse).where(ProductCourse.product_id == product_id))
        return list(result.scalars())

    async def get_invoice(self, invoice_id) -> Invoice | None:
        return await self.db.get(Invoice, invoice_id)

    async def get_webhook_event(self, event_id: str) -> PaymentWebhookEvent | None:
        result = await self.db.execute(select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_id == event_id))
        return result.scalar_one_or_none()

    async def enrollment_exists(self, course_id: UUID, user_id: UUID) -> bool:
        result = await self.db.execute(select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.user_id == user_id))
        return result.scalar_one_or_none() is not None

    async def get_course_chat(self, course_id: UUID) -> ChatChannel | None:
        result = await self.db.execute(select(ChatChannel).where(ChatChannel.course_id == course_id, ChatChannel.channel_type == "course_group"))
        return result.scalar_one_or_none()

    def add(self, entity):
        self.db.add(entity)
        return entity

    async def delete(self, entity) -> None:
        await self.db.delete(entity)

