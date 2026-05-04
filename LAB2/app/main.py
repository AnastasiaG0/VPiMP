from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.api.v1 import router as v1_router
from app.auth.router import router as auth_router
from app.core.config import settings

app = FastAPI(
    title="Smart Home API",
    description="API для управления устройствами умного дома",
    version="2.0.0",
    docs_url="/api/docs" if settings.is_docs_enabled else None,
    #redoc_url="/api/redoc" if settings.is_docs_enabled else None,
    openapi_url="/api/openapi.json" if settings.is_docs_enabled else None,
)

# Подключение маршрутов API
app.include_router(v1_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "Smart Home API",
        "version": "2.0.0",
        "docs": "/api/docs" if settings.is_docs_enabled else None
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Кастомизация OpenAPI схемы для улучшения документации
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Smart Home API",
        version="2.0.0",
        description="API для управления устройствами умного дома",
        #description="""
        # Умный дом API
        
        #API для управления устройствами умного дома с поддержкой:
        #* Регистрации и аутентификации пользователей
        #* OAuth 2.0 через Яндекс ID
        #* Управления устройствами (CRUD операции)
        #* Мягкого удаления устройств
        
        ## Аутентификация
        
        #API использует JWT токены, которые хранятся в HttpOnly Cookies:
        #* access_token - доступ к защищенным эндпоинтам (15 минут)
        #* refresh_token - обновление пары токенов (7 дней)
        
        ### Как тестировать защищенные эндпоинты в Swagger UI:
        
        #1. Выполните запрос `POST /auth/login` с вашими учетными данными
        #2. Cookies установятся автоматически через браузер
        #3. После этого все защищенные эндпоинты будут доступны
        
        #Или используйте OAuth:
        
        #1. Перейдите по `GET /auth/oauth/yandex`
        #2. Пройдите авторизацию через Яндекс
        #3. Вернитесь обратно - сессия установлена
        #""",
        routes=app.routes,
    )
    
    # Добавляем схему безопасности для Bearer токена (для альтернативного способа)
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "JWT токен, хранящийся в HttpOnly cookie. Автоматически отправляется браузером после входа."
        },
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Альтернативный способ: Bearer <token>"
        }
    }

    public_paths = [
        "/",
        "/health",
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/auth/forgot-password",
        "/auth/reset-password",
        "/auth/oauth/yandex",
        "/auth/oauth/yandex/callback",
        "/auth/whoami",  # whoami - публичный, он сам определяет статус
    ]
    
    for path in openapi_schema["paths"]:
        # Проверяем, является ли путь публичным
        is_public = any(path.startswith(public_path) for public_path in public_paths)
        
        for method in openapi_schema["paths"][path]:
            if not is_public:
                # Добавляем security к защищенным эндпоинтам
                openapi_schema["paths"][path][method]["security"] = [
                    {"cookieAuth": []},
                    {"bearerAuth": []}
                ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


# Обработчик непредвиденных ошибок
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, 
    exc: Exception
):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error"
        }
    )