from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Tuple, List
from datetime import datetime

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceService:
    """
    Сервисный слой для работы с устройствами.
    Содержит бизнес-логику, независимую от HTTP.
    """
    
    def __init__(self, db: Session):
        """
        Инициализация сервиса с сессией базы данных.
        
        Args:
            db: Сессия SQLAlchemy для работы с БД
        """
        self.db = db
    
    def get_device(self, device_id: int) -> Optional[Device]:
        """
        Получение устройства по ID (только активные).
        
        Args:
            device_id: ID устройства
            
        Returns:
            Device или None, если устройство не найдено или удалено
        """
        return self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None)  # Исключение удаленных записей
        ).first()
    
    def get_device_by_name(self, name: str) -> Optional[Device]:
        """
        Получение устройства по имени (только активные).
        Используется для проверки дубликатов.
        
        Args:
            name: Название устройства
            
        Returns:
            Device или None, если устройство не найдено
        """
        return self.db.query(Device).filter(
            Device.name == name,
            Device.deleted_at.is_(None)
        ).first()
    
    def get_device_by_name_for_update(self, name: str, exclude_id: int) -> Optional[Device]:
        """
        Получение устройства по имени, исключая указанный ID.
        Используется для проверки дубликатов при обновлении.
        
        Args:
            name: Название устройства
            exclude_id: ID устройства, которое нужно исключить из проверки
            
        Returns:
            Device или None, если устройство не найдено
        """
        return self.db.query(Device).filter(
            Device.name == name,
            Device.id != exclude_id,
            Device.deleted_at.is_(None)
        ).first()
    
    def get_devices(
        self, 
        skip: int = 0, 
        limit: int = 10,
        device_type: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[bool] = None
    ) -> Tuple[List[Device], int]:
        """
        Получение списка устройств с пагинацией и фильтрацией.
        
        Args:
            skip: Количество пропускаемых записей (offset)
            limit: Максимальное количество записей
            device_type: Фильтр по типу устройства
            location: Фильтр по расположению
            status: Фильтр по статусу
            
        Returns:
            Кортеж (список устройств, общее количество)
        """
        # Базовый запрос - только активные устройства
        query = self.db.query(Device).filter(Device.deleted_at.is_(None))
        
        # Применяем фильтры, если они указаны
        if device_type:
            query = query.filter(Device.device_type == device_type)
        if location:
            query = query.filter(Device.location == location)
        if status is not None:
            query = query.filter(Device.status == status)
        
        # Получаем общее количество записей (для метаинформации)
        total = query.count()
        
        # Применяем пагинацию
        devices = query.offset(skip).limit(limit).all()
        
        return devices, total
    
    def create_device(self, device_data: DeviceCreate) -> Device:
        """
        Создание нового устройства.
        
        Args:
            device_data: Данные для создания устройства
            
        Returns:
            Созданное устройство
        """
        # Преобразуем DTO в модель
        device = Device(**device_data.model_dump())
        
        # Добавляем в БД
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)  # Обновляем объект с данными из БД
        
        return device
    
    def update_device(self, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
        """
        Частичное обновление устройства (PATCH).
        Обновляет только переданные поля.
        
        Args:
            device_id: ID устройства
            device_data: Данные для обновления (только переданные поля)
            
        Returns:
            Обновленное устройство или None, если не найдено
        """
        # Находим устройство
        device = self.get_device(device_id)
        if not device:
            return None
        
        # Обновляем только переданные поля
        update_data = device_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        
        # Сохраняем изменения
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    def update_device_full(self, device_id: int, device_data: DeviceCreate) -> Optional[Device]:
        """
        Полное обновление устройства (PUT).
        Обновляет все поля устройства.
        
        Args:
            device_id: ID устройства
            device_data: Полные данные для обновления
            
        Returns:
            Обновленное устройство или None, если не найдено
        """
        # Находим устройство
        device = self.get_device(device_id)
        if not device:
            return None
        
        # Обновляем ВСЕ поля
        device.name = device_data.name
        device.device_type = device_data.device_type
        device.location = device_data.location
        device.status = device_data.status
        device.value = device_data.value
        device.description = device_data.description
        
        # Сохраняем изменения
        self.db.commit()
        self.db.refresh(device)
        
        return device

    def delete_device(self, device_id: int) -> bool:
        """
        Мягкое удаление устройства.
        
        Args:
            device_id: ID устройства
            
        Returns:
            True если успешно, False если устройство не найдено
        """
        # Находим устройство
        device = self.get_device(device_id)
        if not device:
            return False
        
        # Устанавливаем время удаления (мягкое удаление)
        device.deleted_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def get_device_types(self) -> List[str]:
        """
        Получение всех типов устройств (только активные).
        
        Returns:
            Список уникальных типов устройств
        """
        types = self.db.query(Device.device_type).filter(
            Device.deleted_at.is_(None)
        ).distinct().all()
        return [t[0] for t in types]
    
    def get_locations(self) -> List[str]:
        """
        Получение всех локаций (только активные).
        
        Returns:
            Список уникальных локаций
        """
        locations = self.db.query(Device.location).filter(
            Device.deleted_at.is_(None)
        ).distinct().all()
        return [l[0] for l in locations]
    
    def get_deleted_devices(self, skip: int = 0, limit: int = 10) -> Tuple[List[Device], int]:
        """
        Получение списка удаленных устройств (для административных целей).
        
        Args:
            skip: Количество пропускаемых записей
            limit: Максимальное количество записей
            
        Returns:
            Кортеж (список удаленных устройств, общее количество)
        """
        query = self.db.query(Device).filter(Device.deleted_at.is_not(None))
        total = query.count()
        devices = query.offset(skip).limit(limit).all()
        return devices, total
    
    def restore_device(self, device_id: int) -> Optional[Device]:
        """
        Восстановление мягко удаленного устройства.
        
        Args:
            device_id: ID устройства
            
        Returns:
            Восстановленное устройство или None, если не найдено
        """
        # Находим удаленное устройство
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_not(None)
        ).first()
        
        if not device:
            return None
        
        # Восстанавливаем (убираем отметку об удалении)
        device.deleted_at = None
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    def hard_delete_device(self, device_id: int) -> bool:
        """
        Физическое удаление устройства из БД (Hard Delete).
        Используется только для административных целей.
        
        Args:
            device_id: ID устройства
            
        Returns:
            True если успешно, False если устройство не найдено
        """
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return False
        
        self.db.delete(device)
        self.db.commit()
        
        return True