from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email

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


@router.get("/health-check/redis")
def health_check_redis():
    """
    Check Redis connection health.
    """
    try:
        import redis

        from app.core.config import settings

        # Create Redis client
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Test basic operations
        test_key = "health_check_test"
        test_value = "ok"

        # Set and get a test value
        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = r.get(test_key)

        # Clean up
        r.delete(test_key)

        success = retrieved_value == test_value

        return {
            "status": "healthy" if success else "unhealthy",
            "service": "redis",
            "redis_url": settings.REDIS_URL,
            "test_passed": success,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Redis connection test completed successfully"
            if success
            else "Redis test failed",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "redis",
                "test_passed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Redis connection failed: {str(e)}",
            },
        )


@router.get("/health-check/celery")
def health_check_celery():
    """
    Check Celery workers availability and health.
    """
    try:
        from app.core.celery import celery_app

        # Check if workers are available
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()

        if not active_workers:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "service": "celery",
                    "workers": [],
                    "test_passed": False,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "No Celery workers available",
                },
            )

        worker_count = len(active_workers)
        total_active_tasks = sum(len(tasks) for tasks in active_workers.values())

        return {
            "status": "healthy",
            "service": "celery",
            "workers": list(active_workers.keys()),
            "worker_count": worker_count,
            "active_tasks": total_active_tasks,
            "registered_tasks": len(
                registered_tasks.get(list(registered_tasks.keys())[0], [])
            )
            if registered_tasks
            else 0,
            "test_passed": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Celery healthy with {worker_count} worker(s) and {total_active_tasks} active task(s)",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "celery",
                "test_passed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Celery health check failed: {str(e)}",
            },
        )
