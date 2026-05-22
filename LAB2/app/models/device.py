from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class Device(BaseModel):
    """Модель устройства для MongoDB"""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Строковый ID пользователя
    name: str
    device_type: str
    location: str
    status: bool = False
    value: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid(cls, v):
        """Конвертирует ObjectId в строку"""
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
    
    def dict(self, *args, **kwargs):
        """Переопределяем dict для корректной сериализации"""
        d = super().dict(*args, **kwargs)
        if "_id" in d:
            d["id"] = str(d["_id"])
            del d["_id"]
        return d