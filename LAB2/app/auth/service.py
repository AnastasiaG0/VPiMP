from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.auth.models import User, RefreshToken
from app.auth.schemas import UserCreate
from app.core.security import (
    hash_password, verify_password, generate_access_token, 
    generate_refresh_token, verify_refresh_token, hash_token
)
from app.core.config import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    # --- Пользователи ---
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()
    
    def get_user_by_yandex_id(self, yandex_id: str) -> Optional[User]:
        return self.db.query(User).filter(
            User.yandex_id == yandex_id,
            User.deleted_at.is_(None)
        ).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
    
    def register_user(self, user_data: UserCreate) -> User:
        # Проверка на существование
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Хешируем пароль
        hashed, salt = hash_password(user_data.password)
        
        user = User(
            email=user_data.email,
            password_hash=hashed,
            salt=salt,
            full_name=user_data.full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user or not user.password_hash:
            return None
        
        if not verify_password(password, user.password_hash, user.salt):
            return None
        
        return user
    
    def create_or_update_yandex_user(self, yandex_id: str, email: str, name: str) -> User:
        user = self.get_user_by_yandex_id(yandex_id)
        if user:
            return user
        
        # Проверка, не зарегистрирован ли email
        user_by_email = self.get_user_by_email(email)
        if user_by_email:
            # Связываем существующего пользователя с Yandex ID
            user_by_email.yandex_id = yandex_id
            self.db.commit()
            self.db.refresh(user_by_email)
            return user_by_email
        
        # Создаем нового пользователя
        user = User(
            email=email,
            yandex_id=yandex_id,
            full_name=name,
            password_hash=None,
            salt=None
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # --- Токены ---
    
    def generate_tokens(self, user_id: int) -> Tuple[str, str]:
        """Генерирует пару токенов и сохраняет Refresh Token в БД"""
        access_token = generate_access_token(user_id)
        refresh_token = generate_refresh_token(user_id)
        
        # Сохраняем хеш Refresh Token
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
        
        # Удаляем старые неотозванные токены пользователя? (по желанию)
        # self.db.query(RefreshToken).filter(
        #     RefreshToken.user_id == user_id,
        #     RefreshToken.revoked_at.is_(None)
        # ).delete()
        
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(db_token)
        self.db.commit()
        
        return access_token, refresh_token
    
    def refresh_tokens(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Обновляет пару токенов по Refresh Token"""
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            return None
        
        # Проверяем наличие токена в БД (не отозван, не истек)
        token_hash = hash_token(refresh_token)
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not db_token:
            return None
        
        # Удаляем использованный токен
        self.db.delete(db_token)
        self.db.commit()
        
        # Генерируем новую пару
        return self.generate_tokens(user_id)
    
    def revoke_token(self, refresh_token: str) -> bool:
        """Отзывает конкретный Refresh Token (logout)"""
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            return False
        
        token_hash = hash_token(refresh_token)
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).first()
        
        if db_token:
            db_token.revoked_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
    
    def revoke_all_user_tokens(self, user_id: int) -> bool:
        """Отзывает все Refresh Token пользователя (logout-all)"""
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).all()
        
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
    
    # --- Сброс пароля (упрощенная версия) ---
    
    def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Генерирует токен для сброса пароля (в реальном проекте используйте JWT)"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        # Для простоты возвращаем email (в реальности - подписанный JWT)
        return email
    
    def reset_password(self, email: str, token: str, new_password: str) -> bool:
        """Сбрасывает пароль"""
        if token != email:  # упрощенная проверка
            return False
        
        user = self.get_user_by_email(email)
        if not user or not user.password_hash:  # OAuth-пользователи не имеют пароля
            return False
        
        hashed, salt = hash_password(new_password)
        user.password_hash = hashed
        user.salt = salt
        self.db.commit()
        
        # Отзываем все сессии после смены пароля
        self.revoke_all_user_tokens(user.id)
        return True