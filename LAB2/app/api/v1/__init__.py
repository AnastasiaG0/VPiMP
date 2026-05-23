"""
API version 1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import devices, files, profile

router = APIRouter(prefix="/api/v1")
router.include_router(devices.router, prefix="/devices", tags=["Devices"])
router.include_router(files.router, prefix="/files", tags=["Files"])
router.include_router(profile.router, prefix="/profile", tags=["Profile"])

__all__ = ["router"]