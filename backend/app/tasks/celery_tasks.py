from app.core.celery_app import celery_app
from app.tasks.run_giant import run as run_giant
from app.tasks.run_pinarello import run as run_pinarello
from app.tasks.run_specialized import run as run_specialized


@celery_app.task(name="app.tasks.celery_tasks.sync_giant_products")
def sync_giant_products(limit: int | None = None) -> dict[str, int]:
    return run_giant(limit=limit)


@celery_app.task(name="app.tasks.celery_tasks.sync_specialized_products")
def sync_specialized_products(limit: int | None = None) -> dict[str, int]:
    return run_specialized(limit=limit)


@celery_app.task(name="app.tasks.celery_tasks.sync_pinarello_products")
def sync_pinarello_products(limit: int | None = None) -> dict[str, int]:
    return run_pinarello(limit=limit)
