"""
Redis connection and testing tasks.
"""

import logging

from app.core.celery import celery_app
from app.core.config import settings

from .redis_client import (
    _build_redis_test_response,
    _create_redis_client,
    _perform_redis_connection_test,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    time_limit=settings.REDIS_TASK_TIME_LIMIT,
    soft_time_limit=settings.REDIS_TASK_SOFT_TIME_LIMIT,
)
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


@celery_app.task(
    time_limit=settings.REDIS_TASK_TIME_LIMIT,
    soft_time_limit=settings.REDIS_TASK_SOFT_TIME_LIMIT,
)
def test_redis_connection():
    """
    Test task to verify Redis connection is working.

    Returns:
        dict: Connection test results
    """
    try:
        # Import here to avoid import errors if Redis is not available

        from app.core.config import settings

        redis_client = _create_redis_client(settings.REDIS_URL)
        test_result = _perform_redis_connection_test(redis_client)
        success = test_result["success"]

        return _build_redis_test_response(
            success=success,
            redis_url=settings.REDIS_URL,
            message=test_result.get("message", ""),
        )

    except Exception as connection_error:
        logger.error(f"Redis connection test failed: {connection_error}", exc_info=True)
        return _build_redis_test_response(
            success=False,
            error_message=f"Redis connection failed: {str(connection_error)}",
        )
