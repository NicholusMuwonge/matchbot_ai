import hashlib
import logging
from uuid import UUID

from minio.error import S3Error
from sqlmodel import Session, select

from app.core.celery import celery_app
from app.core.config import settings
from app.core.db import engine
from app.models.file import File, FileStatus
from app.services.cache.file_cache import cache_file_content
from app.services.storage.minio_client import (
    MinIOStorageException,
    minio_client_service,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    time_limit=settings.REDIS_TASK_TIME_LIMIT,
    soft_time_limit=settings.REDIS_TASK_SOFT_TIME_LIMIT,
    autoretry_for=(S3Error, MinIOStorageException, ConnectionError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_uploaded_file(file_id: str):
    """
    Process a file after upload confirmation.
    Retries automatically on MinIO/network errors.

    Args:
        file_id: UUID of the file to process
    """
    with Session(engine) as session:
        file = session.exec(select(File).where(File.id == UUID(file_id))).first()

        if not file:
            logger.error(f"File {file_id} not found in database")
            return

        if file.status != FileStatus.UPLOADED:
            logger.warning(f"File {file_id} is not in UPLOADED status, skipping")
            return

        try:
            file.status = FileStatus.SYNCING
            session.commit()

            file_stream = minio_client_service.get_object(
                bucket_name=settings.MINIO_BUCKET_RECONCILIATION,
                object_name=file.storage_path,
            )

            file_content = file_stream.read()
            content_hash = hashlib.sha256(file_content).hexdigest()

            logger.info(
                f"Processing file {file_id}: {file.filename}, hash: {content_hash}"
            )

            # Cache content in Redis (lazy-loading cache)
            cache_file_content(file.id, file_content, ttl=86400)

            # Store metadata in PostgreSQL (NOT raw content)
            file.status = FileStatus.SYNCED
            file.file_hash = content_hash
            file.content = {
                "size_bytes": len(file_content),
                "cached_at": "redis",
                "hash": content_hash,
            }
            session.commit()

        except (S3Error, MinIOStorageException, ConnectionError) as e:
            logger.warning(f"Retryable error processing file {file_id}: {e}")
            file.status = FileStatus.UPLOADED
            session.commit()
            raise

        except Exception as e:
            logger.error(f"Fatal error processing file {file_id}: {e}")
            file.status = FileStatus.FAILED
            file.failure_reason = str(e)
            session.commit()
