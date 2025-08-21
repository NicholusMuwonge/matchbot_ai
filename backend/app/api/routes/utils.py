import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


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
        redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
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


@router.get("/health-check/redis")
def health_check_redis():
    """
    Check Redis connection health.
    """
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


def _get_celery_worker_info():
    """Get Celery worker information and statistics."""
    from app.core.celery import celery_app

    inspector = celery_app.control.inspect()
    active_workers = inspector.active()
    registered_tasks = inspector.registered()

    return {"active_workers": active_workers, "registered_tasks": registered_tasks}


def _validate_celery_workers_available(active_workers: dict) -> None:
    """Validate that Celery workers are available."""
    if not active_workers:
        raise HTTPException(
            status_code=503,
            detail=_build_celery_no_workers_response(),
        )


def _calculate_celery_statistics(active_workers: dict, registered_tasks: dict) -> dict:
    """Calculate Celery worker statistics."""
    worker_count = len(active_workers)
    total_active_tasks = sum(len(tasks) for tasks in active_workers.values())
    registered_task_count = (
        len(registered_tasks.get(list(registered_tasks.keys())[0], []))
        if registered_tasks
        else 0
    )

    return {
        "worker_count": worker_count,
        "total_active_tasks": total_active_tasks,
        "registered_task_count": registered_task_count,
        "worker_names": list(active_workers.keys()),
    }


def _build_celery_healthy_response(stats: dict) -> dict:
    """Build Celery healthy response."""
    return {
        "status": "healthy",
        "service": "celery",
        "workers": stats["worker_names"],
        "worker_count": stats["worker_count"],
        "active_tasks": stats["total_active_tasks"],
        "registered_tasks": stats["registered_task_count"],
        "test_passed": True,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Celery healthy with {stats['worker_count']} worker(s) and {stats['total_active_tasks']} active task(s)",
    }


def _build_celery_no_workers_response() -> dict:
    """Build Celery no workers available response."""
    return {
        "status": "unhealthy",
        "service": "celery",
        "workers": [],
        "test_passed": False,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "No Celery workers available",
    }


def _build_celery_error_response(error_message: str) -> dict:
    """Build Celery error response."""
    return {
        "status": "unhealthy",
        "service": "celery",
        "test_passed": False,
        "error": error_message,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Celery health check failed: {error_message}",
    }


@router.get("/health-check/celery")
def health_check_celery():
    """
    Check Celery workers availability and health.
    """
    try:
        worker_info = _get_celery_worker_info()
        active_workers = worker_info["active_workers"]
        registered_tasks = worker_info["registered_tasks"]

        _validate_celery_workers_available(active_workers)

        celery_statistics = _calculate_celery_statistics(
            active_workers, registered_tasks
        )

        return _build_celery_healthy_response(celery_statistics)

    except HTTPException:
        raise
    except Exception as celery_error:
        logger.error(f"Celery health check failed: {celery_error}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=_build_celery_error_response(str(celery_error)),
        )
