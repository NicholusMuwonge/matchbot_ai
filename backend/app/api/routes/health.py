"""
Simple health check endpoints for Redis and Celery monitoring.
"""

import logging
from datetime import datetime

import redis
from fastapi import APIRouter, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health-check", tags=["health"])


@router.get("/redis")
def check_redis_health():
    """Simple Redis health check."""
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.set("health_check", "ok", ex=60)
        result = redis_client.get("health_check")
        redis_client.delete("health_check")

        return {
            "status": "healthy" if result == "ok" else "unhealthy",
            "service": "redis",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as error:
        logger.error(f"Redis health check failed: {error}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "redis",
                "error": str(error),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get("/celery")
def check_celery_health():
    """Simple Celery health check."""
    try:
        from app.core.celery import celery_app

        inspector = celery_app.control.inspect()
        active_workers = inspector.active()

        if not active_workers:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "service": "celery",
                    "message": "No active workers",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        worker_count = len(active_workers)
        return {
            "status": "healthy",
            "service": "celery",
            "workers": worker_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Celery health check failed: {error}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "celery",
                "error": str(error),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get("/")
def health_check():
    """Basic API health check."""
    return {
        "status": "healthy",
        "service": "api",
        "timestamp": datetime.utcnow().isoformat(),
    }
