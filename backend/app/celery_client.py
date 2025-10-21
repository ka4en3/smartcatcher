"""Celery client for sending tasks from backend services."""
import os
from celery import Celery


def get_celery_client() -> Celery:
    """Get Celery client for sending tasks (not for consuming)."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")

    # Create minimal Celery app just for sending tasks
    app = Celery("smartcatcher_client")

    app.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    return app


# Global client instance
celery_client = get_celery_client()