from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr = Field(
        ..., 
        description="Email пользователя (используется для входа)",
        example="user@example.com"
    )
    password: str = Field(
        ..., 
        min_length=6, 
        description="Пароль (минимум 6 символов)",
        example="secure_password123",
        writeOnly=True
    )
    full_name: Optional[str] = Field(
        None, 
        description="Полное имя пользователя",
        example="Иван Иванов"
    )


class UserLogin(BaseModel):
    """Схема для входа в систему"""
    email: EmailStr = Field(
        ..., 
        description="Email пользователя",
        example="user@example.com"
    )
    password: str = Field(
        ..., 
        description="Пароль",
        example="secure_password123",
        writeOnly=True
    )


class UserResponse(BaseModel):
    """Ответ с данными пользователя (без чувствительной информации)"""
    id: str = Field(..., description="Уникальный идентификатор пользователя", example="673c4f5a8b1f2e3d4c5a6b7c")
    email: str = Field(..., description="Email пользователя", example="user@example.com")
    full_name: Optional[str] = Field(None, description="Полное имя пользователя", example="Иван Иванов")
    created_at: datetime = Field(..., description="Дата регистрации")
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Ответ после успешного входа/обновления токенов"""
    message: str = Field(..., description="Сообщение о результате операции")


class WhoamiResponse(BaseModel):
    """Ответ для эндпоинта /whoami - проверка статуса аутентификации"""
    authenticated: bool = Field(..., description="Аутентифицирован ли пользователь")
    user: Optional[UserResponse] = Field(None, description="Данные пользователя (если аутентифицирован)")


class OAuthAuthorizeResponse(BaseModel):
    """Ответ для редиректа на OAuth провайдера"""
    redirect_url: str = Field(..., description="URL для редиректа")


class ForgotPasswordRequest(BaseModel):
    """Запрос на сброс пароля"""
    email: EmailStr = Field(
        ..., 
        description="Email пользователя",
        example="user@example.com"
    )


class ResetPasswordRequest(BaseModel):
    """Установка нового пароля"""
    email: EmailStr = Field(
        ..., 
        description="Email пользователя",
        example="user@example.com"
    )
    token: str = Field(
        ..., 
        description="Токен сброса пароля",
        example="user@example.com"
    )
    new_password: str = Field(
        ..., 
        min_length=6,
        description="Новый пароль (минимум 6 символов)",
        example="new_secure_password123",
        writeOnly=True
    )