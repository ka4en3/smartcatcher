# worker/celery_app.py

import os
import sys
from datetime import timedelta
from pathlib import Path

from celery import Celery
from celery.schedules import crontab

# Add backend to Python path for importing models and services
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Initialize Celery app
app = Celery("smartcatcher")

# Configure Celery
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
app.conf.update(
    # Broker settings
    broker_url=redis_url,
    result_backend=redis_url,
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Result settings
    result_expires=3600,  # 1 hour

    beat_schedule_filename="/tmp/celerybeat-schedule",
    
    # Task routing
    task_routes={
        "tasks.scraper.*": {"queue": "scraper"},
        # "tasks.notifications.*": {"queue": "notifications"}, # TODO
    },

    # Beat schedule for periodic tasks
    beat_schedule={
        "check-prices": {
            "task": "tasks.scraper.check_all_product_prices",
            "schedule": timedelta(minutes=int(os.getenv("PRICE_CHECK_INTERVAL_MINUTES", "60"))),
            "options": {"queue": "scraper"},
        },
        # TODO
        # "process-notifications": {
        #     "task": "tasks.notifications.process_pending_notifications",
        #     "schedule": timedelta(minutes=5),  # Check every 5 minutes
        #     "options": {"queue": "notifications"},
        # },
        # "cleanup-old-notifications": {
        #     "task": "tasks.notifications.cleanup_old_notifications",
        #     "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        #     "options": {"queue": "notifications"},
        # },
    },
)

# Import tasks to register them
# from worker.tasks import scraper, notifications   # TODO
from tasks import scraper

# Auto-discover tasks
# app.autodiscover_tasks(["tasks"])

if __name__ == "__main__":
    app.start()
