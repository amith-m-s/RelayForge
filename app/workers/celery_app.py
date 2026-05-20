from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "relayforge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.task_routes = {
    "app.workers.tasks.dispatch_delivery": {"queue": "deliveries"},
    "app.workers.tasks.retry_delivery": {"queue": "retries"},
    "app.workers.tasks.aggregate_delivery_metrics": {"queue": "metrics"},
}

celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.result_expires = 3600