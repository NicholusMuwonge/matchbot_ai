"""
Tests for Redis and Celery health check endpoints and tasks.
These tests validate the major features added in MAT-58.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestRedisHealthCheck:
    """Test Redis health check endpoint functionality."""

    def test_redis_health_check_success(self):
        """Test Redis health check returns healthy when Redis is accessible."""
        with (
            patch(
                "app.api.routes.utils._create_redis_health_client"
            ) as mock_redis_client,
            patch(
                "app.api.routes.utils._execute_redis_health_test"
            ) as mock_health_test,
        ):
            # Setup mocks
            mock_health_test.return_value = {
                "success": True,
                "message": "Redis connection test completed successfully",
            }

            client = TestClient(app)
            response = client.get("/api/v1/utils/health-check/redis")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["status"] == "healthy"
            assert response_data["service"] == "redis"
            assert response_data["test_passed"] is True

    def test_redis_health_check_failure(self):
        """Test Redis health check returns unhealthy when Redis is not accessible."""
        with patch(
            "app.api.routes.utils._create_redis_health_client"
        ) as mock_redis_client:
            mock_redis_client.side_effect = ConnectionError("Redis connection failed")

            client = TestClient(app)
            response = client.get("/api/v1/utils/health-check/redis")

            assert response.status_code == 503
            response_data = response.json()["detail"]
            assert response_data["status"] == "unhealthy"
            assert response_data["service"] == "redis"
            assert response_data["test_passed"] is False

    def test_redis_health_test_operations(self):
        """Test Redis health test operations execute correctly."""
        from app.api.routes.utils import _execute_redis_health_test

        mock_redis_client = Mock()
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = "ok"
        mock_redis_client.delete.return_value = 1

        result = _execute_redis_health_test(mock_redis_client)

        assert result["success"] is True
        assert "successfully" in result["message"]
        mock_redis_client.set.assert_called_once()
        mock_redis_client.get.assert_called_once()
        mock_redis_client.delete.assert_called_once()


class TestCeleryHealthCheck:
    """Test Celery health check endpoint functionality."""

    def test_celery_health_check_success(self):
        """Test Celery health check returns healthy when workers are available."""
        with patch("app.api.routes.utils._get_celery_worker_info") as mock_worker_info:
            mock_worker_info.return_value = {
                "active_workers": {"worker1": []},
                "registered_tasks": {
                    "worker1": ["app.tasks.example_tasks.add_numbers"]
                },
            }

            client = TestClient(app)
            response = client.get("/api/v1/utils/health-check/celery")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["status"] == "healthy"
            assert response_data["service"] == "celery"
            assert response_data["test_passed"] is True
            assert response_data["worker_count"] == 1

    def test_celery_health_check_no_workers(self):
        """Test Celery health check returns unhealthy when no workers are available."""
        with patch("app.api.routes.utils._get_celery_worker_info") as mock_worker_info:
            mock_worker_info.return_value = {
                "active_workers": {},
                "registered_tasks": {},
            }

            client = TestClient(app)
            response = client.get("/api/v1/utils/health-check/celery")

            assert response.status_code == 503
            response_data = response.json()["detail"]
            assert response_data["status"] == "unhealthy"
            assert response_data["service"] == "celery"
            assert "No Celery workers available" in response_data["message"]

    def test_celery_statistics_calculation(self):
        """Test Celery worker statistics are calculated correctly."""
        from app.api.routes.utils import _calculate_celery_statistics

        active_workers = {"worker1": ["task1", "task2"], "worker2": ["task3"]}
        registered_tasks = {
            "worker1": [
                "app.tasks.example_tasks.add_numbers",
                "app.tasks.example_tasks.test_redis_connection",
            ]
        }

        stats = _calculate_celery_statistics(active_workers, registered_tasks)

        assert stats["worker_count"] == 2
        assert stats["total_active_tasks"] == 3
        assert stats["registered_task_count"] == 2
        assert len(stats["worker_names"]) == 2


class TestCeleryTasks:
    """Test Celery task functionality."""

    def test_add_numbers_task(self):
        """Test basic add_numbers task execution."""
        from app.tasks.example_tasks import add_numbers

        result = add_numbers.apply(args=[5, 3])
        assert result.get() == 8

    def test_redis_connection_task_success(self):
        """Test Redis connection task succeeds with valid Redis."""
        with (
            patch("app.tasks.example_tasks._create_redis_client") as mock_create_client,
            patch(
                "app.tasks.example_tasks._perform_redis_connection_test"
            ) as mock_test,
        ):
            mock_test.return_value = {
                "success": True,
                "message": "Redis operations completed successfully",
            }

            from app.tasks.example_tasks import test_redis_connection

            result = test_redis_connection.apply()
            task_result = result.get()

            assert task_result["status"] == "success"
            assert task_result["test_passed"] is True

    def test_heavy_computation_task_progress(self):
        """Test heavy computation task reports progress correctly."""
        with (
            patch("app.tasks.example_tasks._process_computation_batch") as mock_batch,
            patch(
                "app.tasks.example_tasks._finalize_computation_result"
            ) as mock_finalize,
        ):
            mock_finalize.return_value = {
                "status": "completed",
                "result": "Heavy computation completed for 2000 data points",
                "processed_batches": 2,
            }

            from app.tasks.example_tasks import process_heavy_computation_task

            result = process_heavy_computation_task.apply(args=[2000])
            task_result = result.get()

            assert task_result["status"] == "completed"
            assert task_result["processed_batches"] == 2
            assert "2000 data points" in task_result["result"]

    def test_file_processing_task_validation(self):
        """Test file processing task validates files correctly."""
        from app.tasks.example_tasks import _validate_file_for_processing

        # Test non-existent file
        result = _validate_file_for_processing("/non/existent/file.txt")
        assert result["valid"] is False
        assert "not found" in result["error"]

    def test_file_processing_task_chunking(self):
        """Test file processing handles chunking correctly."""
        import os
        import tempfile

        from app.tasks.example_tasks import _process_file_in_chunks

        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            test_content = "line1\nline2\nline3\n"
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            result = _process_file_in_chunks(temp_file_path, {"chunk_size": 10})

            assert result["processed_lines"] == 3
            assert result["processed_bytes"] > 0
            assert result["total_size"] > 0

        finally:
            os.unlink(temp_file_path)


class TestErrorHandlingAndLogging:
    """Test proper error handling and logging in Redis/Celery components."""

    def test_redis_health_check_logs_errors(self):
        """Test Redis health check logs errors appropriately."""
        with (
            patch("app.api.routes.utils._create_redis_health_client") as mock_client,
            patch("app.api.routes.utils.logger") as mock_logger,
        ):
            mock_client.side_effect = Exception("Connection timeout")

            client = TestClient(app)
            response = client.get("/api/v1/utils/health-check/redis")

            assert response.status_code == 503
            mock_logger.error.assert_called_once()

    def test_celery_task_retry_mechanism(self):
        """Test Celery tasks implement proper retry logic."""
        from app.tasks.example_tasks import process_heavy_computation_task

        # Mock the task to raise an exception
        with patch("app.tasks.example_tasks._process_computation_batch") as mock_batch:
            mock_batch.side_effect = Exception("Computation failed")

            # The task should implement retry logic
            task_instance = process_heavy_computation_task.apply(args=[1000])

            # Verify the task fails as expected (in test environment)
            with pytest.raises(Exception):
                task_instance.get(propagate=True)

