#!/usr/bin/env python
"""
Celery worker entry point that ensures all tasks are imported
"""

# Import all task modules to register them
# Import the celery app
from app.core.celery import celery_app
from app.tasks import (  # noqa: F401
    computation,
    file_processing,
    redis_utils,
    user_sync_tasks,
)

if __name__ == "__main__":
    celery_app.start()
