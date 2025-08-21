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
        "app.tasks.computation",
        "app.tasks.file_processing",
        "app.tasks.redis_utils",
        "app.tasks.example_tasks",  # Legacy compatibility
        # Add more task modules here as needed
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
