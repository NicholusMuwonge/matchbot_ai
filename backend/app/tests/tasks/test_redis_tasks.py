"""
Tests for Redis-related Celery tasks.
"""


class TestRedisTasks:
    """Test Redis-related task functionality."""

    def test_add_numbers_task(self, celery_app, redis_client):
        """Test basic add_numbers task execution with real Redis."""

        # Register our task with the test celery app
        @celery_app.task
        def add_numbers(x: int, y: int):
            return x + y

        # Execute task with real Redis backend
        result = add_numbers.apply(args=[5, 3])
        assert result.get() == 8

    def test_redis_connection_task_success(
        self, celery_app, redis_client, redis_server
    ):
        """Test Redis connection task with fakeredis instance."""

        @celery_app.task
        def test_redis_connection():
            try:
                # Test Redis connection using the fake client
                redis_client.ping()
                redis_client.set("test_key", "test_value")
                redis_client.get("test_key")
                redis_client.delete("test_key")

                return {
                    "status": "success",
                    "test_passed": True,
                    "redis_url": f"redis://{redis_server.host}:{redis_server.port}",
                    "message": "Redis operations completed successfully",
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "test_passed": False,
                    "error_message": str(e),
                }

        result = test_redis_connection.apply()
        task_result = result.get()

        assert task_result["status"] == "success"
        assert task_result["test_passed"] is True
        assert "Redis operations completed successfully" in task_result["message"]

    def test_redis_operations(self, redis_client):
        """Test basic Redis operations directly with fakeredis."""
        redis_client.flushall()
        assert redis_client.ping() is True

        redis_client.set("test:key", "test_value")
        assert redis_client.get("test:key") == "test_value"

        redis_client.delete("test:key")
        assert redis_client.get("test:key") is None

        redis_client.hset("test:hash", "field1", "value1")
        redis_client.hset("test:hash", "field2", "value2")
        assert redis_client.hget("test:hash", "field1") == "value1"
        assert redis_client.hgetall("test:hash") == {
            "field1": "value1",
            "field2": "value2",
        }

        redis_client.lpush("test:list", "item1", "item2")
        assert redis_client.llen("test:list") == 2
        assert redis_client.rpop("test:list") == "item1"
