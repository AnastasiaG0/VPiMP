from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.auth.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    WhoamiResponse, ForgotPasswordRequest, ResetPasswordRequest,
    OAuthAuthorizeResponse
)
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.core.oauth import (
    generate_oauth_state, verify_oauth_state, get_yandex_auth_url,
    exchange_yandex_code_for_token, get_yandex_user_info
)
from app.core.config import settings
from app.core.security import verify_access_token
from app.core.cache import cache_service

router = APIRouter(prefix="/auth", tags=["Authentication"], redirect_slashes=False)


# --- Регистрация и вход ---

@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя с указанными email, паролем и именем.",
    responses={
        201: {
            "description": "Пользователь успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "Иван Иванов",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        409: {
            "description": "Пользователь с таким email уже существует",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {"detail": "Validation error", "errors": []}
                }
            }
        }
    }
)
async def register(
    user_data: UserCreate,
    db = Depends(get_db)
):
    """Регистрация нового пользователя"""
    service = AuthService(db)
    user = await service.register_user(user_data)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at
    )


@router.post(
    "/login", 
    response_model=TokenResponse,
    summary="Вход в систему",
    description="Аутентификация пользователя. В случае успеха устанавливает HttpOnly cookies с access_token и refresh_token.",
    responses={
        200: {
            "description": "Успешный вход",
            "content": {
                "application/json": {
                    "example": {"message": "Successfully logged in"}
                }
            }
        },
        401: {
            "description": "Неверный email или пароль",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            }
        }
    }
)
async def login(
    response: Response,
    login_data: UserLogin,
    db = Depends(get_db)
):
    """Вход, установка cookies с токенами"""
    service = AuthService(db)
    user = await service.authenticate(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Генерируем токены
    access_token, refresh_token = await service.generate_tokens(user.id)
    
    # Устанавливаем HttpOnly cookies
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
    
    return {"message": "Successfully logged in"}


@router.post(
    "/refresh", 
    response_model=TokenResponse,
    summary="Обновление токенов",
    description="Использует refresh_token из cookies для получения новой пары токенов.",
    responses={
        200: {
            "description": "Токены успешно обновлены",
            "content": {
                "application/json": {
                    "example": {"message": "Tokens refreshed"}
                }
            }
        },
        401: {
            "description": "Refresh token отсутствует или недействителен",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired refresh token"}
                }
            }
        }
    }
)
async def refresh(
    request: Request,
    response: Response,
    db = Depends(get_db)
):
    """Обновление пары токенов"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    service = AuthService(db)
    result = await service.refresh_tokens(refresh_token)
    
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


@router.get(
    "/whoami", 
    response_model=WhoamiResponse,
    summary="Проверка статуса аутентификации",
    description="Возвращает информацию о текущем аутентифицированном пользователе.",
    responses={
        200: {
            "description": "Информация о статусе аутентификации",
            "content": {
                "application/json": {
                    "examples": {
                        "authenticated": {
                            "summary": "Пользователь аутентифицирован",
                            "value": {
                                "authenticated": True,
                                "user": {
                                    "id": 1,
                                    "email": "user@example.com",
                                    "full_name": "Иван Иванов",
                                    "created_at": "2024-01-15T10:30:00Z"
                                }
                            }
                        },
                        "unauthenticated": {
                            "summary": "Пользователь не аутентифицирован",
                            "value": {
                                "authenticated": False,
                                "user": None
                            }
                        }
                    }
                }
            }
        }
    }
)
async def whoami(
    request: Request,
    db = Depends(get_db)
):
    """Проверка статуса аутентификации с кешированием профиля"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return WhoamiResponse(authenticated=False, user=None)
    
    user_id, jti = verify_access_token(access_token)
    if not user_id:
        return WhoamiResponse(authenticated=False, user=None)
    
    # Пытаемся получить профиль из кеша
    cached_user = cache_service.get("user:profile", user_id)
    if cached_user:
        return WhoamiResponse(
            authenticated=True,
            user=UserResponse(**cached_user)
        )
    
    # Cache miss - получаем из БД
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        return WhoamiResponse(authenticated=False, user=None)
    
    # Проверяем JTI в Redis
    if not cache_service.has_jti(user_id, jti):
        return WhoamiResponse(authenticated=False, user=None)
    
    # Сохраняем в кеш
    user_data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    cache_service.set("user:profile", user_data, 300, user_id)
    
    return WhoamiResponse(
        authenticated=True,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at
        )
    )


