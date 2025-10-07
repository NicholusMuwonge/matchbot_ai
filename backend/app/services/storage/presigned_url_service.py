import logging
import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from minio.datatypes import PostPolicy

from app.core.storage_config import StorageConfig, storage_config
from app.services.storage.minio_client import MinIOClientService, MinIOStorageException

logger = logging.getLogger(__name__)


class PresignedURLService:
    """
    High-level service for generating presigned URLs and managing file operations.
    Handles business logic for file uploads, downloads, and validation.
    """

    def __init__(
        self,
        minio_client: MinIOClientService | None = None,
        config: StorageConfig | None = None,
    ):
        self.config = config or storage_config
        self.minio_client = minio_client or MinIOClientService(self.config)

        if (
            self.config.MINIO_EXTERNAL_ENDPOINT
            and self.config.MINIO_EXTERNAL_ENDPOINT != self.config.MINIO_ENDPOINT
        ):
            from app.core.storage_config import StorageConfig

            external_config = StorageConfig(
                MINIO_ENDPOINT=self.config.MINIO_EXTERNAL_ENDPOINT,
                MINIO_ACCESS_KEY=self.config.MINIO_ACCESS_KEY,
                MINIO_SECRET_KEY=self.config.MINIO_SECRET_KEY,
                MINIO_SECURE=self.config.MINIO_SECURE,
                MINIO_REGION=self.config.MINIO_REGION,
            )
            self.minio_external_client = MinIOClientService(external_config)
        else:
            self.minio_external_client = self.minio_client

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
            raise MinIOStorageException(f"Bucket operation failed: {e}")

    def generate_upload_url(
        self,
        filename: str,
        file_type: str = "source",
        reconciliation_id: str | None = None,
        user_id: str | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate presigned POST URL for file upload with validation.

        Files can be uploaded without a reconciliation_id to be reused across multiple reconciliations.
        They will be stored in a user-specific area and can be linked to reconciliations later.

        Args:
            filename: Original filename (for validation and extension)
            file_type: Type of file ('source' or 'comparison')
            reconciliation_id: Optional ID to link file to specific reconciliation
            user_id: User ID for tracking (required if reconciliation_id not provided)
            expires_in: Optional expiry time in seconds

        Returns:
            Dictionary with upload URL, form fields, and instructions
        """
        try:
            if not self.config.is_file_allowed(filename):
                allowed = ", ".join(self.config.UPLOAD_ALLOWED_EXTENSIONS)
                raise MinIOStorageException(
                    f"File type not allowed. Allowed extensions: {allowed}"
                )

            file_ext = Path(filename).suffix.lower()
            content_type = self.config.get_content_type(filename)

            file_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            if not user_id:
                raise MinIOStorageException("user_id is required for file upload")

            prefix = self.config.RECONCILIATION_FILES_PREFIX
            if reconciliation_id:
                bucket_name = self.config.MINIO_BUCKET_RECONCILIATION
                object_name = f"{prefix}/{user_id}/{reconciliation_id}/{file_type}/{timestamp}_{file_id}{file_ext}"
            else:
                bucket_name = self.config.MINIO_BUCKET_RECONCILIATION
                object_name = f"{prefix}/{user_id}/shared_files/{file_type}/{timestamp}_{file_id}{file_ext}"

            self._ensure_bucket_exists(bucket_name)

            expires = expires_in or self.config.UPLOAD_PRESIGNED_URL_EXPIRY
            expiration = datetime.now(timezone.utc) + timedelta(seconds=expires)

            policy = PostPolicy(bucket_name, expiration)
            policy.add_equals_condition("key", object_name)
            policy.add_content_length_range_condition(
                1, self.config.UPLOAD_MAX_FILE_SIZE
            )
            if content_type:
                policy.add_equals_condition("Content-Type", content_type)

            client = self.minio_client.get_client()
            form_data = client.presigned_post_policy(policy)

            if content_type:
                form_data["Content-Type"] = content_type

            result = {
                "upload_url": f"{self.config.minio_external_url}/{bucket_name}",
                "form_fields": form_data,
                "file_id": file_id,
                "object_name": object_name,
                "bucket_name": bucket_name,
                "original_filename": filename,
                "content_type": content_type,
                "expires_at": expiration.isoformat(),
                "max_file_size": self.config.UPLOAD_MAX_FILE_SIZE,
                "allowed_extensions": self.config.UPLOAD_ALLOWED_EXTENSIONS,
                "instructions": {
                    "method": "POST",
                    "enctype": "multipart/form-data",
                    "field_order": ["key"]
                    + [k for k in form_data.keys() if k != "key"]
                    + ["file"],
                    "note": "File field must be last in form submission",
                },
            }

            result["form_fields"]["key"] = object_name

            logger.info(
                f"Generated upload URL - file: {filename}, type: {file_type}, "
                f"reconciliation: {reconciliation_id}, object: {object_name}"
            )

            return result

        except MinIOStorageException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise MinIOStorageException(f"Could not generate upload URL: {e}")

    def generate_download_url(
        self,
        bucket_name: str,
        object_name: str,
        original_filename: str | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate presigned URL for file download.

        Args:
            bucket_name: Source bucket
            object_name: Full object path in bucket
            original_filename: Optional filename for Content-Disposition
            expires_in: Optional expiry time in seconds

        Returns:
            Dictionary with download URL and metadata
        """
        try:
            if not self.verify_file_exists(bucket_name, object_name):
                raise MinIOStorageException(
                    f"File not found: {bucket_name}/{object_name}"
                )

            stat = self.minio_client.stat_object(bucket_name, object_name)
            expires = expires_in or self.config.DOWNLOAD_PRESIGNED_URL_EXPIRY
            expiration = datetime.now(timezone.utc) + timedelta(seconds=expires)

            response_headers = {}
            if original_filename:
                response_headers["response-content-disposition"] = (
                    f'attachment; filename="{original_filename}"'
                )

            client = self.minio_external_client.get_client()
            url = client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires),
                response_headers=response_headers if response_headers else None,
            )

            result = {
                "download_url": url,
                "expires_at": expiration.isoformat(),
                "method": "GET",
                "file_metadata": {
                    "size": stat.size,
                    "etag": stat.etag,
                    "content_type": stat.content_type,
                    "last_modified": stat.last_modified.isoformat()
                    if stat.last_modified
                    else None,
                },
            }

            logger.info(f"Generated download URL for: {bucket_name}/{object_name}")
            return result

        except MinIOStorageException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise MinIOStorageException(f"Could not generate download URL: {e}")

    def verify_file_exists(self, bucket_name: str, object_name: str) -> bool:
        try:
            stat = self.minio_client.stat_object(bucket_name, object_name)
            return stat is not None
        except Exception as e:
            logger.error(
                f"Error verifying file existence: {bucket_name}/{object_name}: {e}"
            )
            return False

    def get_file_metadata(self, bucket_name: str, object_name: str) -> dict[str, Any]:
        try:
            if not self.verify_file_exists(bucket_name, object_name):
                raise MinIOStorageException(
                    f"File not found: {bucket_name}/{object_name}"
                )

            stat = self.minio_client.stat_object(bucket_name, object_name)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat()
                if stat.last_modified
                else None,
                "metadata": stat.metadata,
            }
        except Exception as e:
            logger.error(
                f"Failed to get file metadata: {bucket_name}/{object_name}: {e}"
            )
            raise MinIOStorageException(f"Could not retrieve metadata: {e}")

    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        try:
            return self.minio_client.remove_object(bucket_name, object_name)
        except Exception as e:
            logger.error(f"Failed to delete file: {bucket_name}/{object_name}: {e}")
            raise MinIOStorageException(f"Could not delete file: {e}")

    def list_files(
        self, bucket_name: str, prefix: str | None = None, recursive: bool = True
    ) -> list[dict[str, Any]]:
        try:
            objects = self.minio_client.list_objects(bucket_name, prefix, recursive)

            files = []
            for obj in objects:
                files.append(
                    {
                        "key": obj.object_name,
                        "size": obj.size,
                        "etag": obj.etag,
                        "last_modified": obj.last_modified.isoformat()
                        if obj.last_modified
                        else None,
                    }
                )

            return files
        except Exception as e:
            logger.error(f"Failed to list files in {bucket_name}: {e}")
            raise MinIOStorageException(f"Could not list files: {e}")

    def stream_file_content(
        self, bucket_name: str, object_name: str, chunk_size: int = 8192
    ) -> Generator[bytes, None, None]:
        """
        Stream file content in chunks to avoid loading large files into memory.

        Args:
            bucket_name: Source bucket
            object_name: Object path
            chunk_size: Size of chunks to yield (default 8KB)

        Yields:
            Chunks of file content
        """
        try:
            response = self.minio_client.get_object(bucket_name, object_name)
            try:
                yield from iter(lambda: response.read(chunk_size), b"")
            finally:
                response.close()
                response.release_conn()
        except Exception as e:
            logger.error(f"Failed to stream file: {bucket_name}/{object_name}: {e}")
            raise MinIOStorageException(f"Could not stream file: {e}")

    def generate_result_download_url(
        self,
        reconciliation_id: str,
        user_id: str,
        result_type: str = "report",
        filename: str | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate presigned URL for downloading reconciliation results.
        This is a convenience wrapper around generate_download_url for result files.

        Args:
            reconciliation_id: ID of the reconciliation
            user_id: User ID for tracking
            result_type: Type of result ('report', 'mismatches', 'summary')
            filename: Optional specific filename for the result
            expires_in: Optional expiry time in seconds

        Returns:
            Dictionary with download URL and metadata
        """
        try:
            results_prefix = self.config.RECONCILIATION_RESULTS_PREFIX
            if filename:
                object_name = f"{results_prefix}/{user_id}/{reconciliation_id}/{result_type}/{filename}"
            else:
                raise MinIOStorageException(
                    "filename is required for downloading results. "
                    "Use list_files to find available result files first."
                )

            bucket_name = self.config.MINIO_BUCKET_REPORTS

            return self.generate_download_url(
                bucket_name=bucket_name,
                object_name=object_name,
                original_filename=filename,
                expires_in=expires_in,
            )

        except MinIOStorageException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate result download URL: {e}")
            raise MinIOStorageException(f"Could not generate result download URL: {e}")

    def save_reconciliation_result(
        self,
        reconciliation_id: str,
        user_id: str,
        result_type: str,
        content: bytes,
        filename: str | None = None,
    ) -> dict[str, Any]:
        """
        Save reconciliation result directly to storage.

        Args:
            reconciliation_id: ID of the reconciliation
            user_id: User ID for tracking
            result_type: Type of result ('report', 'mismatches', 'summary')
            content: The result content as bytes
            filename: Optional specific filename

        Returns:
            Dictionary with file metadata including object_name for later retrieval
        """
        try:
            file_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            if filename:
                file_ext = Path(filename).suffix.lower()
                base_filename = Path(filename).stem
            else:
                file_ext = (
                    ".json" if result_type in ["mismatches", "summary"] else ".csv"
                )
                base_filename = result_type

            full_filename = f"{timestamp}_{file_id}_{base_filename}{file_ext}"

            results_prefix = self.config.RECONCILIATION_RESULTS_PREFIX
            bucket_name = self.config.MINIO_BUCKET_REPORTS
            object_name = f"{results_prefix}/{user_id}/{reconciliation_id}/{result_type}/{full_filename}"

            self._ensure_bucket_exists(bucket_name)

            import io

            content_stream = io.BytesIO(content)
            content_length = len(content)

            client = self.minio_client.get_client()
            client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=content_stream,
                length=content_length,
                content_type=self.config.get_content_type(full_filename)
                or "application/octet-stream",
            )

            return {
                "success": True,
                "bucket_name": bucket_name,
                "object_name": object_name,
                "filename": full_filename,
                "file_id": file_id,
                "size": content_length,
                "timestamp": timestamp,
                "result_type": result_type,
                "user_id": user_id,
                "reconciliation_id": reconciliation_id,
            }

        except Exception as e:
            logger.error(f"Failed to save reconciliation result: {e}")
            raise MinIOStorageException(f"Could not save result: {e}")

    def validate_upload_completion(
        self, bucket_name: str, object_name: str
    ) -> dict[str, Any]:
        """
        Validate that a file upload completed successfully by checking if it exists.

        This is typically called after a frontend uploads directly to MinIO using a presigned URL
        to confirm the upload succeeded before creating database records.

        Args:
            bucket_name: The bucket where file was uploaded
            object_name: The object path/key of the uploaded file

        Returns:
            Dictionary with validation results and file metadata
        """
        try:
            stat = self.minio_client.stat_object(bucket_name, object_name)

            if not stat:
                return {
                    "valid": False,
                    "error": "File not found",
                    "bucket": bucket_name,
                    "object": object_name,
                }

            return {
                "valid": True,
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat()
                if stat.last_modified
                else None,
                "bucket": bucket_name,
                "object": object_name,
            }

        except Exception as e:
            logger.error(f"Failed to validate upload: {bucket_name}/{object_name}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "bucket": bucket_name,
                "object": object_name,
            }

    def generate_bulk_upload_urls(
        self,
        files: list[dict[str, Any]],
        user_id: str,
        reconciliation_id: str | None = None,
        expires_in: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate presigned upload URLs for multiple files in bulk.

        All files must pass validation or the entire request fails (atomic operation).

        Args:
            files: List of dictionaries with 'filename' and optional 'file_type'
            user_id: User ID for tracking
            reconciliation_id: Optional reconciliation ID to link files
            expires_in: Optional expiry time in seconds

        Returns:
            List of dictionaries with upload URL details for each file

        Raises:
            MinIOStorageException: If any file fails validation or URL generation
        """
        results = []

        for file_info in files:
            filename = file_info.get("filename")
            file_type = file_info.get("file_type", "source")

            if not filename:
                error_msg = f"Filename missing in bulk upload request: {file_info}"
                logger.error(error_msg)
                raise MinIOStorageException(error_msg)

            url_data = self.generate_upload_url(
                filename=filename,
                file_type=file_type,
                reconciliation_id=reconciliation_id,
                user_id=user_id,
                expires_in=expires_in,
            )
            results.append(url_data)

        return results


presigned_url_service = PresignedURLService()
