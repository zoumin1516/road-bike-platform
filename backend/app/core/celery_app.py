from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "road_bike_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.celery_tasks"],
)

celery_app.conf.update(
    timezone=settings.celery_timezone,
    enable_utc=False,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "daily-giant-full-sync": {
            "task": "app.tasks.celery_tasks.sync_giant_products",
            # 每天凌晨 03:15（Asia/Shanghai）执行，避开常规浏览高峰。
            "schedule": crontab(hour=3, minute=15),
            "kwargs": {"limit": None},
        },
        "daily-specialized-full-sync": {
            "task": "app.tasks.celery_tasks.sync_specialized_products",
            # 每天凌晨 04:15（Asia/Shanghai）执行，和 Giant 错峰。
            "schedule": crontab(hour=4, minute=15),
            "kwargs": {"limit": None},
        },
        "daily-pinarello-full-sync": {
            "task": "app.tasks.celery_tasks.sync_pinarello_products",
            # 每天凌晨 05:15（Asia/Shanghai）执行，和其他品牌错峰。
            "schedule": crontab(hour=5, minute=15),
            "kwargs": {"limit": None},
        },
    },
)
