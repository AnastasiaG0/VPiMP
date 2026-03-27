import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()


class Settings:
    """Класс для хранения настроек приложения"""
    
    # Настройки базы данных
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "smart_home")
    
    # URL для подключения к базе данных
    DATABASE_URL: str = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # Настройки приложения
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "4200"))


# Создаем экземпляр настроек для использования в приложении
settings = Settings()