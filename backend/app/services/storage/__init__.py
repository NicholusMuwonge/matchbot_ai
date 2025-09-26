"""
MinIO storage services for file upload/download operations.

This module provides services for:
- Generating presigned URLs for secure uploads and downloads
- Managing bucket lifecycle and initialization
- Streaming large files for processing
- File metadata and validation

Usage:
    from app.services.storage import (
        minio_client_service,
        presigned_url_service,
        bucket_manager
    )

    # Generate upload URL
    upload_info = presigned_url_service.generate_upload_url(
        filename="data.csv",
        file_type="source",
        reconciliation_id="123"
    )

    # Initialize buckets on startup
    bucket_manager.initialize_buckets()
"""

from app.services.storage.bucket_manager import BucketManager, bucket_manager
from app.services.storage.minio_client import (
    MinIOClientService,
    MinIOStorageException,
    minio_client_service,
)
from app.services.storage.presigned_url_service import (
    PresignedURLService,
    presigned_url_service,
)

__all__ = [
    # Services
    "MinIOClientService",
    "PresignedURLService",
    "BucketManager",
    # Singleton instances
    "minio_client_service",
    "presigned_url_service",
    "bucket_manager",
    # Exceptions
    "MinIOStorageException",
]
