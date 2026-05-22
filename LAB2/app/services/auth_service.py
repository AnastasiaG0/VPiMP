from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

from app.services.user_service import UserService
from app.auth.schemas import UserCreate
from app.core.security import (
    generate_access_token, generate_refresh_token, 
    verify_refresh_token, hash_token
)
from app.core.config import settings
from app.core.cache import cache_service

class AuthService:
    def __init__(self, db):
        self.db = db
        self.user_service = UserService()
    
    async def register_user(self, user_data: UserCreate):
        """Регистрация нового пользователя"""
        existing = await self.user_service.get_user_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        user = await self.user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        return user
    
    async def authenticate(self, email: str, password: str):
        """Аутентификация пользователя"""
        return await self.user_service.authenticate(email, password)
    
    async def get_user_by_id(self, user_id: str):
        """Получение пользователя по ID"""
        return await self.user_service.get_user_by_id(user_id)
    
    async def get_user_by_email(self, email: str):
        """Получение пользователя по email"""
        return await self.user_service.get_user_by_email(email)
    
    async def create_or_update_yandex_user(self, yandex_id: str, email: str, name: str):
        """Создание или обновление пользователя через Yandex"""
        user = await self.user_service.get_user_by_yandex_id(yandex_id)
        if user:
            return user
        
        user_by_email = await self.user_service.get_user_by_email(email)
        if user_by_email:
            await self.user_service.update_user(user_by_email.id, {"yandex_id": yandex_id})
            return await self.user_service.get_user_by_id(user_by_email.id)
        
        return await self.user_service.create_user(
            email=email,
            yandex_id=yandex_id,
            full_name=name
        )
    
    async def generate_tokens(self, user_id: str) -> Tuple[str, str]:
        """Генерация пары токенов"""
        access_token, jti = generate_access_token(user_id)
        cache_service.set_jti(user_id, jti, settings.JWT_ACCESS_EXPIRATION * 60)
        
        refresh_token = generate_refresh_token(user_id)
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
        
        await self.user_service.save_refresh_token(user_id, token_hash, expires_at)
        
        return access_token, refresh_token
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Обновление пары токенов"""
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            return None
        
        token_hash = hash_token(refresh_token)
        db_token = await self.user_service.get_refresh_token(token_hash)
        
        if not db_token:
            return None
        
        await self.user_service.revoke_refresh_token(token_hash)
        
        return await self.generate_tokens(user_id)
    
    async def revoke_token(self, refresh_token: str = None, access_jti: str = None, user_id: str = None):
        """Отзыв токена"""
        if refresh_token:
            token_hash = hash_token(refresh_token)
            await self.user_service.revoke_refresh_token(token_hash)
        
        if access_jti and user_id:
            cache_service.delete_jti(user_id, access_jti)
        
        return True
    
    async def revoke_all_user_tokens(self, user_id: str):
        """Отзыв всех токенов пользователя"""
        await self.user_service.revoke_all_user_tokens(user_id)
        cache_service.delete_all_user_jti(user_id)
        return True
    
    async def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Генерация токена сброса пароля"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        return email
    
    async def reset_password(self, email: str, token: str, new_password: str) -> bool:
        """Сброс пароля"""
        if token != email:
            return False
        
        user = await self.get_user_by_email(email)
        if not user or not user.password_hash:
            return False
        
        from app.core.security import hash_password
        hashed, salt = hash_password(new_password)
        
        await self.user_service.update_user(user.id, {
            "password_hash": hashed,
            "salt": salt
        })
        
        await self.revoke_all_user_tokens(user.id)
        return True