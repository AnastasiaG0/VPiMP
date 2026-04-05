from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from app.database import Base


class Device(Base):
    """
    Модель устройства умного дома.
    Реализует мягкое удаление через поле deleted_at.
    """
    __tablename__ = "devices"  # Имя таблицы в базе данных
    
    # Первичный ключ с автоинкрементом
    id = Column(Integer, primary_key=True, index=True)
    
    # Основные поля устройства
    name = Column(String(100), nullable=False, index=True)        # Название устройства
    device_type = Column(String(50), nullable=False)              # Тип (лампа, термостат, датчик)
    location = Column(String(100), nullable=False)                # Расположение (комната)
    status = Column(Boolean, default=False)                       # Включено/выключено
    value = Column(Float, nullable=True)                          # Значение (температура, яркость)
    description = Column(Text, nullable=True)                     # Описание
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Время создания
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())        # Время обновления
    deleted_at = Column(DateTime(timezone=True), nullable=True)               # Время удаления (soft delete)
    
    def soft_delete(self):
        """
        Метод для мягкого удаления устройства.
        Устанавливает время удаления вместо физического удаления записи.
        """
        self.deleted_at = func.now()
    
    @property
    def is_active(self) -> bool:
        """
        Свойство, проверяющее активна ли запись (не удалена).
        """
        return self.deleted_at is None