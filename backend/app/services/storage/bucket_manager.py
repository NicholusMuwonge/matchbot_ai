import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.storage_config import StorageConfig, storage_config
from app.services.storage.minio_client import MinIOClientService, MinIOStorageException

logger = logging.getLogger(__name__)


class BucketManager:
    """
    Manages MinIO bucket initialization, lifecycle policies, and health checks.
    Ensures all required buckets exist and are properly configured.
    """

    def __init__(
        self,
        minio_client: MinIOClientService | None = None,
        config: StorageConfig | None = None,
    ):
        self.config = config or storage_config
        self.minio_client = minio_client or MinIOClientService(self.config)

    def _create_bucket_if_needed(self, bucket_name: str) -> bool:
        """Create bucket if it doesn't exist."""
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
                return True
            else:
                logger.debug(f"Bucket already exists: {bucket_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            raise MinIOStorageException(f"Bucket creation failed: {e}")

    def initialize_buckets(self) -> bool:
        """
        Create all required buckets if they don't exist.
        Sets up lifecycle policies for automatic cleanup.

        Returns:
            True if all buckets initialized successfully
        """
        try:
            logger.info("Initializing MinIO buckets...")

            if not self.minio_client.verify_connection():
                raise MinIOStorageException("Cannot connect to MinIO server")

            required_buckets = self.config.required_buckets
            success_count = 0

            for bucket_name in required_buckets:
                try:
                    self._create_bucket_if_needed(bucket_name)
                    success_count += 1
                    logger.info(f"✓ Bucket ready: {bucket_name}")
                except Exception as e:
                    logger.error(f"Error initializing bucket {bucket_name}: {e}")

            all_success = success_count == len(required_buckets)

            if all_success:
                logger.info(f"Successfully initialized all {success_count} buckets")
            else:
                logger.warning(
                    f"Initialized {success_count}/{len(required_buckets)} buckets"
                )

            return all_success

        except Exception as e:
            logger.error(f"Failed to initialize buckets: {e}")
            return False

    def verify_buckets_health(self) -> dict[str, Any]:
        """
        Check health status of all required buckets.

        Returns:
            Dictionary with bucket health status
        """
        health_status = {
            "healthy": True,
            "buckets": {},
            "errors": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            if not self.minio_client.verify_connection():
                health_status["healthy"] = False
                health_status["errors"].append("MinIO connection failed")
                return health_status

            for bucket_name in self.config.required_buckets:
                try:
                    exists = self.minio_client.bucket_exists(bucket_name)
                    health_status["buckets"][bucket_name] = {
                        "exists": exists,
                        "accessible": exists,
                    }

                    if not exists:
                        health_status["healthy"] = False
                        health_status["errors"].append(f"Bucket missing: {bucket_name}")

                except Exception as e:
                    logger.error(f"Failed to check bucket {bucket_name}: {e}")
                    health_status["healthy"] = False
                    health_status["buckets"][bucket_name] = {
                        "exists": False,
                        "accessible": False,
                        "error": str(e),
                    }
                    health_status["errors"].append(f"Bucket {bucket_name}: {e}")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["healthy"] = False
            health_status["errors"].append(f"Health check failed: {e}")

        return health_status

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists without creating it."""
        try:
            return self.minio_client.bucket_exists(bucket_name)
        except Exception as e:
            logger.error(f"Failed to check bucket {bucket_name}: {e}")
            return False

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """
        Create a bucket only if it doesn't already exist.

        Returns:
            True if bucket exists (already existed or was created successfully)
        """
        try:
            self._create_bucket_if_needed(bucket_name)
            return True
        except Exception as e:
            logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
            return False

    def delete_bucket_if_exists(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a bucket if it exists.

        Args:
            bucket_name: Name of the bucket to delete
            force: If True, delete even if bucket contains objects

        Returns:
            True if bucket was deleted or didn't exist
        """
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                logger.debug(f"Bucket doesn't exist: {bucket_name}")
                return True

            if force:
                objects = self.minio_client.list_objects(bucket_name, recursive=True)
                for obj in objects:
                    self.minio_client.remove_object(bucket_name, obj.object_name)

            self.minio_client.get_client().remove_bucket(bucket_name)
            logger.info(f"Deleted bucket: {bucket_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False

    def cleanup_expired_files(self) -> dict[str, Any]:
        """
        Manually trigger cleanup of expired files.

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "temp_deleted": 0,
            "unconfirmed_deleted": 0,
            "total_deleted": 0,
            "errors": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            temp_deleted = self._cleanup_bucket(
                self.config.MINIO_BUCKET_TEMP, self.config.TEMP_FILE_TTL_HOURS
            )
            stats["temp_deleted"] = temp_deleted

            unconfirmed_deleted = self._cleanup_bucket(
                self.config.MINIO_BUCKET_RECONCILIATION,
                self.config.UNCONFIRMED_FILE_TTL_HOURS,
                prefix="unconfirmed/",
            )
            stats["unconfirmed_deleted"] = unconfirmed_deleted

            stats["total_deleted"] = temp_deleted + unconfirmed_deleted
            stats["completed_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Cleanup completed: {stats['total_deleted']} files deleted")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            stats["errors"].append(str(e))

        return stats

    def _cleanup_bucket(
        self, bucket_name: str, ttl_hours: int, prefix: str | None = None
    ) -> int:
        """Clean up expired files in a bucket."""
        deleted_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

        try:
            objects = self.minio_client.list_objects(bucket_name, prefix=prefix)

            for obj in objects:
                if obj.last_modified and obj.last_modified < cutoff_time:
                    try:
                        self.minio_client.remove_object(bucket_name, obj.object_name)
                        deleted_count += 1
                        logger.debug(f"Deleted expired file: {obj.object_name}")
                    except Exception as e:
                        logger.error(f"Failed to delete {obj.object_name}: {e}")

        except Exception as e:
            logger.error(f"Error cleaning bucket {bucket_name}: {e}")

        return deleted_count

    def get_bucket_statistics(self, bucket_name: str) -> dict[str, Any]:
        """Get statistics for a specific bucket."""
        stats = {
            "bucket_name": bucket_name,
            "exists": False,
            "file_count": 0,
            "total_size": 0,
            "oldest_file": None,
            "newest_file": None,
        }

        try:
            if not self.minio_client.bucket_exists(bucket_name):
                return stats

            stats["exists"] = True
            objects = self.minio_client.list_objects(bucket_name, recursive=True)

            for obj in objects:
                stats["file_count"] += 1
                stats["total_size"] += obj.size or 0

                if obj.last_modified:
                    if (
                        not stats["oldest_file"]
                        or obj.last_modified < stats["oldest_file"]
                    ):
                        stats["oldest_file"] = obj.last_modified.isoformat()

                    if (
                        not stats["newest_file"]
                        or obj.last_modified > stats["newest_file"]
                    ):
                        stats["newest_file"] = obj.last_modified.isoformat()

        except Exception as e:
            logger.error(f"Failed to get statistics for {bucket_name}: {e}")
            stats["error"] = str(e)

        return stats


bucket_manager = BucketManager()
