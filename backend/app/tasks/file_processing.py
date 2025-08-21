"""
File processing tasks for I/O-bound operations.
"""

import logging
from app.core.celery import celery_app
from app.core.config import settings
from .file_utils import _update_file_processing_progress, _finalize_file_processing_result
from .file_validation import _validate_file_for_processing, _process_file_in_chunks

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    time_limit=settings.FILE_PROCESSING_TASK_TIME_LIMIT,
    soft_time_limit=settings.FILE_PROCESSING_TASK_SOFT_TIME_LIMIT
)
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


