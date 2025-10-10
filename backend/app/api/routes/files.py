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
    summary="Generate presigned upload URL for file",
    description="Creates a file record and returns a presigned URL for uploading a file directly to object storage. URL expires in 1 hour.",
    responses={
        200: {
            "description": "Presigned upload URL generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "upload_url": "http://192.168.50.198:9000/bucket/path?X-Amz-Algorithm=...",
                        "file_id": "8fe61ae3-b96e-4336-9463-a693424e80aa",
                        "external_id": "ext_123abc",
                        "object_name": "source/user123/file.csv",
                        "expires_at": "2025-10-08T11:30:00Z",
                        "expires_in": 3600,
                    }
                }
            },
        },
        500: {"description": "Failed to generate upload URL or create file record"},
    },
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
    summary="Generate multiple presigned upload URLs",
    description="Creates multiple file records and returns presigned URLs for uploading files directly to object storage. Each URL expires in 1 hour.",
    responses={
        200: {
            "description": "Bulk presigned upload URLs generated successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "upload_url": "http://192.168.50.198:9000/bucket/path1?X-Amz-Algorithm=...",
                            "file_id": "8fe61ae3-b96e-4336-9463-a693424e80aa",
                            "external_id": "ext_123abc",
                            "object_name": "source/user123/file1.csv",
                            "expires_at": "2025-10-08T11:30:00Z",
                            "expires_in": 3600,
                        },
                        {
                            "upload_url": "http://192.168.50.198:9000/bucket/path2?X-Amz-Algorithm=...",
                            "file_id": "7ab52de4-c85a-5447-a574-b804535f91bb",
                            "external_id": "ext_456def",
                            "object_name": "source/user123/file2.csv",
                            "expires_at": "2025-10-08T11:30:00Z",
                            "expires_in": 3600,
                        },
                    ]
                }
            },
        },
        500: {"description": "Failed to generate upload URLs or create file records"},
    },
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
    "/confirm-uploads",
    response_model=dict[str, Any],
    dependencies=[Security(security)],
    summary="Confirm file uploads and trigger processing",
    description="Confirms that files have been uploaded to object storage and triggers background processing tasks. Files must be in PENDING status.",
    responses={
        200: {
            "description": "File uploads confirmed and processing started",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Files confirmed and processing started",
                        "task_ids": ["task_123", "task_456"],
                        "files_confirmed": 2,
                    }
                }
            },
        },
        400: {
            "description": "Files not found, belong to another user, or not in PENDING status"
        },
        500: {"description": "Failed to confirm file uploads"},
    },
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
    summary="Generate presigned download URL for a file",
    description="Returns a temporary presigned URL valid for 2 hours that allows direct download from object storage. The file must be in SYNCED status.",
    responses={
        200: {
            "description": "Presigned URL generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "download_url": "http://192.168.50.198:9000/bucket/path?X-Amz-Algorithm=...",
                        "expires_in": 7200,
                        "file_id": "8fe61ae3-b96e-4336-9463-a693424e80aa",
                        "filename": "transactions.csv",
                    }
                }
            },
        },
        400: {"description": "File not ready for download (not in SYNCED status)"},
        403: {"description": "Access denied - file belongs to another user"},
        404: {"description": "File not found"},
        500: {"description": "Failed to generate download URL"},
    },
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
            status_code=400,
            detail=f"File not ready for download. Status: {file.status}",
        )

    try:
        result = presigned_url_service.generate_download_url(
            bucket_name=storage_config.MINIO_BUCKET_RECONCILIATION,
            object_name=file.storage_path,
            original_filename=file.filename,
            expires_in=storage_config.DOWNLOAD_PRESIGNED_URL_EXPIRY,
        )

        result["file_id"] = str(file.id)
        result["filename"] = file.filename
        return result
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
    summary="Get file status and metadata",
    description="Returns comprehensive status information about an uploaded file including processing status, hash, size, and timestamps.",
    responses={
        200: {
            "description": "File status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "file_id": "8fe61ae3-b96e-4336-9463-a693424e80aa",
                        "external_id": "ext_123abc",
                        "filename": "transactions.csv",
                        "status": "SYNCED",
                        "file_size_bytes": 91299,
                        "file_hash": "a1b2c3d4...",
                        "content_type": "text/csv",
                        "provider": "MINIO",
                        "failure_reason": None,
                        "metadata": {"size_bytes": 91299},
                        "created_at": "2025-10-08T10:30:00Z",
                        "updated_at": "2025-10-08T10:30:15Z",
                    }
                }
            },
        },
        403: {"description": "Access denied - file belongs to another user"},
        404: {"description": "File not found"},
    },
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
