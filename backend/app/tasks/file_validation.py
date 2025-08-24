"""
File validation utilities for file processing tasks.
"""

import logging

logger = logging.getLogger(__name__)


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
    import time

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
