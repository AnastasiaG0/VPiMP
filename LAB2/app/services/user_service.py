from typing import Optional
from datetime import datetime
from bson import ObjectId
import uuid
import hashlib

from app.models.user import User, RefreshToken
from app.core.security import hash_password, verify_password, hash_token
from app.core.database import mongodb

class UserService:
    """Сервис для работы с пользователями в MongoDB"""
    
    def __init__(self):
        self.collection = None

    def _generate_yandex_id(self, email: str) -> str:
        """Генерирует уникальный yandex_id для обычных пользователей"""
        return f"local_{uuid.uuid4().hex}"
    
    async def _get_collection(self, name: str):
        """Ленивая инициализация коллекции"""
        if not self.collection:
            db = await mongodb.get_collection(name)
            self.collection = db.parent
        return self.collection[name]
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email"""
        collection = await mongodb.get_collection("users")
        user_data = await collection.find_one({"email": email, "deleted_at": None})
        if user_data:
            # Конвертируем ObjectId в строку перед созданием модели
            if "_id" in user_data:
                user_data["id"] = str(user_data["_id"])
            return User(**user_data)
        return None
    
    async def get_user_by_yandex_id(self, yandex_id: str) -> Optional[User]:
        """Получает пользователя по Yandex ID"""
        collection = await mongodb.get_collection("users")
        user_data = await collection.find_one({"yandex_id": yandex_id, "deleted_at": None})
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Получает пользователя по ID"""
        collection = await mongodb.get_collection("users")
        try:
            user_data = await collection.find_one({"_id": ObjectId(user_id), "deleted_at": None})
            if user_data:
                return User(**user_data)
        except:
            pass
        return None
    
    async def create_user(self, email: str, password: str = None, 
                          yandex_id: str = None, full_name: str = None) -> User:
        """Создает нового пользователя"""
        collection = await mongodb.get_collection("users")
        
        # Генерируем yandex_id, если не передан (т.е. для обычной регистрации)
        if yandex_id is None:
            yandex_id = self._generate_yandex_id(email)

        user_data = {
            "email": email,
            "full_name": full_name,
            "yandex_id": yandex_id,
            "created_at": datetime.utcnow()
        }
        
        if password:
            hashed, salt = hash_password(password)
            user_data["password_hash"] = hashed
            user_data["salt"] = salt
        
        result = await collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        
        return User(**user_data)
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[User]:
        """Обновляет пользователя"""
        collection = await mongodb.get_collection("users")
        update_data["updated_at"] = datetime.utcnow()
        
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_user_by_id(user_id)
        return None
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Аутентифицирует пользователя"""
        user = await self.get_user_by_email(email)
        if not user or not user.password_hash:
            return None
        
        if not verify_password(password, user.password_hash, user.salt):
            return None
        
        return user
    
    async def save_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        """Сохраняет refresh token"""
        collection = await mongodb.get_collection("refresh_tokens")
        
        token_data = {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        
        result = await collection.insert_one(token_data)
        token_data["_id"] = result.inserted_id
        
        return RefreshToken(**token_data)
    
    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Получает refresh token по хешу"""
        collection = await mongodb.get_collection("refresh_tokens")
        token_data = await collection.find_one({
            "token_hash": token_hash,
            "revoked_at": None,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if token_data:
            return RefreshToken(**token_data)
        return None
    
    async def revoke_refresh_token(self, token_hash: str) -> bool:
        """Отзывает refresh token"""
        collection = await mongodb.get_collection("refresh_tokens")
        result = await collection.update_one(
            {"token_hash": token_hash},
            {"$set": {"revoked_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Отзывает все refresh token пользователя"""
        collection = await mongodb.get_collection("refresh_tokens")
        result = await collection.update_many(
            {"user_id": user_id, "revoked_at": None},
            {"$set": {"revoked_at": datetime.utcnow()}}
        )
        return result.modified_count