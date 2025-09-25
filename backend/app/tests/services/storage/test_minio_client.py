import pytest
from minio.error import S3Error

from app.services.storage.minio_client import MinIOClientService, MinIOStorageException


def create_s3_error(
    code="TestError", message="Test error message", resource="test-resource"
):
    """Helper function for creating S3Error instances with custom parameters."""
    return S3Error(
        code=code,
        message=message,
        resource=resource,
        request_id="test-request-id",
        host_id="test-host-id",
        response="test-response",
    )


@pytest.fixture
def mock_config(mocker):
    config = mocker.MagicMock()
    config.MINIO_ENDPOINT = "localhost:9000"
    config.MINIO_ACCESS_KEY = "test_access_key"
    config.MINIO_SECRET_KEY = "secret_key"
    config.MINIO_SECURE = False
    config.MINIO_REGION = "us-east-1"
    return config


@pytest.fixture
def mock_minio_client(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch("app.services.storage.minio_client.Minio", return_value=mock_client)
    return mock_client


@pytest.fixture
def minio_service(mock_config, mock_minio_client):
    return MinIOClientService(config=mock_config)


def test_get_client_returns_minio_client(minio_service, mock_minio_client):
    client = minio_service.get_client()
    assert client == mock_minio_client


def test_verify_connection_success(minio_service, mock_minio_client):
    mock_minio_client.list_buckets.return_value = []
    result = minio_service.verify_connection()
    assert result is True
    mock_minio_client.list_buckets.assert_called_once()


def test_verify_connection_failure(minio_service, mock_minio_client):
    mock_minio_client.list_buckets.side_effect = create_s3_error(
        code="ConnectionFailed", message="Connection failed", resource="bucket"
    )
    result = minio_service.verify_connection()
    assert result is False


def test_bucket_exists_returns_true(minio_service, mock_minio_client):
    mock_minio_client.bucket_exists.return_value = True
    result = minio_service.bucket_exists("test-bucket")
    assert result is True
    mock_minio_client.bucket_exists.assert_called_once_with("test-bucket")


def test_bucket_exists_returns_false(minio_service, mock_minio_client):
    mock_minio_client.bucket_exists.return_value = False
    result = minio_service.bucket_exists("test-bucket")
    assert result is False


def test_bucket_exists_handles_error(minio_service, mock_minio_client):
    mock_minio_client.bucket_exists.side_effect = create_s3_error(
        code="AccessDenied", message="Access denied", resource="bucket"
    )
    result = minio_service.bucket_exists("test-bucket")
    assert result is False


def test_make_bucket_success(minio_service, mock_minio_client):
    result = minio_service.make_bucket("new-bucket")
    assert result is True
    mock_minio_client.make_bucket.assert_called_once_with(
        "new-bucket", location="us-east-1"
    )


def test_make_bucket_raises_exception(minio_service, mock_minio_client):
    mock_minio_client.make_bucket.side_effect = create_s3_error(
        code="BucketAlreadyExists", message="Bucket already exists", resource="bucket"
    )
    with pytest.raises(MinIOStorageException) as exc_info:
        minio_service.make_bucket("existing-bucket")
    assert "Could not create bucket" in str(exc_info.value)


def test_stat_object_success(minio_service, mock_minio_client, mocker):
    mock_stat = mocker.MagicMock()
    mock_minio_client.stat_object.return_value = mock_stat
    result = minio_service.stat_object("bucket", "object.txt")
    assert result == mock_stat


def test_stat_object_not_found(minio_service, mock_minio_client):
    mock_minio_client.stat_object.side_effect = create_s3_error(
        code="NoSuchKey", message="Object not found", resource="object"
    )
    result = minio_service.stat_object("bucket", "missing.txt")
    assert result is None


def test_remove_object_success(minio_service, mock_minio_client):
    result = minio_service.remove_object("bucket", "file.txt")
    assert result is True
    mock_minio_client.remove_object.assert_called_once_with("bucket", "file.txt")


def test_remove_object_raises_exception(minio_service, mock_minio_client):
    mock_minio_client.remove_object.side_effect = create_s3_error(
        code="AccessDenied", message="Access denied", resource="object"
    )
    with pytest.raises(MinIOStorageException) as exc_info:
        minio_service.remove_object("bucket", "file.txt")
    assert "Could not delete object" in str(exc_info.value)


def test_list_objects_success(minio_service, mock_minio_client, mocker):
    mock_objects = [mocker.MagicMock(), mocker.MagicMock()]
    mock_minio_client.list_objects.return_value = mock_objects
    result = minio_service.list_objects("bucket", prefix="docs/")
    assert result == mock_objects
    mock_minio_client.list_objects.assert_called_once_with(
        "bucket", prefix="docs/", recursive=True
    )


def test_get_object_success(minio_service, mock_minio_client, mocker):
    mock_object = mocker.MagicMock()
    mock_minio_client.get_object.return_value = mock_object
    result = minio_service.get_object("bucket", "file.txt")
    assert result == mock_object
    mock_minio_client.get_object.assert_called_once_with("bucket", "file.txt")
