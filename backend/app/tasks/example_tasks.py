"""
Legacy task imports for backward compatibility.
"""

# Import all tasks from individual modules for backward compatibility
from .computation import process_heavy_computation_task
from .file_processing import process_large_file_upload_task
from .redis_utils import add_numbers, test_redis_connection

# Re-export for backward compatibility
__all__ = [
    "process_heavy_computation_task",
    "process_large_file_upload_task",
    "add_numbers",
    "test_redis_connection"
]
