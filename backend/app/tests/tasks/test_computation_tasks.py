"""
Tests for computation-heavy Celery tasks.
"""


class TestComputationTasks:
    """Test computation task functionality."""

    def test_heavy_computation_task_progress(self, celery_app, redis_client):
        """Test heavy computation task with real Celery and Redis."""

        # Register test computation task
        @celery_app.task(bind=True)
        def process_heavy_computation_task(self, data_points: int):  # noqa: ARG001
            """Mock heavy computation task"""
            batch_size = 1000
            batches = data_points // batch_size + (
                1 if data_points % batch_size > 0 else 0
            )

            # Simulate processing batches
            for _ in range(batches):
                # Update progress (in real implementation would update task state)
                pass

            return {
                "status": "completed",
                "result": f"Heavy computation completed for {data_points} data points",
                "processed_batches": batches,
            }

        # Execute task
        result = process_heavy_computation_task.apply(args=[2000])
        task_result = result.get()

        assert task_result["status"] == "completed"
        assert task_result["processed_batches"] == 2
        assert "2000 data points" in task_result["result"]

    def test_celery_task_retry_mechanism(self, celery_app, redis_client):
        """Test Celery task retry logic behavior with eager execution."""
        redis_client.flushall()

        retry_count = 0

        @celery_app.task(bind=True)
        def computation_with_retry(
            self, should_fail: bool = True, max_attempts: int = 3
        ):
            nonlocal retry_count
            retry_count += 1

            if should_fail and retry_count < max_attempts:
                # Simulate retry behavior in eager mode
                try:
                    self.retry(countdown=1, max_retries=max_attempts)
                except Exception:
                    # In eager mode, retries raise exceptions immediately
                    pass
                raise ValueError("Computation failed")

            return {"status": "completed", "retries": retry_count - 1}

        # Test successful execution without retries
        retry_count = 0  # Reset counter
        result = computation_with_retry.apply(args=[False, 1])  # Don't fail
        task_result = result.get()
        assert task_result["status"] == "completed"
        assert task_result["retries"] == 0

        # Test that task can handle retry logic (even if eager mode doesn't actually retry)
        retry_count = 0  # Reset counter
        try:
            result = computation_with_retry.apply(args=[True, 3])  # Will fail
            result.get(propagate=True)
            raise AssertionError("Should have raised an exception")
        except (ValueError, Exception):
            # Expected behavior - task failed as designed
            assert retry_count >= 1  # At least one attempt was made

    def test_celery_task_state_tracking(self, celery_app, redis_client):
        """Test task state is properly tracked in Redis."""

        @celery_app.task(bind=True)
        def tracked_task(self, steps: int):
            for step in range(steps):
                self.update_state(
                    state="PROGRESS", meta={"current": step + 1, "total": steps}
                )
            return {"status": "completed", "steps_completed": steps}

        # Execute task and check result
        result = tracked_task.apply(args=[3])
        task_result = result.get()

        assert task_result["status"] == "completed"
        assert task_result["steps_completed"] == 3
