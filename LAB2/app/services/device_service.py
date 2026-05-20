from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Tuple, List
from datetime import datetime

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceService:
    # Инициализация сервиса с сессией бд
    def __init__(self, db: Session):
        self.db = db
    
    # Получение устройства по ID
    def get_device(self, device_id: int) -> Optional[Device]:
        return self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None)
        ).first()
    
    # Получение устройства по имени
    def get_device_by_name(self, name: str) -> Optional[Device]:
        return self.db.query(Device).filter(
            Device.name == name,
            Device.deleted_at.is_(None)
        ).first()
    
    """# Получение устройства по имени для обновления
    def get_device_by_name_for_update(self, name: str, exclude_id: int) -> Optional[Device]:
        
        return self.db.query(Device).filter(
            Device.name == name,
            Device.id != exclude_id,
            Device.deleted_at.is_(None)
        ).first()"""
    
    # Получение списка устройств с пагинацией и фильтрацией
    def get_devices(
        self, 
        skip: int = 0, 
        limit: int = 10,
        device_type: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[bool] = None
    ) -> Tuple[List[Device], int]:
  
        # Только активные устройства
        query = self.db.query(Device).filter(Device.deleted_at.is_(None))
        
        # Применяем фильтры, если указаны
        if device_type:
            query = query.filter(Device.device_type == device_type)
        if location:
            query = query.filter(Device.location == location)
        if status is not None:
            query = query.filter(Device.status == status)
        
        # Общее количество записей
        total = query.count()
        
        # Применяем пагинацию
        devices = query.offset(skip).limit(limit).all()
        
        return devices, total
    
    # Создание нового устройства
    def create_device(self, device_data: DeviceCreate) -> Device:
        # Преобразуем DTO в модель
        device = Device(**device_data.model_dump())
        
        # Добавляем в БД
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)  # Обновляем объект с данными из БД
        
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
        
        return device

    # Мягкое удаление устройства
    def delete_device(self, device_id: int) -> bool:
        device = self.get_device(device_id)
        if not device:
            return False
        
        # Устанавливаем время удаления
        device.deleted_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    # Получение всех типов устройств
    def get_device_types(self) -> List[str]:
        types = self.db.query(Device.device_type).filter(
            Device.deleted_at.is_(None)
        ).distinct().all()
        return [t[0] for t in types]
    
    # Получение всех локаций устройств
    def get_locations(self) -> List[str]:
        locations = self.db.query(Device.location).filter(
            Device.deleted_at.is_(None)
        ).distinct().all()
        return [l[0] for l in locations]
    
    '''
    # Получение списка удаленных устройств
    def get_deleted_devices(self, skip: int = 0, limit: int = 10) -> Tuple[List[Device], int]:
        query = self.db.query(Device).filter(Device.deleted_at.is_not(None))
        total = query.count()
        devices = query.offset(skip).limit(limit).all()
        return devices, total
    
    # Восстановление мягко удаленного устройства
    def restore_device(self, device_id: int) -> Optional[Device]:
        # Находим удаленное устройство
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_not(None)
        ).first()
        
        if not device:
            return None
        
        device.deleted_at = None
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    # Физическое удаление устройства из бд
    def hard_delete_device(self, device_id: int) -> bool:
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return False
        
        self.db.delete(device)
        self.db.commit()
        
        return True'''