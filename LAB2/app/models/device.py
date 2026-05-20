from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from app.database import Base


class Device(Base):
    __tablename__ = "devices"
    
    # Первичный ключ с автоинкрементом
    id = Column(Integer, primary_key=True, index=True)
    
    # Основные поля устройства
    name = Column(String(100), nullable=False, index=True)
    device_type = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    status = Column(Boolean, default=False)
    value = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)