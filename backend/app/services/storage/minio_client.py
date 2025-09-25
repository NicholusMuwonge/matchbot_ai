import logging

from minio import Minio
from minio.error import S3Error

from app.core.storage_config import StorageConfig, storage_config

logger = logging.getLogger(__name__)


class MinIOStorageException(Exception):
    pass


class MinIOClientService:
    """
    Low-level MinIO client wrapper providing basic storage operations.
    This class only provides core MinIO functionality without business logic.
    Use PresignedURLService for URL generation and BucketManager for bucket operations.
    """

    def __init__(self, config: StorageConfig | None = None):
        self.config = config or storage_config
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            self._client = Minio(
                endpoint=self.config.MINIO_ENDPOINT,
                access_key=self.config.MINIO_ACCESS_KEY,
                secret_key=self.config.MINIO_SECRET_KEY,
                secure=self.config.MINIO_SECURE,
                region=self.config.MINIO_REGION,
            )
            logger.info(
                f"MinIO client initialized for endpoint: {self.config.MINIO_ENDPOINT}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise MinIOStorageException(f"Could not connect to MinIO: {e}")

    def get_client(self) -> Minio:
        if not self._client:
            self._initialize_client()
        return self._client

    def verify_connection(self) -> bool:
        try:
            self._client.list_buckets()
            return True
        except S3Error as e:
            logger.error(f"MinIO connection failed: {e}")
            return False

    def bucket_exists(self, bucket_name: str) -> bool:
        try:
            return self._client.bucket_exists(bucket_name)
        except S3Error as e:
            logger.error(f"Error checking bucket {bucket_name}: {e}")
            return False

    def make_bucket(self, bucket_name: str, location: str | None = None) -> bool:
        try:
            self._client.make_bucket(
                bucket_name, location=location or self.config.MINIO_REGION
            )
            logger.info(f"Created bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            raise MinIOStorageException(f"Could not create bucket: {e}")

    def stat_object(self, bucket_name: str, object_name: str):
        try:
            return self._client.stat_object(bucket_name, object_name)
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"Error getting object stats: {e}")
            raise MinIOStorageException(f"Could not stat object: {e}")

    def remove_object(self, bucket_name: str, object_name: str) -> bool:
        try:
            self._client.remove_object(bucket_name, object_name)
            return True
        except S3Error as e:
            logger.error(f"Failed to delete object: {e}")
            raise MinIOStorageException(f"Could not delete object: {e}")

    def list_objects(
        self, bucket_name: str, prefix: str | None = None, recursive: bool = True
    ):
        try:
            return self._client.list_objects(
                bucket_name, prefix=prefix, recursive=recursive
            )
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}")
            raise MinIOStorageException(f"Could not list objects: {e}")

    def get_object(self, bucket_name: str, object_name: str):
        try:
            return self._client.get_object(bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Failed to get object: {e}")
            raise MinIOStorageException(f"Could not get object: {e}")

    def list_buckets(self):
        try:
            return self._client.list_buckets()
        except S3Error as e:
            logger.error(f"Failed to list buckets: {e}")
            raise MinIOStorageException(f"Could not list buckets: {e}")

    def close(self) -> None:
        if self._client:
            self._client = None
            logger.info("MinIO client connection closed")


minio_client_service = MinIOClientService()
