from celery import Celery

from app.core.config import settings

celery_app = Celery("exode", broker=settings.redis_url, backend=settings.redis_url, include=["app.workers.tasks"])
celery_app.conf.timezone = "Asia/Tashkent"
celery_app.conf.beat_schedule = {
    "cleanup-expired-refresh-tokens": {
        "task": "app.workers.tasks.cleanup_expired_refresh_tokens",
        "schedule": 3600,
    },
}
