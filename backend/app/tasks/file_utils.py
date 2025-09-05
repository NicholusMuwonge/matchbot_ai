"""
File processing utility functions.
"""


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
