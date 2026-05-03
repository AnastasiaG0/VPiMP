from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"
    
    # Первичный ключ с автоинкрементом
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
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

    # Связь с пользователем
    user = relationship("User", back_populates="devices")   