from typing import Optional, Tuple, List
from datetime import datetime
import hashlib
from bson import ObjectId

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.cache import cache_service
from app.core.database import mongodb


class DeviceService:
    """Сервис для работы с устройствами в MongoDB"""
    
    def __init__(self, db, user_id: str):  # <-- user_id теперь str (ObjectId)
        self.db = db  # Это объект database из MongoDB
        self.user_id = user_id
    
    def _serialize_device(self, device: Device) -> dict:
        """Сериализует объект Device в словарь для кеширования"""
        return device.dict()
    
    def _deserialize_device(self, data: dict) -> Device:
        """Восстанавливает объект Device из словаря"""
        return Device(**data)
    
    async def get_device(self, device_id: str) -> Optional[Device]:
        """Получение устройства по ID"""
        # Пытаемся получить из кеша
        cached = cache_service.get("devices:item", self.user_id, device_id)
        
        if cached:
            return self._deserialize_device(cached)
        
        # Cache miss - запрос к MongoDB
        collection = self.db.devices
        try:
            device_data = await collection.find_one({
                "_id": ObjectId(device_id),
                "user_id": self.user_id,
                "deleted_at": None
            })
            
            if device_data:
                device = Device(**device_data)
                cache_service.set("devices:item", device.dict(), 300, self.user_id, device_id)
                return device
        except Exception as e:
            print(f"Error getting device: {e}")
        
        return None
    
    async def get_device_by_name(self, name: str) -> Optional[Device]:
        """Получение устройства по имени"""
        collection = self.db.devices
        device_data = await collection.find_one({
            "name": name,
            "user_id": self.user_id,
            "deleted_at": None
        })
        
        if device_data:
            return Device(**device_data)
        return None
    
    async def get_devices(
        self, 
        skip: int = 0, 
        limit: int = 10,
        device_type: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[bool] = None
    ) -> Tuple[List[Device], int]:
        """Получение списка устройств с пагинацией и фильтрацией"""
        # Формируем ключ кеша
        cache_param = f"{skip}:{limit}:{device_type}:{location}:{status}"
        cache_key_hash = hashlib.md5(cache_param.encode()).hexdigest()
        
        # Пытаемся получить из кеша
        cached = cache_service.get("devices:list", self.user_id, cache_key_hash)
        
        if cached and isinstance(cached, dict) and "devices" in cached and "total" in cached:
            devices = [self._deserialize_device(device_data) for device_data in cached["devices"]]
            return devices, cached["total"]
        
        # Cache miss - запрос к MongoDB
        collection = self.db.devices
        
        # Строим фильтр
        filter_query = {
            "user_id": self.user_id,
            "deleted_at": None
        }
        
        if device_type:
            filter_query["device_type"] = device_type
        if location:
            filter_query["location"] = location
        if status is not None:
            filter_query["status"] = status
        
        # Получаем общее количество
        total = await collection.count_documents(filter_query)
        
        # Получаем устройства с пагинацией
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        devices_data = await cursor.to_list(length=limit)
        
        devices = [Device(**device_data) for device_data in devices_data]
        
        # Сохраняем в кеш
        cache_data = {
            "devices": [device.dict() for device in devices],
            "total": total
        }
        cache_service.set("devices:list", cache_data, 300, self.user_id, cache_key_hash)
        
        return devices, total
    
    async def create_device(self, device_data: DeviceCreate) -> Device:
        """Создание нового устройства"""
        collection = self.db.devices
        
        device_dict = device_data.model_dump()
        device_dict.update({
            "user_id": self.user_id,
            "created_at": datetime.utcnow(),
            "deleted_at": None
        })
        
        result = await collection.insert_one(device_dict)
        device_dict["_id"] = result.inserted_id
        
        device = Device(**device_dict)
        
        # Инвалидируем кеш списков
        await self._invalidate_list_cache()
        
        return device
    
    async def update_device(self, device_id: str, device_data: DeviceUpdate) -> Optional[Device]:
        """Частичное обновление устройства"""
        collection = self.db.devices
        
        update_data = device_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.update_one(
                {
                    "_id": ObjectId(device_id),
                    "user_id": self.user_id,
                    "deleted_at": None
                },
                {"$set": update_data}
            )
            
            if result.modified_count:
                # Инвалидируем кеш
                cache_service.delete("devices:item", self.user_id, device_id)
                await self._invalidate_list_cache()
                return await self.get_device(device_id)
        except Exception as e:
            print(f"Error updating device: {e}")
        
        return None
    
    async def update_device_full(self, device_id: str, device_data: DeviceCreate) -> Optional[Device]:
        """Полное обновление устройства"""
        collection = self.db.devices
        
        update_data = device_data.model_dump()
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.update_one(
                {
                    "_id": ObjectId(device_id),
                    "user_id": self.user_id,
                    "deleted_at": None
                },
                {"$set": update_data}
            )
            
            if result.modified_count:
                # Инвалидируем кеш
                cache_service.delete("devices:item", self.user_id, device_id)
                await self._invalidate_list_cache()
                return await self.get_device(device_id)
        except Exception as e:
            print(f"Error updating device: {e}")
        
        return None
    
    async def delete_device(self, device_id: str) -> bool:
        """Мягкое удаление устройства"""
        collection = self.db.devices
        
        try:
            result = await collection.update_one(
                {
                    "_id": ObjectId(device_id),
                    "user_id": self.user_id,
                    "deleted_at": None
                },
                {"$set": {"deleted_at": datetime.utcnow()}}
            )
            
            if result.modified_count:
                # Инвалидируем кеш
                cache_service.delete("devices:item", self.user_id, device_id)
                await self._invalidate_list_cache()
                return True
        except Exception as e:
            print(f"Error deleting device: {e}")
        
        return False
    
    async def _invalidate_list_cache(self):
        """Инвалидирует все кеши списков устройств пользователя"""
        cache_service.delete_pattern(f"devices:list:{self.user_id}:*")
    
    async def get_device_types(self) -> List[str]:
        """Получение всех типов устройств"""
        collection = self.db.devices
        types = await collection.distinct("device_type", {
            "user_id": self.user_id,
            "deleted_at": None
        })
        return types
    
    async def get_locations(self) -> List[str]:
        """Получение всех локаций"""
        collection = self.db.devices
        locations = await collection.distinct("location", {
            "user_id": self.user_id,
            "deleted_at": None
        })
        return locations