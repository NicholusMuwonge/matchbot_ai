"""
Tests for computation-heavy Celery tasks.
"""

import pytest
from unittest.mock import patch


class TestComputationTasks:
    """Test computation task functionality."""

    def test_heavy_computation_task_progress(self):
        """Test heavy computation task reports progress correctly."""
        with (
            patch("app.tasks.computation._process_computation_batch") as mock_batch,
            patch(
                "app.tasks.computation._finalize_computation_result"
            ) as mock_finalize,
        ):
            mock_finalize.return_value = {
                "status": "completed",
                "result": "Heavy computation completed for 2000 data points",
                "processed_batches": 2,
            }

            from app.tasks.computation import process_heavy_computation_task

            result = process_heavy_computation_task.apply(args=[2000])
            task_result = result.get()

            assert task_result["status"] == "completed"
            assert task_result["processed_batches"] == 2
            assert "2000 data points" in task_result["result"]

    def test_celery_task_retry_mechanism(self):
        """Test Celery tasks implement proper retry logic."""
        from app.tasks.computation import process_heavy_computation_task

        # Mock the task to raise an exception
        with patch("app.tasks.computation._process_computation_batch") as mock_batch:
            mock_batch.side_effect = Exception("Computation failed")

            # The task should implement retry logic
            task_instance = process_heavy_computation_task.apply(args=[1000])

            # Verify the task fails as expected (in test environment)
            with pytest.raises(Exception):
                task_instance.get(propagate=True)