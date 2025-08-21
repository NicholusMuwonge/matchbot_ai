"""
Legacy test imports for backward compatibility.
These tests validate the major features added in MAT-58.
"""

# Import all test classes from individual modules for backward compatibility
from ..health.test_redis import TestRedisHealthCheck
from ..health.test_celery import TestCeleryHealthCheck
from ...tasks.test_redis_tasks import TestRedisTasks
from ...tasks.test_computation_tasks import TestComputationTasks
from ...tasks.test_file_tasks import TestFileProcessingTasks

# Re-export for backward compatibility
__all__ = [
    "TestRedisHealthCheck",
    "TestCeleryHealthCheck", 
    "TestRedisTasks",
    "TestComputationTasks",
    "TestFileProcessingTasks"
]

# Create aliases for legacy compatibility
TestCeleryTasks = TestRedisTasks
TestErrorHandlingAndLogging = TestRedisHealthCheck