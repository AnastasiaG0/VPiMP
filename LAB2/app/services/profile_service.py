from typing import Optional
from fastapi import HTTPException, status
from datetime import datetime
from bson import ObjectId

from app.models.user import User
from app.services.file_service import FileService
from app.core.database import mongodb
from app.core.cache import cache_service
from app.core.config import settings


class ProfileService:
    """Service for managing user profile"""
    
    def __init__(self, db, user: User):
        self.db = db
        self.user = user
        self.file_service = FileService(db, user.id)
    
    async def get_profile(self) -> dict:
        """Get user profile."""
        cached = cache_service.get("user", "profile", self.user.id)
        if cached:
            return cached
        
        profile = {
            "id": self.user.id,
            "email": self.user.email,
            "full_name": self.user.full_name,
            "bio": getattr(self.user, 'bio', None),
            "avatar_file_id": getattr(self.user, 'avatar_file_id', None),
            "created_at": self.user.created_at.isoformat() if self.user.created_at else None,
        }
        
        if profile["avatar_file_id"]:
            profile["avatar_url"] = f"/api/v1/files/{profile['avatar_file_id']}"
        
        cache_service.set("user", "profile", profile, settings.CACHE_TTL_DEFAULT, self.user.id)
        
        return profile
    
    async def update_profile(self, full_name: Optional[str] = None, bio: Optional[str] = None, avatar_file_id: Optional[str] = None) -> User:
        """Update user profile."""
        update_data = {}
        
        if full_name is not None:
            update_data["full_name"] = full_name
        
        if bio is not None:
            update_data["bio"] = bio
        
        if avatar_file_id is not None:
            file_metadata = await self.file_service.get_file_metadata(avatar_file_id)
            if not file_metadata:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Avatar file not found"
                )
            
            old_avatar_id = getattr(self.user, 'avatar_file_id', None)
            update_data["avatar_file_id"] = avatar_file_id
            
            if old_avatar_id:
                try:
                    await self.file_service.delete_file(old_avatar_id)
                except Exception as e:
                    print(f"Failed to delete old avatar {old_avatar_id}: {e}")
        
        if not update_data:
            return self.user
        
        update_data["updated_at"] = datetime.utcnow()
        
        collection = mongodb.database["users"]
        await collection.update_one(
            {"_id": ObjectId(self.user.id)},
            {"$set": update_data}
        )
        
        for key, value in update_data.items():
            setattr(self.user, key, value)
        
        cache_service.delete("user", "profile", self.user.id)
        
        return self.user