import os
from datetime import datetime, timezone

import pytest

os.environ["MINIO_ACCESS_KEY"] = "test_access_key"
os.environ["MINIO_SECRET_KEY"] = "test_secret_key"

from app.services.storage.minio_client import MinIOStorageException
from app.services.storage.presigned_url_service import PresignedURLService


@pytest.fixture
def mock_config(mocker):
    config = mocker.MagicMock()
    config.MINIO_ENDPOINT = "localhost:9000"
    config.MINIO_ACCESS_KEY = "test_access_key"
    config.MINIO_SECRET_KEY = "secret_key"
    config.MINIO_SECURE = False
    config.MINIO_REGION = "us-east-1"
    config.MINIO_BUCKET_RECONCILIATION = "reconciliation-files"
    config.MINIO_BUCKET_REPORTS = "reports"
    config.RECONCILIATION_FILES_PREFIX = "files"
    config.RECONCILIATION_RESULTS_PREFIX = "results"
    config.UPLOAD_PRESIGNED_URL_EXPIRY = 3600
    config.DOWNLOAD_PRESIGNED_URL_EXPIRY = 1800
    config.UPLOAD_MAX_FILE_SIZE = 10485760
    config.UPLOAD_ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".json"]
    config.minio_url = "http://localhost:9000"
    config.is_file_allowed = mocker.MagicMock(return_value=True)
    config.get_content_type = mocker.MagicMock(return_value="text/csv")
    return config


@pytest.fixture
def mock_minio_client(mocker):
    mock_client_service = mocker.MagicMock()
    mock_client = mocker.MagicMock()
    mock_client_service.get_client.return_value = mock_client
    return mock_client_service, mock_client


@pytest.fixture
def presigned_service(mock_minio_client, mock_config):
    mock_client_service, _ = mock_minio_client
    return PresignedURLService(minio_client=mock_client_service, config=mock_config)


class TestFileOperations:
    def test_verify_file_exists_true(
        self, presigned_service, mock_minio_client, mocker
    ):
        mock_client_service, _ = mock_minio_client
        mock_stat = mocker.MagicMock()
        mock_client_service.stat_object.return_value = mock_stat

        result = presigned_service.verify_file_exists("bucket", "object.csv")
        assert result is True

    def test_verify_file_exists_false(self, presigned_service, mock_minio_client):
        mock_client_service, _ = mock_minio_client
        mock_client_service.stat_object.side_effect = Exception("Not found")

        result = presigned_service.verify_file_exists("bucket", "missing.csv")
        assert result is False

    def test_get_file_metadata_success(
        self, presigned_service, mock_minio_client, mocker
    ):
        mock_client_service, _ = mock_minio_client

        mock_stat = mocker.MagicMock()
        mock_stat.size = 2048
        mock_stat.etag = "metadata-etag"
        mock_stat.content_type = "application/json"
        mock_stat.last_modified = datetime(2024, 1, 1, 15, 30, 0, tzinfo=timezone.utc)
        mock_stat.metadata = {"custom": "metadata"}
        mock_client_service.stat_object.return_value = mock_stat

        result = presigned_service.get_file_metadata("bucket", "file.json")

        assert result["size"] == 2048
        assert result["etag"] == "metadata-etag"
        assert result["content_type"] == "application/json"
        assert result["metadata"] == {"custom": "metadata"}

    def test_get_file_metadata_file_not_found(
        self, presigned_service, mock_minio_client
    ):
        mock_client_service, _ = mock_minio_client
        mock_client_service.stat_object.return_value = None

        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service.get_file_metadata("bucket", "missing.txt")
        assert "File not found" in str(exc_info.value)

    def test_delete_file_success(self, presigned_service, mock_minio_client):
        mock_client_service, _ = mock_minio_client
        mock_client_service.remove_object.return_value = True

        result = presigned_service.delete_file("bucket", "file.csv")
        assert result is True
        mock_client_service.remove_object.assert_called_once_with("bucket", "file.csv")

    def test_delete_file_failure(self, presigned_service, mock_minio_client):
        mock_client_service, _ = mock_minio_client
        mock_client_service.remove_object.side_effect = Exception("Delete failed")

        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service.delete_file("bucket", "file.csv")
        assert "Could not delete file" in str(exc_info.value)


class TestListFiles:
    def test_list_files_success(self, presigned_service, mock_minio_client, mocker):
        mock_client_service, _ = mock_minio_client

        mock_obj1 = mocker.MagicMock()
        mock_obj1.object_name = "file1.csv"
        mock_obj1.size = 1024
        mock_obj1.etag = "etag1"
        mock_obj1.last_modified = datetime(2024, 1, 1, tzinfo=timezone.utc)

        mock_obj2 = mocker.MagicMock()
        mock_obj2.object_name = "file2.json"
        mock_obj2.size = 2048
        mock_obj2.etag = "etag2"
        mock_obj2.last_modified = datetime(2024, 1, 2, tzinfo=timezone.utc)

        mock_client_service.list_objects.return_value = [mock_obj1, mock_obj2]

        result = presigned_service.list_files("test-bucket", prefix="docs/")

        assert len(result) == 2
        assert result[0]["key"] == "file1.csv"
        assert result[0]["size"] == 1024
        assert result[1]["key"] == "file2.json"
        assert result[1]["size"] == 2048

    def test_list_files_empty(self, presigned_service, mock_minio_client):
        mock_client_service, _ = mock_minio_client
        mock_client_service.list_objects.return_value = []

        result = presigned_service.list_files("empty-bucket")
        assert result == []


class TestStreamFileContent:
    def test_stream_file_content_success(
        self, presigned_service, mock_minio_client, mocker
    ):
        mock_client_service, _ = mock_minio_client

        mock_response = mocker.MagicMock()
        mock_response.read.side_effect = [b"chunk1", b"chunk2", b""]
        mock_client_service.get_object.return_value = mock_response

        chunks = list(presigned_service.stream_file_content("bucket", "file.txt"))

        assert chunks == [b"chunk1", b"chunk2"]
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    def test_stream_file_content_error(self, presigned_service, mock_minio_client):
        mock_client_service, _ = mock_minio_client
        mock_client_service.get_object.side_effect = Exception("Stream failed")

        with pytest.raises(MinIOStorageException) as exc_info:
            list(presigned_service.stream_file_content("bucket", "file.txt"))
        assert "Could not stream file" in str(exc_info.value)


class TestBucketOperations:
    def test_ensure_bucket_exists_already_exists(
        self, presigned_service, mock_minio_client
    ):
        mock_client_service, _ = mock_minio_client
        mock_client_service.bucket_exists.return_value = True

        presigned_service._ensure_bucket_exists("existing-bucket")

        mock_client_service.bucket_exists.assert_called_once_with("existing-bucket")
        mock_client_service.make_bucket.assert_not_called()

    def test_ensure_bucket_exists_creates_new(
        self, presigned_service, mock_minio_client
    ):
        mock_client_service, _ = mock_minio_client
        mock_client_service.bucket_exists.return_value = False

        presigned_service._ensure_bucket_exists("new-bucket")

        mock_client_service.bucket_exists.assert_called_once_with("new-bucket")
        mock_client_service.make_bucket.assert_called_once_with("new-bucket")

    def test_ensure_bucket_exists_error(self, presigned_service, mock_minio_client):
        mock_client_service, _ = mock_minio_client
        mock_client_service.bucket_exists.side_effect = Exception("Bucket check failed")

        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service._ensure_bucket_exists("error-bucket")
        assert "Bucket operation failed" in str(exc_info.value)
