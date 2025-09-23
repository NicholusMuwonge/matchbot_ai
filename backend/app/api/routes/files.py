"""
File management API endpoints for MinIO integration.
"""

from datetime import timedelta

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.services.minio_service import minio_service

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str | None = Query(None, description="Optional path prefix for the file"),
):
    """
    Upload a file to MinIO storage.

    Args:
        file: The file to upload
        path: Optional path prefix for organizing files

    Returns:
        Object containing the file path and presigned download URL
    """
    try:
        # Construct object name with optional path
        object_name = f"{path}/{file.filename}" if path else file.filename

        # Upload file to MinIO
        file_path = minio_service.upload_file(
            file.file,
            object_name,
            content_type=file.content_type or "application/octet-stream",
            metadata={"original_filename": file.filename},
        )

        # Generate download URL
        download_url = minio_service.generate_presigned_download_url(
            file_path, expires_in=timedelta(hours=24)
        )

        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "download_url": download_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Download a file from MinIO storage.

    Args:
        file_path: Path to the file in MinIO

    Returns:
        The file as a streaming response
    """
    try:
        if not minio_service.object_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Get file metadata
        metadata = minio_service.get_object_metadata(file_path)

        # Download file
        file_data = minio_service.download_file(file_path)

        return StreamingResponse(
            file_data,
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename={file_path.split('/')[-1]}"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presigned-upload-url")
async def generate_presigned_upload_url(
    filename: str = Query(..., description="Name of the file to upload"),
    path: str | None = Query(None, description="Optional path prefix"),
    expires_in_hours: int = Query(
        1, ge=1, le=24, description="URL expiration in hours"
    ),
):
    """
    Generate a presigned URL for direct file upload to MinIO.

    Args:
        filename: Name of the file to upload
        path: Optional path prefix for organizing files
        expires_in_hours: How long the URL should be valid (1-24 hours)

    Returns:
        Presigned URL for uploading the file
    """
    try:
        # Construct object name with optional path
        object_name = f"{path}/{filename}" if path else filename

        # Generate presigned URL
        upload_url = minio_service.generate_presigned_upload_url(
            object_name, expires_in=timedelta(hours=expires_in_hours)
        )

        return {
            "upload_url": upload_url,
            "file_path": object_name,
            "expires_in": f"{expires_in_hours} hours",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presigned-download-url")
async def generate_presigned_download_url(
    file_path: str = Query(..., description="Path to the file in MinIO"),
    expires_in_hours: int = Query(
        1, ge=1, le=24, description="URL expiration in hours"
    ),
):
    """
    Generate a presigned URL for direct file download from MinIO.

    Args:
        file_path: Path to the file in MinIO
        expires_in_hours: How long the URL should be valid (1-24 hours)

    Returns:
        Presigned URL for downloading the file
    """
    try:
        if not minio_service.object_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Generate presigned URL
        download_url = minio_service.generate_presigned_download_url(
            file_path, expires_in=timedelta(hours=expires_in_hours)
        )

        return {
            "download_url": download_url,
            "file_path": file_path,
            "expires_in": f"{expires_in_hours} hours",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_path:path}")
async def delete_file(file_path: str):
    """
    Delete a file from MinIO storage.

    Args:
        file_path: Path to the file in MinIO

    Returns:
        Success message
    """
    try:
        if not minio_service.object_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        minio_service.delete_file(file_path)

        return {"message": f"File {file_path} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_files(
    prefix: str | None = Query(None, description="Filter files by prefix"),
):
    """
    List files in MinIO storage.

    Args:
        prefix: Optional prefix to filter files

    Returns:
        List of files with metadata
    """
    try:
        files = minio_service.list_objects(prefix=prefix)
        return {
            "count": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
