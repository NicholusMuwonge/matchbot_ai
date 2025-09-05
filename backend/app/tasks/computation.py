"""
Heavy computation tasks for CPU-intensive operations.
"""

import logging
import time

from celery import current_task

from app.core.celery import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    time_limit=settings.COMPUTATION_TASK_TIME_LIMIT,
    soft_time_limit=settings.COMPUTATION_TASK_SOFT_TIME_LIMIT,
)
def process_heavy_computation_task(self, data_size: int = 10000):
    """
    Example task that simulates heavy computation work with progress updates.
    This demonstrates proper async processing for CPU-intensive operations.

    Args:
        data_size: Size of data to process (simulated workload)

    Returns:
        dict: Task completion status
    """
    logger.info(
        f"Starting heavy computation task {self.request.id} with data size {data_size}"
    )

    try:
        for batch_number in range(data_size // 1000):
            # Simulate CPU-intensive work
            _process_computation_batch(batch_number, data_size)

            # Update task progress
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": batch_number * 1000,
                    "total": data_size,
                    "status": f"Processing batch {batch_number + 1} of {data_size // 1000}...",
                },
            )
            logger.debug(
                f"Task {self.request.id} progress: {batch_number * 1000}/{data_size}"
            )
            time.sleep(0.1)  # Simulate processing time

        computation_result = _finalize_computation_result(data_size, self.request.id)
        logger.info(f"Task {self.request.id} completed successfully")
        return computation_result

    except Exception as computation_error:
        logger.error(
            f"Heavy computation task {self.request.id} failed: {computation_error}",
            exc_info=True,
        )
        raise self.retry(exc=computation_error, countdown=60, max_retries=3)


def _process_computation_batch(batch_number: int, _total_data_size: int) -> None:
    """Simulate processing a batch of computation-heavy data."""
    # Simulate CPU-intensive work
    import math

    result = sum(math.sqrt(i) for i in range(1000))
    logger.debug(f"Processed batch {batch_number}, computation result: {result:.2f}")


def _finalize_computation_result(data_size: int, task_id: str) -> dict:
    """Finalize and return computation task results."""
    return {
        "status": "completed",
        "result": f"Heavy computation completed for {data_size} data points",
        "task_id": task_id,
        "processed_batches": data_size // 1000,
    }
