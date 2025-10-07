"""
Integration tests for process_uploaded_file Celery task.
Tests file syncing, hash calculation, and Redis caching.
"""

import hashlib
import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from app.models.file import File, FileStatus, StorageProvider
from app.services.cache.redis_client import redis_client
from app.tasks.file.process_file import process_uploaded_file


@pytest.fixture
def test_file_content():
    """Sample file content for testing."""
    return b"Test file content for processing and caching"


@pytest.fixture
def test_file_record(session: Session, test_file_content):
    """Create a test file record in UPLOADED status."""
    file = File(
        id=uuid.uuid4(),
        external_id=f"test-{uuid.uuid4()}",
        user_id=uuid.uuid4(),
        filename="test_file.txt",
        storage_path="test/path/test_file.txt",
        content_type="text/plain",
        file_size_bytes=len(test_file_content),
        status=FileStatus.UPLOADED,
        provider=StorageProvider.MINIO,
    )
    session.add(file)
    session.commit()
    session.refresh(file)
    return file


class TestProcessUploadedFile:
    """Test process_uploaded_file Celery task."""

    def test_process_file_success(
        self, session: Session, test_file_record: File, test_file_content: bytes
    ):
        """Test successful file processing: status change, hash calculation, Redis caching."""
        # Mock MinIO client to return test content
        mock_stream = MagicMock()
        mock_stream.read.return_value = test_file_content

        with patch(
            "app.tasks.file.process_file.minio_client_service.get_object",
            return_value=mock_stream,
        ):
            # Execute task
            process_uploaded_file(str(test_file_record.id))

        # Refresh from DB
        session.expire(test_file_record)
        file = session.exec(select(File).where(File.id == test_file_record.id)).first()

        # Verify status changed to SYNCED
        assert file.status == FileStatus.SYNCED

        # Verify hash was calculated and stored
        expected_hash = hashlib.sha256(test_file_content).hexdigest()
        assert file.file_hash == expected_hash

        # Verify metadata stored in content field
        assert file.content is not None
        assert file.content["size_bytes"] == len(test_file_content)
        assert file.content["hash"] == expected_hash
        assert file.content["cached_at"] == "redis"

        # Verify content cached in Redis
        cache_key = f"file_content:{file.id}"
        cached_content = redis_client.get(cache_key)
        assert cached_content is not None
        assert cached_content == test_file_content

        # Cleanup
        redis_client.delete(cache_key)

    def test_process_file_not_found(self, session: Session):
        """Test task handles missing file gracefully."""
        fake_id = str(uuid.uuid4())

        # Should not raise exception, just log error
        process_uploaded_file(fake_id)

        # No file should be created
        file = session.exec(select(File).where(File.id == uuid.UUID(fake_id))).first()
        assert file is None

    def test_process_file_wrong_status(
        self, session: Session, test_file_content: bytes
    ):
        """Test task skips files not in UPLOADED status."""
        # Create file in PENDING status
        file = File(
            id=uuid.uuid4(),
            external_id=f"test-{uuid.uuid4()}",
            user_id=uuid.uuid4(),
            filename="test_file.txt",
            storage_path="test/path/test_file.txt",
            content_type="text/plain",
            file_size_bytes=len(test_file_content),
            status=FileStatus.PENDING,  # Wrong status
            provider=StorageProvider.MINIO,
        )
        session.add(file)
        session.commit()

        # Execute task
        process_uploaded_file(str(file.id))

        # Refresh from DB
        session.expire(file)
        file = session.exec(select(File).where(File.id == file.id)).first()

        # Status should remain PENDING
        assert file.status == FileStatus.PENDING
        assert file.file_hash is None

    def test_process_file_fatal_error(
        self, session: Session, test_file_record: File, test_file_content: bytes
    ):
        """Test task handles fatal errors and marks file as FAILED."""
        # Mock MinIO client to raise non-retryable exception
        with patch(
            "app.tasks.file.process_file.minio_client_service.get_object",
            side_effect=ValueError("Fatal error"),
        ):
            # Execute task
            process_uploaded_file(str(test_file_record.id))

        # Refresh from DB
        session.expire(test_file_record)
        file = session.exec(select(File).where(File.id == test_file_record.id)).first()

        # Verify status changed to FAILED
        assert file.status == FileStatus.FAILED
        assert file.failure_reason == "Fatal error"

    def test_redis_cache_ttl(
        self, session: Session, test_file_record: File, test_file_content: bytes
    ):
        """Test Redis cache is set with 24-hour TTL."""
        mock_stream = MagicMock()
        mock_stream.read.return_value = test_file_content

        with patch(
            "app.tasks.file.process_file.minio_client_service.get_object",
            return_value=mock_stream,
        ):
            process_uploaded_file(str(test_file_record.id))

        # Check TTL in Redis
        cache_key = f"file_content:{test_file_record.id}"
        ttl = redis_client.ttl(cache_key)

        # TTL should be around 86400 seconds (24 hours), allow some variance
        assert 86300 < ttl <= 86400

        # Cleanup
        redis_client.delete(cache_key)
