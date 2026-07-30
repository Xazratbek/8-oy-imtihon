from fastapi import APIRouter

from app.apps.analytics import router as analytics
from app.apps.auth import router as auth
from app.apps.courses import router as courses
from app.apps.exports import router as exports
from app.apps.learning import router as learning
from app.apps.live_sessions import router as live
from app.apps.media import router as media
from app.apps.messenger import router as messenger
from app.apps.payments import router as payments
from app.apps.public_catalog import router as public_catalog
from app.apps.schools import router as schools

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(schools.router)
api_router.include_router(courses.router)
api_router.include_router(public_catalog.router)
api_router.include_router(media.router)
api_router.include_router(payments.router)
api_router.include_router(learning.router)
api_router.include_router(messenger.router)
api_router.include_router(messenger.ws_router)
api_router.include_router(analytics.router)
api_router.include_router(exports.router)
api_router.include_router(live.router)
