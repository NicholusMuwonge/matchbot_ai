"""
Celery health check endpoint and utilities.
"""

import logging
from fastapi import APIRouter, HTTPException
from .celery_utils import (
    _get_celery_worker_info,
    _validate_celery_workers_available,
    _calculate_celery_statistics,
    _build_celery_healthy_response,
    _build_celery_error_response
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health-check", tags=["health"])




@router.get("/celery")
def health_check_celery():
    """Check Celery workers availability and health."""
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