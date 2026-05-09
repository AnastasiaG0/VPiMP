from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Tuple, List
from datetime import datetime
import hashlib
import json
import redis

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.cache import cache_service
from app.core.config import settings


class DeviceService:
    # Инициализация сервиса с сессией бд
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def _serialize_device(self, device: Device) -> dict:
        """Сериализует объект Device в словарь для кеширования"""
        return {
            "id": device.id,
            "user_id": device.user_id,
            "name": device.name,
            "device_type": device.device_type,
            "location": device.location,
            "status": device.status,
            "value": device.value,
            "description": device.description,
            "created_at": device.created_at.isoformat() if device.created_at else None,
            "updated_at": device.updated_at.isoformat() if device.updated_at else None,
            "deleted_at": device.deleted_at.isoformat() if device.deleted_at else None,
        }
    
    def _deserialize_device(self, data: dict) -> Device:
        """Восстанавливает объект Device из словаря"""
        # Создаём объект Device без привязки к сессии
        device = Device()
        for key, value in data.items():
            if value is not None and key in ["created_at", "updated_at", "deleted_at"]:
                # Преобразуем ISO строки обратно в datetime
                from datetime import datetime
                setattr(device, key, datetime.fromisoformat(value))
            else:
                setattr(device, key, value)
        return device

    def _get_list_cache_key(self, skip: int = 0, limit: int = 10,
                            device_type: Optional[str] = None,
                            location: Optional[str] = None,
                            status: Optional[bool] = None) -> str:
        """Формирует ключ кеша для списка устройств"""
        # Создаём уникальный ключ на основе всех параметров
        params = f"{skip}:{limit}:{device_type}:{location}:{status}"
        return f"devices:list:{self.user_id}:{hashlib.md5(params.encode()).hexdigest()}"
    
    '''def _get_item_cache_key(self, device_id: int) -> str:
        """Формирует ключ кеша для конкретного устройства"""
        return f"devices:item:{self.user_id}:{device_id}"'''
    
    def _invalidate_list_cache(self):
        """Инвалидирует все кеши списков устройств пользователя"""
        cache_service.delete_pattern(f"devices:list:{self.user_id}:*")

    # Получение устройства текущего пользователя по ID 
    def get_device(self, device_id: int) -> Optional[Device]:
        # Пытаемся получить из кеша
        #cache_key = self._get_item_cache_key(device_id)
        cached = cache_service.get("devices:item", self.user_id, device_id)
        
        if cached:
            # Восстанавливаем объект Device из словаря
            return self._deserialize_device(cached)
        
        # Cache miss - запрос к БД
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == self.user_id,
            Device.deleted_at.is_(None)
        ).first()
        
        # Сохраняем в кеш
        if device:
            cache_service.set("devices:item", self._serialize_device(device), 300, self.user_id, device_id)
        
        return device
    
    # Получение устройства текущего пользователя по имени
    def get_device_by_name(self, name: str) -> Optional[Device]:
        return self.db.query(Device).filter(
            Device.name == name,
            Device.user_id == self.user_id,
            Device.deleted_at.is_(None)
        ).first()
    
    # Получение списка устройств с пагинацией и фильтрацией
    def get_devices(
        self, 
        skip: int = 0, 
        limit: int = 10,
        device_type: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[bool] = None
    ) -> Tuple[List[Device], int]:
        # Формируем параметры для ключа кеша
        cache_param = f"{skip}:{limit}:{device_type}:{location}:{status}"
        cache_key_hash = hashlib.md5(cache_param.encode()).hexdigest()
        
        # Пытаемся получить из кеша
        cached = cache_service.get("devices:list", self.user_id, cache_key_hash)
        
        if cached and isinstance(cached, dict) and "devices" in cached and "total" in cached:
            # Восстанавливаем объекты Device из словарей
            devices = [self._deserialize_device(device_data) for device_data in cached["devices"]]
            return devices, cached["total"]
        
        # Cache miss - запрос к БД
        query = self.db.query(Device).filter(
            Device.user_id == self.user_id,
            Device.deleted_at.is_(None)
        )
        
        # Применяем фильтры, если указаны
        if device_type:
            query = query.filter(Device.device_type == device_type)
        if location:
            query = query.filter(Device.location == location)
        if status is not None:
            query = query.filter(Device.status == status)
        
        total = query.count()
        devices = query.offset(skip).limit(limit).all()
        
        # Сохраняем в кеш (сериализуем объекты)
        cache_data = {
            "devices": [self._serialize_device(device) for device in devices],
            "total": total
        }
        cache_service.set("devices:list", cache_data, 300, self.user_id, cache_key_hash)
        
        return devices, total
    
    # Создание нового устройства
    def create_device(self, device_data: DeviceCreate) -> Device:
        # Преобразуем DTO в модель и привязываем устройство к текущему пользователю
        device = Device(
            **device_data.model_dump(),
            user_id=self.user_id
        )
        
        # Добавляем в БД
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)  # Обновляем объект с данными из БД

        # Инвалидируем кеш списков
        if cache_service.is_available():
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # Удаляем все ключи с устройствами этого пользователя
            pattern = f"smart_home:devices:list:{self.user_id}:*"
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
        
        return device
    
    # Частичное обновление устройства
    def update_device(self, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
        device = self.get_device(device_id)
        if not device:
            return None
        
        # Обновляем переданные поля
        update_data = device_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        
        self.db.commit()
        self.db.refresh(device)
        
        # Инвалидируем кеш
        cache_service.delete("devices:item", self.user_id, device_id)
        self._invalidate_list_cache()

        return device
    
    # Полное обновление устройства
    def update_device_full(self, device_id: int, device_data: DeviceCreate) -> Optional[Device]:
        device = self.get_device(device_id)
        if not device:
            return None
        
        device.name = device_data.name
        device.device_type = device_data.device_type
        device.location = device_data.location
        device.status = device_data.status
        device.value = device_data.value
        device.description = device_data.description
        
        self.db.commit()
        self.db.refresh(device)
        
        # Инвалидируем кеш
        cache_service.delete("devices:item", self.user_id, device_id)
        self._invalidate_list_cache()

        return device

    # Мягкое удаление устройства
    def delete_device(self, device_id: int) -> bool:
        device = self.get_device(device_id)
        if not device:
            return False
        
        # Устанавливаем время удаления
        device.deleted_at = datetime.utcnow()
        self.db.commit()

        # Инвалидируем кеш
        cache_service.delete("devices:item", self.user_id, device_id)
        self._invalidate_list_cache()
        
        return True
    
    def _invalidate_list_cache(self):
        """Инвалидирует все кеши списков устройств пользователя"""
        cache_service.delete_pattern(f"devices:list:{self.user_id}:*")

    # Получение всех типов устройств текущего пользователя
    def get_device_types(self) -> List[str]:
        types = self.db.query(Device.device_type).filter(
            Device.user_id == self.user_id,
            Device.deleted_at.is_(None)
        ).distinct().all()
        return [t[0] for t in types]
    
    # Получение всех локаций устройств текущего пользователя
    def get_locations(self) -> List[str]:
        locations = self.db.query(Device.location).filter(
            Device.user_id == self.user_id,
            Device.deleted_at.is_(None)
        ).distinct().all()
        return [l[0] for l in locations]