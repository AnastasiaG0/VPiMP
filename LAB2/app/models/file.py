from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from uuid import uuid4


class FileMetadata(BaseModel):
    """Модель метаданных файла для MongoDB"""
    id: Optional[str] = Field(default=None, alias="_id")
    file_id: str = Field(default_factory=lambda: str(uuid4()))  # UUID для внешних ссылок
    user_id: str  # ID пользователя-владельца
    original_name: str
    object_key: str  # Ключ объекта в MinIO
    bucket: str
    size: int  # Размер в байтах
    mimetype: str
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
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def dict(self, *args, **kwargs):
        """Переопределяем dict для корректной сериализации"""
        # Убираем exclude_sensitive если он есть, так как он не поддерживается
        kwargs.pop('exclude_sensitive', None)
        
        d = super().dict(*args, **kwargs)
        if "_id" in d:
            d["id"] = str(d["_id"])
            del d["_id"]
        return d
    
    def to_response_dict(self):
        """Возвращает словарь для публичных ответов (без чувствительных полей)"""
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "size": self.size,
            "mimetype": self.mimetype,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "url": f"/files/{self.file_id}"
        }