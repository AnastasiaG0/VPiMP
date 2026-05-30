from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.api.v1 import router as v1_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.database import mongodb
from app.core.queue.consumer import EventConsumer
import asyncio
import logging

logger = logging.getLogger(__name__)

# Global consumer instance
_event_consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global _event_consumer
    
    # Startup
    await mongodb.connect()
    
    # Start RabbitMQ consumer
    try:
        print("🔄 Initializing RabbitMQ consumer...")
        _event_consumer = EventConsumer()
        # Run consumer in background task
        asyncio.create_task(_event_consumer.start())
        print("🚀 RabbitMQ consumer started successfully")
    except Exception as e:
        print(f"❌ Failed to start RabbitMQ consumer: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    
    # Shutdown
    if _event_consumer:
        await _event_consumer.stop()
    await mongodb.disconnect()

app = FastAPI(
    title="Smart Home API",
    description="API for Smart Home device management",
    version="2.0.0",
    docs_url="/api/docs" if settings.is_docs_enabled else None,
    openapi_url="/api/openapi.json" if settings.is_docs_enabled else None,
    lifespan=lifespan
)

# Include API routes
app.include_router(v1_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "Smart Home API",
        "version": "2.0.0",
        "database": "MongoDB",
        "docs": "/api/docs" if settings.is_docs_enabled else None,
        "async_events": "RabbitMQ"
    }


@app.get("/health")
async def health_check():
    """Check application health"""
    db_status = "healthy" if mongodb.client else "unhealthy"
    return {
        "status": "healthy",
        "database": db_status,
        "cache": "healthy",
        "queue": "configured"
    }


# FIXED validation exception handler - convert bytes to string
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    # Convert errors to JSON serializable format
    errors = []
    for error in exc.errors():
        # Convert any bytes in 'loc' to strings
        loc = []
        for item in error.get("loc", []):
            if isinstance(item, bytes):
                loc.append(item.decode("utf-8"))
            else:
                loc.append(str(item))
        
        errors.append({
            "loc": loc,
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", ""))
        })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


# General exception handler
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, 
    exc: Exception
):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}"
        }
    )


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Smart Home API",
        version="2.0.0",
        description="API for Smart Home device management",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "JWT token stored in HttpOnly cookie"
        },
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Alternative: Bearer <token>"
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
        "/auth/whoami",
    ]
    
    for path in openapi_schema["paths"]:
        is_public = any(path.startswith(public_path) for public_path in public_paths)
        
        for method in openapi_schema["paths"][path]:
            if not is_public:
                openapi_schema["paths"][path][method]["security"] = [
                    {"cookieAuth": []},
                    {"bearerAuth": []}
                ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi