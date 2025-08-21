"""
Example Celery tasks for testing Redis and Celery setup
"""

import logging
import time

from celery import current_task

from app.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def example_task(self, duration: int = 10):
    """
    Example task that simulates work with progress updates.

    Args:
        duration: How long the task should run (in seconds)

    Returns:
        dict: Task completion status
    """
    logger.info(f"Starting example task {self.request.id} for {duration} seconds")

    try:
        for i in range(duration):
            # Update task progress
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": i,
                    "total": duration,
                    "status": f"Processing step {i + 1} of {duration}...",
                },
            )
            logger.debug(f"Task {self.request.id} progress: {i + 1}/{duration}")
            time.sleep(1)

        result = {
            "status": "completed",
            "result": f"Task completed after {duration} seconds",
            "task_id": self.request.id,
        }
        logger.info(f"Task {self.request.id} completed successfully")
        return result

    except Exception as exc:
        logger.error(f"Task {self.request.id} failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task
def add_numbers(x: int, y: int):
    """
    Simple task to add two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        int: Sum of x and y
    """
    logger.info(f"Adding {x} + {y}")
    result = x + y
    logger.info(f"Result: {result}")
    return result


@celery_app.task
def test_redis_connection():
    """
    Test task to verify Redis connection is working.

    Returns:
        dict: Connection test results
    """
    try:
        # Import here to avoid import errors if Redis is not available
        import redis

        from app.core.config import settings

        # Create Redis client
        r = redis.from_url(settings.REDIS_URL)

        # Test basic operations
        test_key = "celery_test_key"
        test_value = "celery_test_value"

        # Set and get a test value
        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = r.get(test_key)

        # Clean up
        r.delete(test_key)

        success = (
            retrieved_value.decode("utf-8") == test_value if retrieved_value else False
        )

        return {
            "status": "success" if success else "failed",
            "redis_url": settings.REDIS_URL,
            "test_passed": success,
            "message": "Redis connection test completed successfully"
            if success
            else "Redis test failed",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Redis connection failed: {str(e)}",
            "test_passed": False,
        }
