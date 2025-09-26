import os
from datetime import datetime, timedelta, timezone

import pytest

os.environ['MINIO_ACCESS_KEY'] = 'test_access_key'
os.environ['MINIO_SECRET_KEY'] = 'test_secret_key'

from app.services.storage.bucket_manager import BucketManager
from app.services.storage.minio_client import MinIOStorageException


class TestBucketManager:
    """Tests for BucketManager public API."""

    @pytest.fixture
    def mock_config(self, mocker):
        """Mock storage configuration."""
        config = mocker.MagicMock()
        config.required_buckets = ["reconciliation", "reports", "temp"]
        config.MINIO_BUCKET_RECONCILIATION = "reconciliation"
        config.MINIO_BUCKET_REPORTS = "reports"
        config.MINIO_BUCKET_TEMP = "temp"
        config.TEMP_FILE_TTL_HOURS = 1
        config.UNCONFIRMED_FILE_TTL_HOURS = 24
        return config

    @pytest.fixture
    def mock_client(self, mocker):
        """Mock MinIO client."""
        client = mocker.MagicMock()
        client.verify_connection.return_value = True
        client.bucket_exists.return_value = False
        client.make_bucket.return_value = True
        client.list_objects.return_value = []
        return client

    @pytest.fixture
    def manager(self, mock_client, mock_config):
        """Create BucketManager with mocked dependencies."""
        return BucketManager(minio_client=mock_client, config=mock_config)

    # Test: initialize_buckets()
    def test_initialize_buckets_creates_missing(
        self, manager, mock_client, mock_config
    ):
        """Should create all required buckets when missing."""
        mock_client.bucket_exists.return_value = False

        result = manager.initialize_buckets()

        assert result is True
        assert mock_client.make_bucket.call_count == len(mock_config.required_buckets)

    def test_initialize_buckets_handles_connection_failure(self, manager, mock_client):
        """Should fail gracefully when MinIO unavailable."""
        mock_client.verify_connection.return_value = False

        with pytest.raises(MinIOStorageException, match="Cannot connect"):
            manager.initialize_buckets()

    # Test: verify_buckets_health()
    def test_verify_health_all_buckets_exist(self, manager, mock_client, mock_config):
        """Should report healthy when all buckets exist."""
        mock_client.bucket_exists.return_value = True

        health = manager.verify_buckets_health()

        assert health["healthy"] is True
        assert len(health["errors"]) == 0
        for bucket in mock_config.required_buckets:
            assert health["buckets"][bucket]["exists"] is True

    def test_verify_health_detects_missing_buckets(self, manager, mock_client):
        """Should report unhealthy when buckets missing."""
        mock_client.bucket_exists.side_effect = [True, False, True]

        health = manager.verify_buckets_health()

        assert health["healthy"] is False
        assert len(health["errors"]) > 0

    # Test: bucket_exists()
    def test_bucket_exists_returns_boolean(self, manager, mock_client):
        """Should return True/False based on bucket existence."""
        mock_client.bucket_exists.return_value = True
        assert manager.bucket_exists("test") is True

        mock_client.bucket_exists.return_value = False
        assert manager.bucket_exists("test") is False

    # Test: create_bucket_if_not_exists()
    def test_create_bucket_if_not_exists(self, manager, mock_client):
        """Should create bucket only when missing."""
        mock_client.bucket_exists.return_value = False

        result = manager.create_bucket_if_not_exists("new-bucket")

        assert result is True
        mock_client.make_bucket.assert_called_once()

    # Test: delete_bucket_if_exists()
    def test_delete_bucket_removes_empty_bucket(self, manager, mock_client):
        """Should delete empty bucket."""
        mock_client.bucket_exists.return_value = True
        mock_client.list_objects.return_value = []
        mock_raw_client = mock_client.get_client.return_value

        result = manager.delete_bucket_if_exists("test-bucket")

        assert result is True
        mock_raw_client.remove_bucket.assert_called_once_with("test-bucket")

    def test_delete_bucket_force_removes_with_objects(
        self, manager, mock_client, mocker
    ):
        """Should delete bucket and its contents when force=True."""
        mock_client.bucket_exists.return_value = True
        mock_obj = mocker.Mock(object_name="file.txt")
        mock_client.list_objects.return_value = [mock_obj]

        result = manager.delete_bucket_if_exists("test-bucket", force=True)

        assert result is True
        mock_client.remove_object.assert_called_once_with("test-bucket", "file.txt")

    # Test: cleanup_expired_files()
    def test_cleanup_expired_files_removes_old_files(
        self, manager, mock_client, mocker
    ):
        """Should delete files older than TTL."""
        now = datetime.now(timezone.utc)
        old_file = mocker.Mock(
            object_name="old.csv", last_modified=now - timedelta(hours=25)
        )
        recent_file = mocker.Mock(
            object_name="recent.csv", last_modified=now - timedelta(minutes=30)
        )
        mock_client.list_objects.side_effect = [
            [old_file, recent_file],  # temp bucket
            [],  # reconciliation bucket
        ]

        stats = manager.cleanup_expired_files()

        assert stats["temp_deleted"] == 1
        mock_client.remove_object.assert_called_once_with("temp", "old.csv")

    # Test: get_bucket_statistics()
    def test_get_bucket_statistics(self, manager, mock_client, mocker):
        """Should return bucket metrics."""
        mock_client.bucket_exists.return_value = True
        mock_client.list_objects.return_value = [
            mocker.Mock(
                object_name="f1", size=100, last_modified=datetime.now(timezone.utc)
            ),
            mocker.Mock(
                object_name="f2", size=200, last_modified=datetime.now(timezone.utc)
            ),
        ]

        stats = manager.get_bucket_statistics("test-bucket")

        assert stats["exists"] is True
        assert stats["file_count"] == 2
        assert stats["total_size"] == 300


class TestIntegrationScenarios:
    """Integration tests for real-world usage patterns."""

    def test_bucket_lifecycle(self, mocker):
        """Test complete bucket lifecycle: create, use, cleanup."""
        mock_client = mocker.MagicMock()
        mock_client.verify_connection.return_value = True
        mock_client.bucket_exists.side_effect = [False, True, True, False]
        mock_client.make_bucket.return_value = True

        manager = BucketManager(minio_client=mock_client)

        # Create bucket
        assert manager.create_bucket_if_not_exists("lifecycle-test") is True

        # Verify it exists
        assert manager.bucket_exists("lifecycle-test") is True

        # Delete it
        assert manager.delete_bucket_if_exists("lifecycle-test") is True

        # Verify it's gone
        assert manager.bucket_exists("lifecycle-test") is False
