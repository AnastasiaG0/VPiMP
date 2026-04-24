from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# Создаем движок для подключения к PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    echo=False           # Установите True для логирования SQL запросов
)

# Создаем фабрику сессий для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Функция-зависимость для получения сессии базы данных.
    Используется в эндпоинтах FastAPI.
    """
    db = SessionLocal()
    try:
        yield db          # Возвращаем сессию
    finally:
        db.close()        # Закрываем сессию после использования