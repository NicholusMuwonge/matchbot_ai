"""
Tests for Redis-related Celery tasks.
"""

from unittest.mock import patch


class TestRedisTasks:
    """Test Redis-related task functionality."""

    def test_add_numbers_task(self):
        """Test basic add_numbers task execution."""
        from app.tasks.redis_utils import add_numbers

        result = add_numbers.apply(args=[5, 3])
        assert result.get() == 8

    def test_redis_connection_task_success(self):
        """Test Redis connection task succeeds with valid Redis."""
        with (
            patch("app.tasks.redis_utils._create_redis_client"),
            patch("app.tasks.redis_utils._perform_redis_connection_test") as mock_test,
        ):
            mock_test.return_value = {
                "success": True,
                "message": "Redis operations completed successfully",
            }

            from app.tasks.redis_utils import test_redis_connection

            result = test_redis_connection.apply()
            task_result = result.get()

            assert task_result["status"] == "success"
            assert task_result["test_passed"] is True
