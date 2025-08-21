"""
Tests for Celery health check endpoints.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


class TestCeleryHealthCheck:
    """Test Celery health check endpoint functionality."""

    def test_celery_health_check_success(self):
        """Test Celery health check returns healthy when workers are available."""
        with patch("app.api.routes.health.celery._get_celery_worker_info") as mock_worker_info:
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
        with patch("app.api.routes.health.celery._get_celery_worker_info") as mock_worker_info:
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
        from app.api.routes.health.celery import _calculate_celery_statistics

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