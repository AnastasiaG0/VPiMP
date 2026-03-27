from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    """
    Базовый класс для всех схем устройств.
    Содержит общие поля.
    """
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


class DeviceCreate(DeviceBase):
    """
    Схема для создания нового устройства.
    Наследует все поля от DeviceBase.
    """
    pass


class DeviceUpdate(BaseModel):
    """
    Схема для частичного обновления устройства.
    Все поля опциональны.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[str] = Field(None, min_length=1, max_length=50)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[bool] = None
    value: Optional[float] = None
    description: Optional[str] = Field(None, max_length=500)


class DeviceResponse(DeviceBase):
    """
    Схема для ответа API.
    Добавляет поля, которые генерируются сервером.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Настройка для работы с SQLAlchemy моделями
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """
    Параметры пагинации.
    Используется для валидации query-параметров.
    """
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


class DeviceListResponse(BaseModel):
    """
    Схема для ответа со списком устройств.
    Включает данные и метаинформацию для пагинации.
    """
    data: list[DeviceResponse]      # Список устройств
    meta: dict                       # Метаинформация о пагинации
    
    model_config = ConfigDict(from_attributes=True)