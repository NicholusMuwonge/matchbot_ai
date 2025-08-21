"""
Example Celery tasks for testing Redis and Celery setup
"""

import logging
import time

from celery import current_task

from app.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
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


def _build_redis_test_response(success: bool, redis_url: str, message: str) -> dict:
    """Build Redis test response structure."""
    return {
        "status": "success" if success else "failed",
        "redis_url": redis_url,
        "test_passed": success,
        "message": message,
    }


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


def _build_redis_test_error_response(error_message: str) -> dict:
    """Build Redis test error response structure."""
    return {
        "status": "error",
        "message": f"Redis connection failed: {error_message}",
        "test_passed": False,
    }


@celery_app.task
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
            success, settings.REDIS_URL, test_result.get("message", "")
        )

    except Exception as connection_error:
        logger.error(f"Redis connection test failed: {connection_error}", exc_info=True)
        return _build_redis_test_error_response(str(connection_error))


@celery_app.task(bind=True)
def process_large_file_upload_task(
    self, file_path: str, processing_options: dict = None
):
    """
    Example task for processing large file uploads asynchronously.
    This demonstrates proper async processing for I/O-bound operations.

    Args:
        file_path: Path to the file to process
        processing_options: Options for file processing

    Returns:
        dict: File processing results
    """
    if processing_options is None:
        processing_options = {}

    logger.info(
        f"Starting file processing task {self.request.id} for file: {file_path}"
    )

    try:
        # Validate file exists and is accessible
        file_validation_result = _validate_file_for_processing(file_path)
        if not file_validation_result["valid"]:
            raise ValueError(file_validation_result["error"])

        # Process file in chunks to avoid memory issues
        processing_result = _process_file_in_chunks(
            file_path,
            processing_options,
            progress_callback=lambda current, total: _update_file_processing_progress(
                self, current, total
            ),
        )

        final_result = _finalize_file_processing_result(
            processing_result, file_path, self.request.id
        )

        logger.info(f"File processing task {self.request.id} completed successfully")
        return final_result

    except Exception as file_processing_error:
        logger.error(
            f"File processing task {self.request.id} failed: {file_processing_error}",
            exc_info=True,
        )
        raise self.retry(exc=file_processing_error, countdown=30, max_retries=2)


def _validate_file_for_processing(file_path: str) -> dict:
    """Validate that the file exists and can be processed."""
    import os

    try:
        if not os.path.exists(file_path):
            return {"valid": False, "error": f"File not found: {file_path}"}

        if not os.access(file_path, os.R_OK):
            return {"valid": False, "error": f"File not readable: {file_path}"}

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {"valid": False, "error": f"File is empty: {file_path}"}

        return {"valid": True, "file_size": file_size}

    except Exception as validation_error:
        logger.error(f"File validation failed: {validation_error}", exc_info=True)
        return {"valid": False, "error": str(validation_error)}


def _process_file_in_chunks(
    file_path: str, options: dict, progress_callback=None
) -> dict:
    """Process file content in manageable chunks."""
    import os

    chunk_size = options.get("chunk_size", 8192)  # 8KB chunks
    total_size = os.path.getsize(file_path)
    processed_bytes = 0
    processed_lines = 0

    try:
        with open(file_path, encoding="utf-8") as file_handle:
            while True:
                chunk = file_handle.read(chunk_size)
                if not chunk:
                    break

                # Simulate processing work on the chunk
                chunk_lines = chunk.count("\n")
                processed_lines += chunk_lines
                processed_bytes += len(chunk.encode("utf-8"))

                # Update progress
                if progress_callback:
                    progress_callback(processed_bytes, total_size)

                # Small delay to simulate processing time
                time.sleep(0.01)

        return {
            "processed_bytes": processed_bytes,
            "processed_lines": processed_lines,
            "total_size": total_size,
        }

    except Exception as processing_error:
        logger.error(f"File chunk processing failed: {processing_error}", exc_info=True)
        raise


def _update_file_processing_progress(
    task_instance, current_bytes: int, total_bytes: int
) -> None:
    """Update task progress during file processing."""
    progress_percentage = (
        int((current_bytes / total_bytes) * 100) if total_bytes > 0 else 0
    )

    task_instance.update_state(
        state="PROGRESS",
        meta={
            "current_bytes": current_bytes,
            "total_bytes": total_bytes,
            "progress_percentage": progress_percentage,
            "status": f"Processing file... {progress_percentage}% complete",
        },
    )


def _finalize_file_processing_result(
    processing_result: dict, file_path: str, task_id: str
) -> dict:
    """Finalize and return file processing results."""
    return {
        "status": "completed",
        "file_path": file_path,
        "task_id": task_id,
        "processed_bytes": processing_result["processed_bytes"],
        "processed_lines": processing_result["processed_lines"],
        "file_size": processing_result["total_size"],
        "message": f"Successfully processed {processing_result['processed_lines']} lines from {file_path}",
    }
