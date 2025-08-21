"""
Celery health check utility functions.
"""

import logging
from datetime import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)


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