from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.v1 import router as v1_router

# Создаем экземпляр приложения FastAPI
app = FastAPI(
    title="Smart Home API",
    description="API для управления устройствами умного дома",
    version="2.0.0"
)

# Подключаем маршруты API
app.include_router(v1_router)


@app.get("/")
async def root():
    """
    Корневой эндпоинт с информацией о сервисе.
    """
    return {
        "message": "Smart Home API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Эндпоинт для проверки работоспособности сервиса.
    """
    return {"status": "healthy"}


# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    """
    Обработка ошибок валидации данных.
    Возвращает 400 Bad Request с деталями ошибки.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


# Обработчик общих ошибок
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, 
    exc: Exception
):
    """
    Обработка непредвиденных ошибок.
    Возвращает 500 Internal Server Error без деталей.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error"
        }
    )