@router.post(
    "/logout", 
    response_model=TokenResponse,
    summary="Выход из системы",
    description="Завершает текущую сессию, отзывая refresh_token и удаляя cookies.",
    responses={
        200: {
            "description": "Успешный выход",
            "content": {
                "application/json": {
                    "example": {"message": "Successfully logged out"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        }
    }
)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Завершение текущей сессии"""
    refresh_token = request.cookies.get("refresh_token")

    # Извлекаем JTI из текущего Access Token
    access_token = request.cookies.get("access_token")
    _, jti = verify_access_token(access_token) if access_token else (None, None)

    if refresh_token or jti:
        service = AuthService(db)
        await service.revoke_token(refresh_token, jti, user.id)
    
    # Инвалидируем кеш профиля
    cache_service.delete("user:profile", user.id)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out"}


@router.post(
    "/logout-all", 
    response_model=TokenResponse,
    summary="Завершение всех сессий",
    description="Отзывает все refresh_token пользователя, завершая все активные сессии.",
    responses={
        200: {
            "description": "Все сессии завершены",
            "content": {
                "application/json": {
                    "example": {"message": "All sessions terminated"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        }
    }
)
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Завершение всех сессий пользователя"""
    service = AuthService(db)
    await service.revoke_all_user_tokens(user.id)
    
    # Инвалидируем кеш профиля
    cache_service.delete("user:profile", user.id)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "All sessions terminated"}   


# --- OAuth ---

@router.get(
    "/oauth/yandex",
    summary="OAuth через Яндекс",
    description="Инициирует OAuth 2.0 поток аутентификации через Яндекс ID.",
    responses={
        307: {
            "description": "Редирект на страницу авторизации Яндекса"
        }
    }
)
async def oauth_yandex():
    """Инициация входа через Yandex ID"""
    state = generate_oauth_state()
    redirect_url = get_yandex_auth_url(state)
    return RedirectResponse(url=redirect_url)


@router.get(
    "/oauth/yandex/callback",
    summary="Callback OAuth Яндекс",
    description="Обработчик callback URL от Яндекс ID после авторизации пользователя.",
    responses={
        307: {
            "description": "Редирект на главную страницу после успешной авторизации"
        },
        400: {
            "description": "Ошибка при обмене кода или получении данных пользователя",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_state": {
                            "summary": "Неверный параметр state",
                            "value": {"detail": "Invalid state parameter"}
                        },
                        "code_exchange_failed": {
                            "summary": "Не удалось обменять код",
                            "value": {"detail": "Failed to exchange code for token"}
                        },
                        "userinfo_failed": {
                            "summary": "Не удалось получить данные пользователя",
                            "value": {"detail": "Failed to get user info"}
                        }
                    }
                }
            }
        }
    }
)
async def oauth_yandex_callback(
    code: str,
    state: str,
    response: Response,
    db = Depends(get_db)
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
    user = await service.create_or_update_yandex_user(yandex_id, email, name)
    
    # Генерируем локальные токены
    access_token, refresh_token = await service.generate_tokens(user.id)
    
    # Редирект на фронтенд с установкой cookies
    response = RedirectResponse(url="http://localhost:4200", status_code=302)

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
    return response


# --- Сброс пароля ---

@router.post(
    "/forgot-password", 
    response_model=TokenResponse,
    summary="Запрос сброса пароля",
    description="Отправляет токен сброса пароля на указанный email (в упрощенной реализации - возвращает токен в ответе).",
    responses={
        200: {
            "description": "Запрос обработан",
            "content": {
                "application/json": {
                    "example": {"message": "If email exists, reset link has been sent"}
                }
            }
        }
    }
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db = Depends(get_db)
):
    service = AuthService(db)
    token = await service.generate_password_reset_token(request.email)
    
    if token:
        print(f"Reset token for {request.email}: {token}")
    
    return {"message": "If email exists, reset link has been sent"}


@router.post(
    "/reset-password", 
    response_model=TokenResponse,
    summary="Сброс пароля",
    description="Устанавливает новый пароль с использованием токена сброса.",
    responses={
        200: {
            "description": "Пароль успешно изменен",
            "content": {
                "application/json": {
                    "example": {"message": "Password has been reset"}
                }
            }
        },
        400: {
            "description": "Неверный или истекший токен",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired token"}
                }
            }
        }
    }
)
async def reset_password(
    request: ResetPasswordRequest,
    db = Depends(get_db)
):
    """Установка нового пароля"""
    service = AuthService(db)
    success = await service.reset_password(request.email, request.token, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Инвалидируем кеш профиля
    user = await service.get_user_by_email(request.email)
    if user:
        cache_service.delete("user:profile", user.id)
    
    return {"message": "Password has been reset"}