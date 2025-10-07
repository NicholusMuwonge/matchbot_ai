import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from sqlmodel import Session

from app.api.deps import ClerkSessionUser, get_db
from app.core.storage_config import storage_config
from app.models.file import File, FileStatus, StorageProvider
from app.schemas.file import (
    BulkConfirmUploadRequest,
    BulkUploadRequest,
    FileConfirmation,
    FileUploadRequest,
)
from app.services.storage.minio_client import (
    MinIOStorageException,
    minio_client_service,
)
from app.services.storage.presigned_url_service import presigned_url_service

router = APIRouter(prefix="/files", tags=["files"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


def validate_files_for_confirmation(
    session: Session,
    external_ids: list[str],
    user_id: UUID,
) -> dict[str, File]:
    files = session.exec(File.by_external_ids(external_ids, user_id)).all()

    if len(files) != len(external_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more files not found or do not belong to the user",
        )

    file_map = {f.external_id: f for f in files}

    for external_id in external_ids:
        if file_map[external_id].status != FileStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"File {external_id} is {file_map[external_id].status}, expected PENDING",
            )

    return file_map


def update_files_to_uploaded(
    file_map: dict[str, File],
    confirmations: list[FileConfirmation],
) -> None:
    for confirmation in confirmations:
        file_record = file_map[confirmation.external_id]
        file_record.status = FileStatus.UPLOADED
        file_record.file_size_bytes = confirmation.file_size


@router.post(
    "/presigned-upload",
    response_model=dict[str, Any],
    dependencies=[Security(security)],
)
def generate_presigned_upload_url(
    request: FileUploadRequest,
    current_user: ClerkSessionUser,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = presigned_url_service.generate_upload_url(
            filename=request.filename,
            file_type="source",
            user_id=current_user.user_id,
        )

        file_record = File(
            id=UUID(result["file_id"]),
            external_id=request.external_id,
            user_id=UUID(current_user.user_id),
            filename=request.filename,
            storage_path=result["object_name"],
            content_type=result["content_type"],
            file_size_bytes=0,
            status=FileStatus.PENDING,
            provider=StorageProvider.MINIO,
            expires_at=result["expires_at"],
        )
        session.add(file_record)
        session.commit()

        return result
    except MinIOStorageException as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating upload URL: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")


@router.post(
    "/presigned-uploads",
    response_model=list[dict[str, Any]],
    dependencies=[Security(security)],
)
def generate_bulk_presigned_upload_urls(
    request: BulkUploadRequest,
    current_user: ClerkSessionUser,
    session: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    try:
        files_data = [
            {"filename": f.filename, "file_type": "source"} for f in request.files
        ]
        results = presigned_url_service.generate_bulk_upload_urls(
            files=files_data,
            user_id=current_user.user_id,
        )

        with session.begin_nested():
            file_records = []
            for i, result in enumerate(results):
                file_record = File(
                    id=UUID(result["file_id"]),
                    external_id=request.files[i].external_id,
                    user_id=UUID(current_user.user_id),
                    filename=request.files[i].filename,
                    storage_path=result["object_name"],
                    content_type=result["content_type"],
                    file_size_bytes=0,
                    status=FileStatus.PENDING,
                    provider=StorageProvider.MINIO,
                    expires_at=result["expires_at"],
                )
                file_records.append(file_record)

            session.add_all(file_records)
            session.commit()

        return results
    except MinIOStorageException as e:
        logger.error(f"Failed to generate bulk upload URLs: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating bulk upload URLs: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to generate upload URLs")


@router.post(
    "/confirm-uploads", response_model=dict[str, Any], dependencies=[Security(security)]
)
def confirm_uploads(
    request: BulkConfirmUploadRequest,
    current_user: ClerkSessionUser,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    external_ids = [f.external_id for f in request.files]

    file_map = validate_files_for_confirmation(
        session, external_ids, UUID(current_user.user_id)
    )

    try:
        with session.begin_nested():
            update_files_to_uploaded(file_map, request.files)
            session.commit()

        return {
            "confirmed": len(file_map),
            "message": f"Successfully confirmed {len(file_map)} file upload(s)",
        }
    except Exception as e:
        logger.error(f"Transaction failed confirming file uploads: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to confirm file uploads")

@router.get(
    "/{file_id}/download-url",
    response_model=dict[str, Any],
    dependencies=[Security(security)],
)
def generate_file_download_url(
    file_id: UUID,
    current_user: ClerkSessionUser,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    file = session.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.user_id != UUID(current_user.user_id):
        raise HTTPException(status_code=403, detail="Access denied to this file")

    if file.status != FileStatus.SYNCED:
        raise HTTPException(
            status_code=400, detail=f"File not ready for download. Status: {file.status}"
        )

    try:
        download_url = minio_client_service.generate_presigned_get_url(
            bucket_name=storage_config.MINIO_BUCKET_RECONCILIATION,
            object_name=file.storage_path,
            expires_seconds=storage_config.DOWNLOAD_PRESIGNED_URL_EXPIRY,
            response_headers={
                "response-content-disposition": f'attachment; filename="{file.filename}"'
            },
        )

        return {
            "download_url": download_url,
            "file_id": str(file.id),
            "filename": file.filename,
            "expires_in": storage_config.DOWNLOAD_PRESIGNED_URL_EXPIRY,
        }
    except MinIOStorageException as e:
        logger.error(f"Failed to generate download URL for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download URL")
    except Exception as e:
        logger.error(f"Unexpected error generating download URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download URL")


@router.get(
    "/{file_id}/status",
    response_model=dict[str, Any],
    dependencies=[Security(security)],
)
def get_file_status(
    file_id: UUID,
    current_user: ClerkSessionUser,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    file = session.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.user_id != UUID(current_user.user_id):
        raise HTTPException(status_code=403, detail="Access denied to this file")

    return {
        "file_id": str(file.id),
        "external_id": file.external_id,
        "filename": file.filename,
        "status": file.status,
        "file_size_bytes": file.file_size_bytes,
        "file_hash": file.file_hash,
        "content_type": file.content_type,
        "provider": file.provider,
        "failure_reason": file.failure_reason,
        "metadata": file.file_metadata,
        "created_at": file.created_at,
        "updated_at": file.updated_at,
    }