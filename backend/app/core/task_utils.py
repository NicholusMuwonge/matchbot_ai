"""
Shared task utilities for consistent task processing patterns.

This module provides reusable task processing utilities similar to Ruby's concerns.
"""

import math
from datetime import datetime, timezone
from typing import Any


class TaskProcessingMixin:
    """Mixin providing common task processing utilities."""

    @staticmethod
    def process_computation_batch(
        batch_number: int, data_size: int = 1000
    ) -> dict[str, Any]:
        """Process a batch of computation-heavy data."""
        # Simulate CPU-intensive work
        result = sum(math.sqrt(i) for i in range(data_size))

        return {
            "batch_number": batch_number,
            "computation_result": round(result, 2),
            "processed_items": data_size,
            "status": "completed",
        }

    @staticmethod
    def finalize_task_result(
        data_size: int,
        task_id: str,
        result_data: Any = None,
        additional_info: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Finalize and return standardized task results."""
        result = {
            "status": "completed",
            "task_id": task_id,
            "processed_items": data_size,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "processing_time": f"{data_size * 0.001:.3f}s",  # Simulated processing time
        }

        if result_data is not None:
            result["result_data"] = result_data

        if additional_info:
            result.update(additional_info)

        return result

    @staticmethod
    def build_task_response(
        status: str, task_id: str, message: str = None, data: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Build standardized task response."""
        response = {
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if message:
            response["message"] = message

        if data:
            response.update(data)

        return response


class FileProcessingMixin:
    """Mixin for file processing task utilities."""

    @staticmethod
    def validate_file_for_processing(file_path: str) -> dict[str, Any]:
        """Validate file for processing with standardized response."""
        import os

        if not os.path.exists(file_path):
            return {"valid": False, "error": "File not found", "file_path": file_path}

        if not os.path.isfile(file_path):
            return {
                "valid": False,
                "error": "Path is not a file",
                "file_path": file_path,
            }

        try:
            file_size = os.path.getsize(file_path)
            return {
                "valid": True,
                "file_path": file_path,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
            }
        except OSError as e:
            return {
                "valid": False,
                "error": f"Cannot access file: {str(e)}",
                "file_path": file_path,
            }

    @staticmethod
    def update_processing_progress(
        file_path: str,
        processed_chunks: int,
        total_chunks: int,
        current_chunk_size: int = 0,
    ) -> dict[str, Any]:
        """Update and format file processing progress."""
        progress_percentage = (
            (processed_chunks / total_chunks) * 100 if total_chunks > 0 else 0
        )

        return {
            "file_path": file_path,
            "processed_chunks": processed_chunks,
            "total_chunks": total_chunks,
            "current_chunk_size": current_chunk_size,
            "progress_percentage": round(progress_percentage, 2),
            "status": "completed" if processed_chunks >= total_chunks else "processing",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def finalize_file_processing(
        file_path: str, total_chunks: int, processing_result: Any = None
    ) -> dict[str, Any]:
        """Finalize file processing with standardized result."""
        result = {
            "file_path": file_path,
            "total_chunks_processed": total_chunks,
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "success": True,
        }

        if processing_result is not None:
            result["processing_result"] = processing_result

        return result


class RedisTaskMixin:
    """Mixin for Redis-related task utilities."""

    @staticmethod
    def create_redis_client_config(redis_url: str) -> dict[str, Any]:
        """Create standardized Redis client configuration."""
        return {
            "url": redis_url,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }

    @staticmethod
    def perform_connection_test(redis_client) -> dict[str, Any]:
        """Perform standardized Redis connection test."""
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_value = "ping"

            # Set operation
            redis_client.set(test_key, test_value, ex=10)  # Expire in 10 seconds

            # Get operation
            retrieved_value = redis_client.get(test_key)
            if retrieved_value:
                retrieved_value = retrieved_value.decode("utf-8")

            # Delete test key
            redis_client.delete(test_key)

            success = retrieved_value == test_value

            return {
                "connection_successful": success,
                "test_operation": "set/get/delete",
                "test_result": "passed" if success else "failed",
                "tested_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            return {
                "connection_successful": False,
                "error": str(e),
                "test_operation": "connection_test",
                "test_result": "failed",
                "tested_at": datetime.now(timezone.utc).isoformat(),
            }

    @staticmethod
    def build_redis_test_response(
        redis_url: str,
        connection_result: dict[str, Any],
        additional_tests: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Build comprehensive Redis test response."""
        response = {
            "redis_url": redis_url,
            "connection_test": connection_result,
            "overall_status": "healthy"
            if connection_result.get("connection_successful")
            else "unhealthy",
            "tested_at": datetime.now(timezone.utc).isoformat(),
        }

        if additional_tests:
            response["additional_tests"] = additional_tests

        return response
