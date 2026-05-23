import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()


class Settings:
    """Класс для хранения настроек приложения"""
    
    # Настройки базы данных
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "27017"))
    DB_USER: str = os.getenv("DB_USER", "student")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "student_secure_password")
    DB_NAME: str = os.getenv("DB_NAME", "smart_home")
    
    # URI для подключения к MongoDB
    MONGO_URI: str = os.getenv(
        "MONGO_URI",
        f"mongodb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?authSource=admin"
    )
    
    # Настройки приложения
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "4200"))
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Настройки JWT
    JWT_ACCESS_SECRET: str = os.getenv("JWT_ACCESS_SECRET", "access_secret")
    JWT_REFRESH_SECRET: str = os.getenv("JWT_REFRESH_SECRET", "refresh_secret")
    JWT_ACCESS_EXPIRATION: int = int(os.getenv("JWT_ACCESS_EXPIRATION", "15"))
    JWT_REFRESH_EXPIRATION: int = int(os.getenv("JWT_REFRESH_EXPIRATION", "10080"))

    # Настройки Yandex OAuth
    YANDEX_CLIENT_ID: str = os.getenv("YANDEX_CLIENT_ID", "")
    YANDEX_CLIENT_SECRET: str = os.getenv("YANDEX_CLIENT_SECRET", "")
    YANDEX_CALLBACK_URL: str = os.getenv("YANDEX_CALLBACK_URL", "http://localhost:4200/auth/oauth/yandex/callback")

    # Настройки Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    CACHE_TTL_DEFAULT: int = int(os.getenv("CACHE_TTL_DEFAULT", "300"))

    # Настройки MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "smart-home-files")
    MINIO_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10 MB
    ALLOWED_IMAGE_TYPES: list = os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/jpg").split(",")

    # Для формирования публичных URL (если нужно)
    MINIO_EXTERNAL_ENDPOINT: str = os.getenv("MINIO_EXTERNAL_ENDPOINT", "localhost:9000")
    

    @property
    def is_docs_enabled(self) -> bool:
        """Документация доступна только в режиме разработки"""
        return self.APP_ENV == "development"

# Создаем экземпляр настроек для использования в приложении
settings = Settings()