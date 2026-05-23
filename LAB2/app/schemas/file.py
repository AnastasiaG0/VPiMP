from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str = Field(..., description="Unique file identifier")
    original_name: str = Field(..., description="Original file name")
    size: int = Field(..., description="File size in bytes")
    mimetype: str = Field(..., description="MIME type of file")
    created_at: datetime = Field(..., description="Upload date")
    
    model_config = ConfigDict(from_attributes=True)


class FileMetadataResponse(BaseModel):
    """Response with file metadata (without sensitive information)"""
    file_id: str = Field(..., description="Unique file identifier")
    original_name: str = Field(..., description="Original file name")
    size: int = Field(..., description="File size in bytes")
    mimetype: str = Field(..., description="MIME type of file")
    created_at: datetime = Field(..., description="Upload date")
    url: Optional[str] = Field(None, description="URL to access the file")
    
    model_config = ConfigDict(from_attributes=True)


class FileListResponse(BaseModel):
    """Response with file list"""
    data: list[FileMetadataResponse] = Field(..., description="List of files")
    meta: dict = Field(..., description="Pagination metadata")


class ProfileUpdateRequest(BaseModel):
    """Request to update profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name")
    bio: Optional[str] = Field(None, max_length=500, description="Short biography")
    avatar_file_id: Optional[str] = Field(None, description="Avatar file ID")


class ProfileResponse(BaseModel):
    """Response with profile data"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="Full name")
    bio: Optional[str] = Field(None, description="Biography")
    avatar_file_id: Optional[str] = Field(None, description="Avatar file ID")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: Optional[str] = Field(None, description="Registration date")
    
    model_config = ConfigDict(from_attributes=True)