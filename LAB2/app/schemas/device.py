from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Название устройства"
    )
    device_type: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="Тип устройства (лампа, термостат, датчик)"
    )
    location: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Расположение устройства"
    )
    status: bool = Field(
        default=False, 
        description="Статус устройства (вкл/выкл)"
    )
    value: Optional[float] = Field(
        None, 
        description="Значение (температура, яркость и т.д.)"
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Описание устройства"
    )

# Создание нового устройства
class DeviceCreate(DeviceBase):
    pass

# Частичное обновление устройства
class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[str] = Field(None, min_length=1, max_length=50)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[bool] = None
    value: Optional[float] = None
    description: Optional[str] = Field(None, max_length=500)

# Ответ API. Добавляет поля, которые генерируются сервером
class DeviceResponse(DeviceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Настройка для работы с SQLAlchemy моделями
    model_config = ConfigDict(from_attributes=True)

# Параматры пагинации
class PaginationParams(BaseModel):
    page: int = Field(
        1, 
        ge=1, 
        description="Номер страницы (начиная с 1)"
    )
    limit: int = Field(
        10, 
        ge=1, 
        le=100, 
        description="Количество элементов на странице (от 1 до 100)"
    )

# Ответ со списком устройств
class DeviceListResponse(BaseModel):
    data: list[DeviceResponse]      # Список устройств
    meta: dict                       # Метаинформация о пагинации
    
    model_config = ConfigDict(from_attributes=True)