from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings
import asyncio

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Устанавливает соединение с MongoDB"""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.database = self.client[settings.DB_NAME]
        
        # Проверяем соединение
        await self.client.admin.command('ping')
        print(f"[OK] Connected to MongoDB at {settings.DB_HOST}:{settings.DB_PORT}")
        
        # Создаем индексы
        await self.create_indexes()
    
    async def disconnect(self):
        """Закрывает соединение с MongoDB"""
        if self.client:
            self.client.close()
            print("[OK] Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Создает необходимые индексы для оптимизации запросов"""
        # Индексы для пользователей
        await self.database.users.create_index("email", unique=True)
        await self.database.users.create_index("yandex_id", unique=True, sparse=True)
        
        # Индексы для устройств
        await self.database.devices.create_index([("user_id", 1), ("deleted_at", 1)])
        await self.database.devices.create_index("name")
        await self.database.devices.create_index("device_type")
        await self.database.devices.create_index("location")
        
        # Индексы для refresh токенов
        await self.database.refresh_tokens.create_index("token_hash", unique=True)
        await self.database.refresh_tokens.create_index("expires_at")

        # Индексы для файлов
        await self.database.files.create_index("file_id", unique=True)
        await self.database.files.create_index([("user_id", 1), ("deleted_at", 1)])
        await self.database.files.create_index("created_at")

        # Индексы для пользователей (добавляем avatar_file_id)
        await self.database.users.create_index("avatar_file_id", sparse=True)
    
    async def get_collection(self, name: str):
        """Возвращает коллекцию MongoDB"""
        return self.database[name]

# Глобальный экземпляр
mongodb = MongoDB()

async def get_db():
    """Dependency для получения коллекции users (для совместимости)"""
    return mongodb.database