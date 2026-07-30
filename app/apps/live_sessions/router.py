from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.apps.auth.models import User
from app.apps.live_sessions.models import LiveSession
from app.apps.live_sessions.schemas import LiveSessionCreate, LiveSessionOut
from app.apps.live_sessions.service import LiveSessionService
from app.db.session import get_db

router = APIRouter(prefix="/live-sessions", tags=["Live sessions"])


def get_live_session_service(db: AsyncSession = Depends(get_db)) -> LiveSessionService:
    return LiveSessionService(db)


@router.post("", response_model=LiveSessionOut, summary="Live dars yaratish")
async def create_live(
    payload: LiveSessionCreate,
    user: User = Depends(get_current_user),
    service: LiveSessionService = Depends(get_live_session_service),
) -> LiveSession:
    return await service.create_live(payload, user.id)


@router.get("", response_model=list[LiveSessionOut], summary="Course live darslari")
async def list_live(
    course_id: UUID,
    user: User = Depends(get_current_user),
    service: LiveSessionService = Depends(get_live_session_service),
) -> list[LiveSession]:
    return await service.list_live(course_id, user.id)


@router.get("/{session_id}/join", summary="Live dars join link")
async def join_live(
    session_id: UUID,
    user: User = Depends(get_current_user),
    service: LiveSessionService = Depends(get_live_session_service),
) -> dict:
    return await service.join_live(session_id, user.id)


@router.post("/{session_id}/finish", response_model=LiveSessionOut, summary="Live dars tugatish")
async def finish_live(
    session_id: UUID,
    user: User = Depends(get_current_user),
    service: LiveSessionService = Depends(get_live_session_service),
) -> LiveSession:
    return await service.finish_live(session_id, user.id)

