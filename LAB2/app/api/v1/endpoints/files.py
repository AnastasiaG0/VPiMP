from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from fastapi.responses import StreamingResponse
from typing import Optional

from app.core.database import get_db
from app.services.file_service import FileService
from app.schemas.file import FileUploadResponse, FileMetadataResponse, FileListResponse
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
    description="Uploads a file to MinIO object storage."
)
async def upload_file(
    file: UploadFile = File(...),
    is_avatar: bool = False,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload file to storage."""
    service = FileService(db, current_user.id)
    metadata = await service.upload_file(file, is_avatar=is_avatar)
    
    return FileUploadResponse(
        file_id=metadata.file_id,
        original_name=metadata.original_name,
        size=metadata.size,
        mimetype=metadata.mimetype,
        created_at=metadata.created_at
    )


@router.get(
    "/{file_id}",
    summary="Download file",
    description="Downloads a file by its ID."
)
async def download_file(
    file_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download file from storage with permission check."""
    service = FileService(db, current_user.id)
    stream, metadata = await service.get_file_stream(file_id)
    
    headers = {
        "Content-Disposition": f"attachment; filename=\"{metadata.original_name}\"",
        "Content-Type": metadata.mimetype,
        "Content-Length": str(metadata.size)
    }
    
    return StreamingResponse(
        stream,
        headers=headers,
        media_type=metadata.mimetype
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Deletes a file from storage (Soft Delete + remove from MinIO)."
)
async def delete_file(
    file_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete file from storage."""
    service = FileService(db, current_user.id)
    await service.delete_file(file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/",
    response_model=FileListResponse,
    summary="Get file list",
    description="Returns a list of all user files with pagination."
)
async def list_files(
    skip: int = 0,
    limit: int = 10,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of user files."""
    service = FileService(db, current_user.id)
    files = await service.get_user_files(skip=skip, limit=limit)
    
    return FileListResponse(
        data=[
            FileMetadataResponse(
                file_id=f.file_id,
                original_name=f.original_name,
                size=f.size,
                mimetype=f.mimetype,
                created_at=f.created_at,
                url=f"/files/{f.file_id}"
            )
            for f in files
        ],
        meta={
            "total": len(files),
            "skip": skip,
            "limit": limit
        }
    )