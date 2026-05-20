from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import secrets

from app.core.database import get_db
from app.auth.service import AuthService
from app.auth.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    WhoamiResponse, ForgotPasswordRequest, ResetPasswordRequest
)
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.auth.models import User
from app.core.oauth import (
    generate_oauth_state, verify_oauth_state, get_yandex_auth_url,
    exchange_yandex_code_for_token, get_yandex_user_info
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Регистрация и вход ---

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
    service = AuthService(db)
    user = service.register_user(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Вход, установка cookies с токенами"""
    service = AuthService(db)
    user = service.authenticate(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Генерируем токены
    access_token, refresh_token = service.generate_tokens(user.id)
    
    # Устанавливаем HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # в production должно быть True (HTTPS)
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRATION * 60  # в секундах
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRATION * 60
    )
    
    return {"message": "Successfully logged in"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Обновление пары токенов"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    service = AuthService(db)
    result = service.refresh_tokens(refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    new_access, new_refresh = result
    
    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRATION * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRATION * 60
    )
    
    return {"message": "Tokens refreshed"}


@router.get("/whoami", response_model=WhoamiResponse)
async def whoami(user: Optional[User] = Depends(get_current_user_optional)):
    """Проверка статуса аутентификации"""
    if user:
        return WhoamiResponse(
            authenticated=True,
            user=UserResponse.model_validate(user)
        )
    return WhoamiResponse(authenticated=False, user=None)


@router.post("/logout", response_model=TokenResponse)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Завершение текущей сессии"""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        service = AuthService(db)
        service.revoke_token(refresh_token)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all", response_model=TokenResponse)
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Завершение всех сессий пользователя"""
    service = AuthService(db)
    service.revoke_all_user_tokens(user.id)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "All sessions terminated"}


# --- OAuth ---

@router.get("/oauth/yandex")
async def oauth_yandex():
    """Инициация входа через Yandex ID"""
    state = generate_oauth_state()
    redirect_url = get_yandex_auth_url(state)
    return RedirectResponse(url=redirect_url)


@router.get("/oauth/yandex/callback")
async def oauth_yandex_callback(
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Callback от Yandex"""
    # Проверяем state
    if not verify_oauth_state(state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Обмениваем код на токен
    yandex_token = await exchange_yandex_code_for_token(code)
    if not yandex_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
    
    # Получаем данные пользователя
    user_info = await get_yandex_user_info(yandex_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info"
        )
    
    yandex_id = str(user_info.get("id"))
    email = user_info.get("default_email")
    name = user_info.get("real_name") or user_info.get("display_name")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Yandex"
        )
    
    # Создаем или обновляем пользователя
    service = AuthService(db)
    user = service.create_or_update_yandex_user(yandex_id, email, name)
    
    # Генерируем локальные токены
    access_token, refresh_token = service.generate_tokens(user.id)
    
    # Устанавливаем cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRATION * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRATION * 60
    )
    
    # Редирект на фронтенд
    return RedirectResponse(url="http://localhost:4200")  # изменить на адрес фронтенда


# --- Сброс пароля (упрощенный) ---

@router.post("/forgot-password", response_model=TokenResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Запрос на сброс пароля (отправляет токен на email)"""
    service = AuthService(db)
    token = service.generate_password_reset_token(request.email)
    
    if token:
        # В реальном проекте здесь отправка email
        print(f"Reset token for {request.email}: {token}")
        return {"message": "If email exists, reset link has been sent"}
    
    # Всегда возвращаем успех, чтобы не раскрывать существование email
    return {"message": "If email exists, reset link has been sent"}


@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Установка нового пароля"""
    service = AuthService(db)
    success = service.reset_password(request.email, request.token, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    return {"message": "Password has been reset"}