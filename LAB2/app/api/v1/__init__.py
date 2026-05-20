"""
API version 1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import devices

router = APIRouter(prefix="/api/v1")
router.include_router(devices.router, prefix="/devices", tags=["devices"])

__all__ = ["router"]