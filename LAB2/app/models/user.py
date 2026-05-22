from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from bson import ObjectId


class User(BaseModel):
    """Модель пользователя для MongoDB"""
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    password_hash: Optional[str] = None
    salt: Optional[str] = None
    yandex_id: Optional[str] = None
    full_name: Optional[str] = None
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
    def is_active(self) -> bool:
        return self.deleted_at is None
    
    def dict(self, *args, **kwargs):
        """Переопределяем dict для корректной сериализации ObjectId"""
        d = super().dict(*args, **kwargs)
        if "_id" in d:
            d["id"] = str(d["_id"])
            del d["_id"]
        return d


class RefreshToken(BaseModel):
    """Модель Refresh токена"""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
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