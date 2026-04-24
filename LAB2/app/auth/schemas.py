from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Для регистрации"""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Пароль не менее 6 символов")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Для входа"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Ответ с данными пользователя (без чувствительной информации)"""
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Ответ после успешного входа/обновления (для документации)"""
    message: str


class RefreshTokenRequest(BaseModel):
    """Для обновления токенов (тело не нужно, так как токен из куки)"""
    pass


class WhoamiResponse(BaseModel):
    """Ответ для /whoami"""
    authenticated: bool
    user: Optional[UserResponse] = None


class OAuthAuthorizeResponse(BaseModel):
    """Ответ для редиректа на провайдера"""
    redirect_url: str


class ForgotPasswordRequest(BaseModel):
    """Запрос на сброс пароля"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Установка нового пароля"""
    email: EmailStr
    token: str  # токен из письма (для упрощения - email, но в реальном проекте это должен быть JWT)
    new_password: str = Field(..., min_length=6)