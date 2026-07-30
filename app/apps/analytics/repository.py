from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course
from app.apps.learning.models import Enrollment, LessonProgress
from app.apps.payments.models import Invoice
from app.apps.schools.models import SchoolMember


class AnalyticsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_owner_or_admin(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(
            select(SchoolMember).where(
                SchoolMember.school_id == school_id,
                SchoolMember.user_id == user_id,
                SchoolMember.role.in_(("owner", "admin")),
                SchoolMember.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def dashboard(self, school_id: UUID, from_: datetime | None = None, to: datetime | None = None) -> dict:
        invoice_filter = [Invoice.school_id == school_id, Invoice.status == "paid"]
        if from_:
            invoice_filter.append(Invoice.created_at >= from_)
        if to:
            invoice_filter.append(Invoice.created_at <= to)
        revenue = await self.db.scalar(select(func.coalesce(func.sum(Invoice.amount), 0)).where(*invoice_filter))
        paid_invoices = await self.db.scalar(select(func.count(Invoice.id)).where(*invoice_filter))
        students = await self.db.scalar(select(func.count(func.distinct(Enrollment.user_id))).where(Enrollment.school_id == school_id))
        active_students = await self.db.scalar(
            select(func.count(func.distinct(Enrollment.user_id))).where(Enrollment.school_id == school_id, Enrollment.status == "active")
        )
        completed = await self.db.scalar(
            select(func.count(LessonProgress.id)).join(Course, Course.id == LessonProgress.course_id).where(Course.school_id == school_id)
        )
        top_rows = await self.db.execute(
            select(Course.title, func.count(Enrollment.id).label("students"))
            .join(Enrollment, Enrollment.course_id == Course.id, isouter=True)
            .where(Course.school_id == school_id)
            .group_by(Course.id)
            .order_by(func.count(Enrollment.id).desc())
            .limit(5)
        )
        return {
            "total_students": students or 0,
            "active_students": active_students or 0,
            "revenue": float(revenue or 0),
            "paid_invoices": paid_invoices or 0,
            "completed_lessons": completed or 0,
            "top_courses": [{"title": title, "students": count} for title, count in top_rows.all()],
        }

