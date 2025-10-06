import logging
from uuid import UUID

from sqlmodel import Session, select

from app.core.celery import celery_app
from app.core.config import settings
from app.core.db import engine
from app.models.file import File, FileStatus
from app.services.storage.minio_client import minio_client_service

logger = logging.getLogger(__name__)


@celery_app.task(
    time_limit=settings.REDIS_TASK_TIME_LIMIT,
    soft_time_limit=settings.REDIS_TASK_SOFT_TIME_LIMIT,
)
def process_uploaded_file(file_id: str):
    """
    Process a file after upload confirmation.

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
                object_name=file.storage_path
            )

            logger.info(f"Processing file {file_id}: {file.filename}")

            file.status = FileStatus.SYNCED
            session.commit()

        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")
            file.status = FileStatus.FAILED
            file.failure_reason = str(e)
            session.commit()
