from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.auth.service import AuthService
from app.auth.models import User
from app.core.security import verify_access_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Извлекает Access Token из Cookie, проверяет его и возвращает пользователя.
    Используется для защиты эндпоинтов.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_id = verify_access_token(access_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Опциональная зависимость - возвращает пользователя или None"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    
    user_id = verify_access_token(access_token)
    if not user_id:
        return None
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        return None
    
    return user