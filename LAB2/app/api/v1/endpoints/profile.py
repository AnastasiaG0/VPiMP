from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.database import get_db
from app.services.profile_service import ProfileService
from app.schemas.file import ProfileUpdateRequest, ProfileResponse
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get(
    "/",
    response_model=ProfileResponse,
    summary="Get profile",
    description="Returns the current user's profile information."
)
async def get_profile(
    db = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    """
    service = ProfileService(db, current_user)
    profile = await service.get_profile()
    return ProfileResponse(**profile)


@router.post(
    "/",
    response_model=ProfileResponse,
    summary="Update profile",
    description="Updates the current user's profile data."
)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile.
    """
    service = ProfileService(db, current_user)
    updated_user = await service.update_profile(
        full_name=profile_data.full_name,
        bio=profile_data.bio,
        avatar_file_id=profile_data.avatar_file_id
    )
    
    profile = await service.get_profile()
    return ProfileResponse(**profile)