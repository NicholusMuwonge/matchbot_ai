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
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    # Auto-discover tasks from all installed apps
    include=[
        "app.tasks.computation",
        "app.tasks.file_processing", 
        "app.tasks.redis_utils",
        "app.tasks.example_tasks",  # Legacy compatibility
    ],
)

# Configure task routes for different queues
celery_app.conf.task_routes = {
    "app.tasks.redis_utils.add_numbers": {"queue": "default"},
    "app.tasks.redis_utils.test_redis_connection": {"queue": "default"},
    "app.tasks.computation.process_heavy_computation_task": {"queue": "heavy_compute"},
    "app.tasks.file_processing.process_large_file_upload_task": {"queue": "file_processing"},
    # Legacy compatibility
    "app.tasks.example_tasks.add_numbers": {"queue": "default"},
    "app.tasks.example_tasks.test_redis_connection": {"queue": "default"},
    "app.tasks.example_tasks.process_heavy_computation_task": {"queue": "heavy_compute"},
    "app.tasks.example_tasks.process_large_file_upload_task": {"queue": "file_processing"},
    # Add more routing rules as needed
}

if __name__ == "__main__":
    celery_app.start()
