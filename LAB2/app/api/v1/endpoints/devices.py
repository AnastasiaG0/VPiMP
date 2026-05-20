from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.device_service import DeviceService
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, 
    DeviceListResponse
)

# Создаем роутер для устройств
router = APIRouter()


@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    # Параметры пагинации
    page: int = Query(
        1, 
        ge=1, 
        description="Номер страницы (начиная с 1)"
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=100, 
        description="Количество элементов на странице (от 1 до 100)"
    ),
    # Параметры фильтрации
    device_type: Optional[str] = Query(
        None, 
        description="Фильтр по типу устройства"
    ),
    location: Optional[str] = Query(
        None, 
        description="Фильтр по расположению"
    ),
    status: Optional[bool] = Query(
        None, 
        description="Фильтр по статусу (true - вкл, false - выкл)"
    ),
    db: Session = Depends(get_db)
):
    """
    Получение списка активных устройств с пагинацией и фильтрацией.
    
    - **page**: номер страницы (по умолчанию 1)
    - **limit**: количество элементов на странице (по умолчанию 10, максимум 100)
    - **device_type**: фильтр по типу устройства
    - **location**: фильтр по расположению
    - **status**: фильтр по статусу
    
    Возвращает список устройств и метаинформацию о пагинации.
    """
    service = DeviceService(db)
    
    # Вычисляем offset для SQL запроса
    skip = (page - 1) * limit
    
    # Получаем устройства и общее количество
    devices, total = service.get_devices(
        skip=skip,
        limit=limit,
        device_type=device_type,
        location=location,
        status=status
    )
    
    # Вычисляем общее количество страниц
    total_pages = (total + limit - 1) // limit
    
    # Возвращаем ответ с данными и метаинформацией
    return DeviceListResponse(
        data=[DeviceResponse.model_validate(device) for device in devices],
        meta={
            "total": total,           # Всего записей
            "page": page,             # Текущая страница
            "limit": limit,           # Элементов на странице
            "total_pages": total_pages  # Всего страниц
        }
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение устройства по ID.
    
    - **device_id**: уникальный идентификатор устройства
    
    Возвращает устройство, если оно существует и не удалено.
    """
    service = DeviceService(db)
    device = service.get_device(device_id)
    
    if not device:
        # Если устройство не найдено, возвращаем 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.post(
    "/", 
    response_model=DeviceResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db)
):
    """
    Создание нового устройства.
    
    - **device_data**: данные нового устройства
    
    Возвращает созданное устройство с присвоенным ID.
    """
    service = DeviceService(db)

    # Проверка на дубликат
    existing = service.get_device_by_name(device_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with name '{device_data.name}' already exists"
        )

    device = service.create_device(device_data)
    return DeviceResponse.model_validate(device)


@router.put("/{device_id}", response_model=DeviceResponse)
async def put_device(
    device_id: int,
    device_data: DeviceCreate,
    db: Session = Depends(get_db)
):
    """ Полное обновление устройства """
    service = DeviceService(db)
    device = service.update_device_full(device_id, device_data)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceResponse)
async def patch_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """ Частичное обновление устройства """
    service = DeviceService(db)
    device = service.update_device(device_id, device_data)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Мягкое удаление устройства.
    
    - **device_id**: ID устройства для удаления
    
    Устройство не удаляется физически, а помечается как удаленное.
    """
    service = DeviceService(db)
    success = service.delete_device(device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )


@router.get("/types/", response_model=list[str])
async def get_device_types(
    db: Session = Depends(get_db)
):
    """
    Получение всех типов устройств.
    
    Возвращает список уникальных типов устройств.
    """
    service = DeviceService(db)
    return service.get_device_types()


@router.get("/locations/", response_model=list[str])
async def get_locations(
    db: Session = Depends(get_db)
):
    """
    Получение всех локаций.
    
    Возвращает список уникальных расположений устройств.
    """
    service = DeviceService(db)
    return service.get_locations()