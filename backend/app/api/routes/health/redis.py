"""
Redis health check endpoint and utilities.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health-check", tags=["health"])


def _create_redis_health_client(redis_url: str):
    """Create Redis client for health checks."""
    import redis

    return redis.from_url(redis_url, decode_responses=True)


def _execute_redis_health_test(redis_client) -> dict:
    """Execute Redis health test operations."""
    test_key = "health_check_test"
    test_value = "ok"

    try:
        # Set and get a test value
        redis_client.set(test_key, test_value, ex=60)
        retrieved_value = redis_client.get(test_key)

        # Clean up
        redis_client.delete(test_key)

        success = retrieved_value == test_value

        return {
            "success": success,
            "message": "Redis connection test completed successfully"
            if success
            else "Redis test failed",
        }

    except Exception as test_error:
        logger.error(
            f"Redis health test operations failed: {test_error}", exc_info=True
        )
        return {
            "success": False,
            "message": f"Redis health test failed: {str(test_error)}",
        }


def _build_redis_health_response(success: bool, redis_url: str, message: str) -> dict:
    """Build Redis health check response."""
    return {
        "status": "healthy" if success else "unhealthy",
        "service": "redis",
        "redis_url": redis_url,
        "test_passed": success,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
    }


def _build_redis_health_error_response(error_message: str) -> dict:
    """Build Redis health check error response."""
    return {
        "status": "unhealthy",
        "service": "redis",
        "test_passed": False,
        "error": error_message,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Redis connection failed: {error_message}",
    }


@router.get("/redis")
def health_check_redis():
    """Check Redis connection health."""
    try:
        from app.core.config import settings

        redis_client = _create_redis_health_client(settings.REDIS_URL)
        health_test_result = _execute_redis_health_test(redis_client)
        success = health_test_result["success"]

        return _build_redis_health_response(
            success, settings.REDIS_URL, health_test_result.get("message", "")
        )

    except Exception as health_error:
        logger.error(f"Redis health check failed: {health_error}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=_build_redis_health_error_response(str(health_error)),
        )