"""
Tests for file processing Celery tasks.
"""

import os
import tempfile


class TestFileProcessingTasks:
    """Test file processing task functionality."""

    def test_file_processing_task_validation(self):
        """Test file processing task validates files correctly."""
        from app.tasks.file_processing import _validate_file_for_processing

        # Test non-existent file
        result = _validate_file_for_processing("/non/existent/file.txt")
        assert result["valid"] is False
        assert "not found" in result["error"]

    def test_file_processing_task_chunking(self):
        """Test file processing handles chunking correctly."""
        from app.tasks.file_processing import _process_file_in_chunks

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