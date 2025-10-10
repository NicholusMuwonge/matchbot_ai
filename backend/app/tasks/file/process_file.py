import hashlib
import logging
from uuid import UUID

from minio.error import S3Error
from sqlmodel import Session, select

from app.core.celery import celery_app
from app.core.config import settings
from app.core.db import engine
from app.core.storage_config import storage_config
from app.models.file import File, FileStatus
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
                bucket_name=storage_config.MINIO_BUCKET_RECONCILIATION,
                object_name=file.storage_path,
            )

            file_content = file_stream.read()
            content_hash = hashlib.sha256(file_content).hexdigest()

            logger.info(
                f"Processing file {file_id}: {file.filename}, hash: {content_hash}"
            )

            duplicate = File.is_a_duplicate(session, file_hash=content_hash, file=file)

            if duplicate:
                logger.info(
                    f"File {file_id} is duplicate of {duplicate.id} "
                    f"(hash: {content_hash}). Deduplicating."
                )
                _delete_file_from_storage(file)
                _reassign_to_existing_file(
                    file=file,
                    duplicate=duplicate,
                    content_hash=content_hash,
                    file_content=file_content,
                    file_id=file_id,
                    session=session,
                )
                return

            file.status = FileStatus.SYNCED
            file.file_hash = content_hash
            file.file_metadata = {
                "size_bytes": len(file_content),
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


def _delete_file_from_storage(file: File) -> None:
    """Delete duplicate file from MinIO storage"""
    try:
        minio_client_service.delete_object(
            bucket_name=storage_config.MINIO_BUCKET_RECONCILIATION,
            object_name=file.storage_path,
        )
        logger.info(f"Deleted duplicate file from MinIO: {file.storage_path}")
    except Exception as e:
        logger.warning(
            f"Failed to delete duplicate file from MinIO: {e}. "
            f"Cleanup job will handle it."
        )


def _reassign_to_existing_file(
    file: File,
    duplicate: File,
    content_hash: str,
    file_content: bytes,
    file_id: str,
    session: Session,
) -> None:
    """Reassign file record to use existing file's storage path"""
    file.storage_path = duplicate.storage_path
    file.file_hash = content_hash
    file.status = FileStatus.SYNCED
    file.file_metadata = {
        "size_bytes": len(file_content),
        "deduplicated": True,
        "original_file_id": str(duplicate.id),
        "original_filename": duplicate.filename,
        "note": f"Identical content to {duplicate.filename}",
    }
    session.commit()

    logger.info(
        f"File {file_id} deduplicated successfully, reusing storage from {duplicate.id}"
    )
