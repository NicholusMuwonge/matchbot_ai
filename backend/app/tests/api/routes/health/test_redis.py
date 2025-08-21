"""
Tests for Redis health check endpoints.
"""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app


class TestRedisHealthCheck:
    """Test Redis health check endpoint functionality."""

    def test_redis_health_check_success(self):
        """Test Redis health check returns healthy when Redis is accessible."""
        with (
            patch(
                "app.api.routes.health.redis._create_redis_health_client"
            ) as mock_redis_client,
            patch(
                "app.api.routes.health.redis._execute_redis_health_test"
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
            "app.api.routes.health.redis._create_redis_health_client"
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
        from app.api.routes.health.redis import _execute_redis_health_test

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

    def test_redis_health_check_logs_errors(self):
        """Test Redis health check logs errors appropriately."""
        with (
            patch("app.api.routes.health.redis._create_redis_health_client") as mock_client,
            patch("app.api.routes.health.redis.logger") as mock_logger,
        ):
            mock_client.side_effect = Exception("Connection timeout")

            client = TestClient(app)
            response = client.get("/api/v1/utils/health-check/redis")

            assert response.status_code == 503
            mock_logger.error.assert_called_once()