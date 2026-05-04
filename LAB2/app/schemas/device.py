from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Название устройства",
        example="Гостиная лампа"
    )
    device_type: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="Тип устройства",
        examples=["лампа", "термостат", "датчик движения", "розетка"]
    )
    location: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Расположение устройства",
        example="Гостиная"
    )
    status: bool = Field(
        default=False, 
        description="Статус устройства (вкл/выкл)",
        example=True
    )
    value: Optional[float] = Field(
        None, 
        description="Значение (температура в °C, яркость в % и т.д.)",
        examples=[22.5, 75]
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Описание устройства",
        example="LED лампа с регулировкой яркости"
    )

class DeviceCreate(DeviceBase):
    """Схема для создания нового устройства"""
    pass

class DeviceUpdate(BaseModel):
    """Схема для частичного обновления устройства"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, example="Обновленное название")
    device_type: Optional[str] = Field(None, min_length=1, max_length=50, example="термостат")
    location: Optional[str] = Field(None, min_length=1, max_length=100, example="Спальня")
    status: Optional[bool] = Field(None, example=False)
    value: Optional[float] = Field(None, example=21.0)
    description: Optional[str] = Field(None, max_length=500, example="Обновленное описание")

# Ответ API. Добавляет поля, которые генерируются сервером
class DeviceResponse(DeviceBase):
    """Ответ API с данными устройства"""
    id: int = Field(..., description="Уникальный идентификатор устройства", example=1)
    created_at: datetime = Field(..., description="Дата создания устройства")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")
    
    # Настройка для работы с SQLAlchemy моделями
    model_config = ConfigDict(from_attributes=True)

class PaginationParams(BaseModel):
    """Параметры пагинации"""
    page: int = Field(
        1, 
        ge=1, 
        description="Номер страницы (начиная с 1)",
        example=1
    )
    limit: int = Field(
        10, 
        ge=1, 
        le=100, 
        description="Количество элементов на странице (от 1 до 100)",
        example=10
    )

class DeviceListResponse(BaseModel):
    """Ответ со списком устройств"""
    data: list[DeviceResponse] = Field(..., description="Список устройств")
    meta: dict = Field(
        ..., 
        description="Метаинформация о пагинации",
        example={
            "total": 25,
            "page": 2,
            "limit": 10,
            "total_pages": 3
        }
    )
    
    model_config = ConfigDict(from_attributes=True)