"""
Redis client utilities and connection helpers.
"""

import logging

logger = logging.getLogger(__name__)


def _create_redis_client(redis_url: str):
    """Create and return a Redis client instance."""
    import redis

    return redis.from_url(redis_url)


def _perform_redis_connection_test(redis_client) -> dict:
    """Perform Redis connection test operations."""
    test_key = "celery_test_key"
    test_value = "celery_test_value"

    try:
        # Set and get a test value
        redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = redis_client.get(test_key)

        # Clean up
        redis_client.delete(test_key)

        success = (
            retrieved_value.decode("utf-8") == test_value if retrieved_value else False
        )

        return {
            "success": success,
            "message": "Redis operations completed successfully"
            if success
            else "Redis test operations failed",
        }

    except Exception as test_error:
        logger.error(f"Redis test operations failed: {test_error}", exc_info=True)
        return {
            "success": False,
            "message": f"Redis test operations failed: {str(test_error)}",
        }


def _build_redis_test_response(
    success: bool, redis_url: str = None, message: str = None, error_message: str = None
) -> dict:
    """Build Redis test response structure for both success and error cases."""
    if success:
        return {
            "status": "success",
            "redis_url": redis_url,
            "test_passed": True,
            "message": message or "Redis operations completed successfully",
        }
    else:
        return {
            "status": "error",
            "test_passed": False,
            "message": error_message or f"Redis connection failed: {message}",
        }
