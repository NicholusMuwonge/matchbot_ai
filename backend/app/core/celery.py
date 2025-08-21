"""
Celery configuration for async task processing
"""

from celery import Celery

from app.core.config import settings

# Create Celery app instance
celery_app = Celery("matchbot_ai")

# Configure Celery
celery_app.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Auto-discover tasks from all installed apps
    include=[
        "app.tasks.example_tasks",
        # Add more task modules here as needed
    ],
)

# Optional: Configure task routes for different queues
celery_app.conf.task_routes = {
    "app.tasks.example_tasks.*": {"queue": "default"},
    # Add more routing rules as needed
}

if __name__ == "__main__":
    celery_app.start()
