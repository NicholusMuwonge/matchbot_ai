"""
MinIO service for S3-compatible object storage operations.
Handles file uploads, downloads, and presigned URL generation.
"""

import logging
from datetime import timedelta
from io import BytesIO
from typing import BinaryIO

from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import MinioException

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOService:
    """Service class for MinIO operations."""

    def __init__(self):
        """Initialize MinIO client with configuration from settings."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL,
            region=settings.MINIO_REGION,
        )
        self.default_bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the default bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(self.default_bucket):
                self.client.make_bucket(
                    self.default_bucket, location=settings.MINIO_REGION
                )
                logger.info(f"Created bucket: {self.default_bucket}")
            else:
                logger.debug(f"Bucket already exists: {self.default_bucket}")
        except MinioException as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise

    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        metadata: dict | None = None,
        bucket_name: str | None = None,
    ) -> str:
        """
        Upload a file to MinIO.

        Args:
            file_data: File data as binary stream
            object_name: Name of the object in the bucket
            content_type: MIME type of the file
            metadata: Additional metadata for the object
            bucket_name: Target bucket (uses default if not specified)

        Returns:
            The object name/path in the bucket
        """
        bucket = bucket_name or self.default_bucket

        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning

            self.client.put_object(
                bucket,
                object_name,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata or {},
            )
            logger.info(f"Uploaded {object_name} to {bucket}")
            return object_name
        except MinioException as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def download_file(
        self, object_name: str, bucket_name: str | None = None
    ) -> BytesIO:
        """
        Download a file from MinIO.

        Args:
            object_name: Name of the object to download
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            File data as BytesIO stream
        """
        bucket = bucket_name or self.default_bucket

        try:
            response = self.client.get_object(bucket, object_name)
            data = BytesIO(response.read())
            response.close()
            response.release_conn()
            logger.info(f"Downloaded {object_name} from {bucket}")
            return data
        except MinioException as e:
            logger.error(f"Failed to download file: {e}")
            raise

    def generate_presigned_upload_url(
        self,
        object_name: str,
        expires_in: timedelta = timedelta(hours=1),
        bucket_name: str | None = None,
    ) -> str:
        """
        Generate a presigned URL for file upload.

        Args:
            object_name: Name of the object to upload
            expires_in: URL expiration time
            bucket_name: Target bucket (uses default if not specified)

        Returns:
            Presigned URL for upload
        """
        bucket = bucket_name or self.default_bucket

        try:
            url = self.client.presigned_put_object(
                bucket, object_name, expires=expires_in
            )
            logger.info(f"Generated presigned upload URL for {object_name}")
            return url
        except MinioException as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise

    def generate_presigned_download_url(
        self,
        object_name: str,
        expires_in: timedelta = timedelta(hours=1),
        bucket_name: str | None = None,
    ) -> str:
        """
        Generate a presigned URL for file download.

        Args:
            object_name: Name of the object to download
            expires_in: URL expiration time
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            Presigned URL for download
        """
        bucket = bucket_name or self.default_bucket

        try:
            url = self.client.presigned_get_object(
                bucket, object_name, expires=expires_in
            )
            logger.info(f"Generated presigned download URL for {object_name}")
            return url
        except MinioException as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise

    def delete_file(self, object_name: str, bucket_name: str | None = None) -> bool:
        """
        Delete a file from MinIO.

        Args:
            object_name: Name of the object to delete
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            True if successful
        """
        bucket = bucket_name or self.default_bucket

        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted {object_name} from {bucket}")
            return True
        except MinioException as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    def delete_files(
        self, object_names: list[str], bucket_name: str | None = None
    ) -> bool:
        """
        Delete multiple files from MinIO.

        Args:
            object_names: List of object names to delete
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            True if successful
        """
        bucket = bucket_name or self.default_bucket

        try:
            delete_objects = [DeleteObject(name) for name in object_names]
            errors = self.client.remove_objects(bucket, delete_objects)

            for error in errors:
                logger.error(f"Failed to delete {error.object_name}: {error.error}")

            logger.info(f"Bulk deleted {len(object_names)} objects from {bucket}")
            return True
        except MinioException as e:
            logger.error(f"Failed to delete files: {e}")
            raise

    def list_objects(
        self, prefix: str | None = None, bucket_name: str | None = None
    ) -> list[dict]:
        """
        List objects in a bucket.

        Args:
            prefix: Filter objects by prefix
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            List of object metadata
        """
        bucket = bucket_name or self.default_bucket

        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            result = []
            for obj in objects:
                result.append(
                    {
                        "name": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                    }
                )
            logger.info(f"Listed {len(result)} objects from {bucket}")
            return result
        except MinioException as e:
            logger.error(f"Failed to list objects: {e}")
            raise

    def object_exists(self, object_name: str, bucket_name: str | None = None) -> bool:
        """
        Check if an object exists in the bucket.

        Args:
            object_name: Name of the object to check
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            True if object exists
        """
        bucket = bucket_name or self.default_bucket

        try:
            self.client.stat_object(bucket, object_name)
            return True
        except MinioException:
            return False

    def get_object_metadata(
        self, object_name: str, bucket_name: str | None = None
    ) -> dict:
        """
        Get metadata for an object.

        Args:
            object_name: Name of the object
            bucket_name: Source bucket (uses default if not specified)

        Returns:
            Object metadata
        """
        bucket = bucket_name or self.default_bucket

        try:
            stat = self.client.stat_object(bucket, object_name)
            return {
                "name": stat.object_name,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
            }
        except MinioException as e:
            logger.error(f"Failed to get object metadata: {e}")
            raise


# Global instance for dependency injection
minio_service = MinIOService()
