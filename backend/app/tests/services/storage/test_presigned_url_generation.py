import os
from datetime import datetime, timedelta, timezone

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


class TestGenerateUploadURL:
    def test_generate_upload_url_with_reconciliation_id(
        self, presigned_service, mock_minio_client, mock_config, mocker
    ):
        mock_client_service, mock_client = mock_minio_client
        mock_client_service.bucket_exists.return_value = True

        mocker.patch("uuid.uuid4", return_value="test-file-id")
        mock_datetime = mocker.patch(
            "app.services.storage.presigned_url_service.datetime"
        )
        mock_datetime.now.return_value = datetime(
            2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        mock_form_data = {
            "AWSAccessKeyId": "test_access_key",
            "policy": "test-policy",
            "signature": "test-signature",
        }
        mock_client.presigned_post_policy.return_value = mock_form_data

        result = presigned_service.generate_upload_url(
            filename="test.csv",
            file_type="source",
            reconciliation_id="rec-123",
            user_id="user-456",
        )

        assert result["upload_url"] == f"{mock_config.minio_url}/reconciliation-files"
        assert result["file_id"] == "test-file-id"
        assert "rec-123" in result["object_name"]
        assert "user-456" in result["object_name"]
        assert result["content_type"] == "text/csv"
        assert result["max_file_size"] == mock_config.UPLOAD_MAX_FILE_SIZE

    def test_generate_upload_url_without_reconciliation_id(
        self, presigned_service, mock_minio_client, mock_config
    ):
        mock_client_service, mock_client = mock_minio_client
        mock_client_service.bucket_exists.return_value = True

        mock_form_data = {"test": "data"}
        mock_client.presigned_post_policy.return_value = mock_form_data

        result = presigned_service.generate_upload_url(
            filename="data.xlsx", file_type="comparison", user_id="user-789"
        )

        assert "shared_files" in result["object_name"]
        assert "user-789" in result["object_name"]
        assert "comparison" in result["object_name"]

    def test_generate_upload_url_file_not_allowed(self, presigned_service, mock_config):
        mock_config.is_file_allowed.return_value = False

        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service.generate_upload_url(
                filename="test.txt", file_type="source", user_id="user-123"
            )
        assert "File type not allowed" in str(exc_info.value)

    def test_generate_upload_url_missing_user_id(self, presigned_service):
        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service.generate_upload_url(
                filename="test.csv", file_type="source"
            )
        assert "user_id is required" in str(exc_info.value)

    def test_generate_upload_url_creates_bucket_if_not_exists(
        self, presigned_service, mock_minio_client, mock_config
    ):
        mock_client_service, mock_client = mock_minio_client
        mock_client_service.bucket_exists.return_value = False
        mock_form_data = {"test": "data"}
        mock_client.presigned_post_policy.return_value = mock_form_data

        presigned_service.generate_upload_url(
            filename="test.csv", file_type="source", user_id="user-123"
        )

        mock_client_service.make_bucket.assert_called_once_with(
            mock_config.MINIO_BUCKET_RECONCILIATION
        )


class TestGenerateDownloadURL:
    def test_generate_download_url_success(
        self, presigned_service, mock_minio_client, mocker
    ):
        mock_client_service, mock_client = mock_minio_client

        mock_stat = mocker.MagicMock()
        mock_stat.size = 1024
        mock_stat.etag = "test-etag"
        mock_stat.content_type = "text/csv"
        mock_stat.last_modified = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_client_service.stat_object.return_value = mock_stat

        mock_client.presigned_get_object.return_value = (
            "http://localhost:9000/download-url"
        )

        result = presigned_service.generate_download_url(
            bucket_name="test-bucket",
            object_name="test-object.csv",
            original_filename="download.csv",
        )

        assert result["download_url"] == "http://localhost:9000/download-url"
        assert result["method"] == "GET"
        assert result["file_metadata"]["size"] == 1024
        assert result["file_metadata"]["etag"] == "test-etag"

    def test_generate_download_url_file_not_found(
        self, presigned_service, mock_minio_client
    ):
        mock_client_service, _ = mock_minio_client
        mock_client_service.stat_object.return_value = None

        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service.generate_download_url(
                bucket_name="test-bucket", object_name="missing.csv"
            )
        assert "File not found" in str(exc_info.value)

    def test_generate_download_url_with_custom_expiry(
        self, presigned_service, mock_minio_client, mocker
    ):
        mock_client_service, mock_client = mock_minio_client

        mock_stat = mocker.MagicMock()
        mock_client_service.stat_object.return_value = mock_stat
        mock_client.presigned_get_object.return_value = (
            "http://localhost:9000/download-url"
        )

        presigned_service.generate_download_url(
            bucket_name="test-bucket", object_name="test.csv", expires_in=7200
        )

        call_args = mock_client.presigned_get_object.call_args
        assert call_args.kwargs["expires"] == timedelta(seconds=7200)


class TestReconciliationResults:
    def test_generate_result_download_url_success(
        self, presigned_service, mock_minio_client, mock_config, mocker
    ):
        mock_client_service, mock_client = mock_minio_client

        mock_stat = mocker.MagicMock()
        mock_client_service.stat_object.return_value = mock_stat
        mock_client.presigned_get_object.return_value = (
            "http://localhost:9000/result-url"
        )

        result = presigned_service.generate_result_download_url(
            reconciliation_id="rec-789",
            user_id="user-456",
            result_type="report",
            filename="report.csv",
        )

        assert result["download_url"] == "http://localhost:9000/result-url"
        expected_object = f"{mock_config.RECONCILIATION_RESULTS_PREFIX}/user-456/rec-789/report/report.csv"
        mock_client_service.stat_object.assert_called_with(
            mock_config.MINIO_BUCKET_REPORTS, expected_object
        )

    def test_generate_result_download_url_missing_filename(self, presigned_service):
        with pytest.raises(MinIOStorageException) as exc_info:
            presigned_service.generate_result_download_url(
                reconciliation_id="rec-123", user_id="user-456", result_type="report"
            )
        assert "filename is required" in str(exc_info.value)

    def test_save_reconciliation_result_success(
        self, presigned_service, mock_minio_client, mock_config, mocker
    ):
        mock_client_service, mock_client = mock_minio_client
        mock_client_service.bucket_exists.return_value = True

        mocker.patch("uuid.uuid4", return_value="result-id")
        mock_datetime = mocker.patch(
            "app.services.storage.presigned_url_service.datetime"
        )
        mock_datetime.now.return_value = datetime(
            2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        content = b"test,data\n1,2\n"
        result = presigned_service.save_reconciliation_result(
            reconciliation_id="rec-123",
            user_id="user-456",
            result_type="report",
            content=content,
            filename="custom_report.csv",
        )

        assert result["success"] is True
        assert result["file_id"] == "result-id"
        assert result["size"] == len(content)
        assert result["reconciliation_id"] == "rec-123"
        assert result["user_id"] == "user-456"
        assert "custom_report.csv" in result["filename"]

        mock_client.put_object.assert_called_once()

    def test_save_reconciliation_result_auto_filename(
        self, presigned_service, mock_minio_client, mock_config, mocker
    ):
        mock_client_service, mock_client = mock_minio_client
        mock_client_service.bucket_exists.return_value = True

        content = b'{"mismatches": []}'
        result = presigned_service.save_reconciliation_result(
            reconciliation_id="rec-789",
            user_id="user-123",
            result_type="mismatches",
            content=content,
        )

        assert result["success"] is True
        assert ".json" in result["filename"]
        assert "mismatches" in result["filename"]


class TestValidateUploadCompletion:
    def test_validate_upload_completion_valid(
        self, presigned_service, mock_minio_client, mocker
    ):
        mock_client_service, _ = mock_minio_client

        mock_stat = mocker.MagicMock()
        mock_stat.size = 5000
        mock_stat.etag = "upload-etag"
        mock_stat.content_type = "text/csv"
        mock_stat.last_modified = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_client_service.stat_object.return_value = mock_stat

        result = presigned_service.validate_upload_completion("uploads", "file.csv")

        assert result["valid"] is True
        assert result["size"] == 5000
        assert result["etag"] == "upload-etag"
        assert result["bucket"] == "uploads"
        assert result["object"] == "file.csv"

    def test_validate_upload_completion_not_found(
        self, presigned_service, mock_minio_client
    ):
        mock_client_service, _ = mock_minio_client
        mock_client_service.stat_object.return_value = None

        result = presigned_service.validate_upload_completion("uploads", "missing.csv")

        assert result["valid"] is False
        assert result["error"] == "File not found"

    def test_validate_upload_completion_error(
        self, presigned_service, mock_minio_client
    ):
        mock_client_service, _ = mock_minio_client
        mock_client_service.stat_object.side_effect = Exception("Validation error")

        result = presigned_service.validate_upload_completion("uploads", "error.csv")

        assert result["valid"] is False
        assert "Validation error" in result["error"]
