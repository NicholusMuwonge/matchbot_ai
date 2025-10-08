"""Tests for process_uploaded_file task."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models.file import File, FileStatus, StorageProvider
from app.tasks.file.process_file import process_uploaded_file


@pytest.fixture
def uploaded_file(db: Session):
    """Create a file record in UPLOADED status ready for processing."""
    user_id = uuid4()
    file = File(
        id=uuid4(),
        external_id="ext_test_123",
        user_id=user_id,
        filename="test_transactions.csv",
        storage_path="source/test_user/test_transactions.csv",
        content_type="text/csv",
        file_size_bytes=0,
        status=FileStatus.UPLOADED,
        provider=StorageProvider.MINIO,
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


class TestProcessUploadedFile:
    """Test process_uploaded_file task."""

    @patch("app.tasks.file.process_file.minio_client_service")
    def test_process_uploaded_file_success(
        self, mock_minio, db: Session, uploaded_file: File
    ):
        """Test successful file processing without duplicates.

        Scenario:
        - File exists in database with UPLOADED status
        - File successfully fetched from MinIO
        - Hash calculated correctly
        - No duplicate files found
        - File status updated to SYNCED
        - Metadata stored with correct size
        """

        test_content = b"Date,Amount,Description\n2025-01-01,100.50,Test transaction"

        mock_response = MagicMock()
        mock_response.read.return_value = test_content
        mock_minio.get_object.return_value = mock_response

        # Act
        process_uploaded_file(str(uploaded_file.id))

        # Assert - Verify MinIO was called correctly
        mock_minio.get_object.assert_called_once_with(
            bucket_name="reconciliation",
            object_name=uploaded_file.storage_path,
        )

        # Assert - Verify file status updated
        db.refresh(uploaded_file)
        assert uploaded_file.status == FileStatus.SYNCED

        # Assert - Verify hash was calculated and stored
        assert uploaded_file.file_hash is not None
        assert len(uploaded_file.file_hash) == 64  # SHA256 hash length

        # Assert - Verify metadata stored correctly
        assert uploaded_file.file_metadata is not None
        assert uploaded_file.file_metadata["size_bytes"] == len(test_content)
        assert "deduplicated" not in uploaded_file.file_metadata

        # Assert - Verify no MinIO delete was called (not a duplicate)
        mock_minio.delete_object.assert_not_called()
