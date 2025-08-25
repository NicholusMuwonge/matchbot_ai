"""
Legacy test imports for backward compatibility.
These tests validate the major features added in MAT-58.
"""

# Import all test classes from individual modules for backward compatibility
# from ...tasks.test_computation_tasks import TestComputationTasks  # Disabled due to flaky tests
from ...tasks.test_file_tasks import TestFileProcessingTasks
from ...tasks.test_redis_tasks import TestRedisTasks

# Re-export for backward compatibility
__all__ = [
    "TestRedisTasks",
    "TestFileProcessingTasks",
]  # "TestComputationTasks" disabled

# Create aliases for legacy compatibility
TestCeleryTasks = TestRedisTasks
