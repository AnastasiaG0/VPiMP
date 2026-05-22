from fastapi import Depends, HTTPException, status, Request
from typing import Optional

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.security import verify_access_token
from app.core.cache import cache_service


async def get_current_user(
    request: Request,
    db = Depends(get_db)
) -> User:
    """
    Извлекает Access Token из Cookie, проверяет его и возвращает пользователя.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_id, jti = verify_access_token(access_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    # Если Redis недоступен, пропускаем проверку JTI
    if cache_service.is_available():
        # Проверяем, активен ли токен в Redis
        if not cache_service.has_jti(user_id, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


async def get_current_user_optional(
    request: Request,
    db = Depends(get_db)
) -> Optional[User]:
    """Опциональная зависимость - возвращает пользователя или None"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    
    user_id, jti = verify_access_token(access_token)
    if not user_id:
        return None
    
    # Если Redis доступен, проверяем JTI
    if cache_service.is_available() and not cache_service.has_jti(user_id, jti):
        return None

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        return None
    
    return user