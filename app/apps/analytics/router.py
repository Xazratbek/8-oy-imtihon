from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.apps.analytics.service import AnalyticsService
from app.apps.auth.models import User
from app.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/dashboard", summary="School dashboard metrikalari")
async def dashboard(
    school_id: UUID,
    from_: datetime | None = None,
    to: datetime | None = None,
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    return await service.dashboard(school_id, user.id, from_, to)

