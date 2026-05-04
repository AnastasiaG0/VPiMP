from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.device_service import DeviceService
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, 
    DeviceListResponse
)

from app.auth.dependencies import get_current_user
from app.auth.models import User

# Создаем роутер для устройств
router = APIRouter()

@router.get(
    "/", 
    response_model=DeviceListResponse,
    summary="Получить список устройств",
    description="""
    Возвращает список активных устройств текущего пользователя с поддержкой пагинации и фильтрации.
    
    **Фильтры:**
    * device_type - тип устройства
    * location - расположение
    * status - статус (true/false)
    
    **Пагинация:**
    * page - номер страницы (начиная с 1)
    * limit - элементов на странице (макс. 100)
    """,
    responses={
        200: {
            "description": "Успешный ответ со списком устройств",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Гостиная лампа",
                                "device_type": "лампа",
                                "location": "Гостиная",
                                "status": True,
                                "value": 75,
                                "description": "LED лампа",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": None
                            }
                        ],
                        "meta": {
                            "total": 1,
                            "page": 1,
                            "limit": 10,
                            "total_pages": 1
                        }
                    }
                }
            }
        },
        401: {
            "description": "Не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        }
    }
)
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
        description="Фильтр по типу устройства",
        example="лампа"
    ),
    location: Optional[str] = Query(
        None, 
        description="Фильтр по расположению",
        example="Гостиная"
    ),
    status: Optional[bool] = Query(
        None, 
        description="Фильтр по статусу (true - вкл, false - выкл)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = DeviceService(db, current_user.id)
    
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


@router.get(
    "/{device_id}", 
    response_model=DeviceResponse,
    summary="Получить устройство по ID",
    description="Возвращает информацию об устройстве по его уникальному идентификатору.",
    responses={
        200: {
            "description": "Устройство найдено",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Гостиная лампа",
                        "device_type": "лампа",
                        "location": "Гостиная",
                        "status": True,
                        "value": 75,
                        "description": "LED лампа с регулировкой яркости",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": None
                    }
                }
            }
        },
        404: {
            "description": "Устройство не найдено",
            "content": {
                "application/json": {
                    "example": {"detail": "Device not found"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        }
    }
)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение устройства по ID."""
    service = DeviceService(db, current_user.id)
    device = service.get_device(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.post(
    "/", 
    response_model=DeviceResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать устройство",
    description="Создает новое устройство для текущего пользователя.",
    responses={
        201: {
            "description": "Устройство успешно создано",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Новая лампа",
                        "device_type": "лампа",
                        "location": "Кабинет",
                        "status": False,
                        "value": None,
                        "description": "Настольная лампа",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": None
                    }
                }
            }
        },
        409: {
            "description": "Устройство с таким именем уже существует",
            "content": {
                "application/json": {
                    "example": {"detail": "Device with name 'Новая лампа' already exists"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {"detail": "Validation error", "errors": []}
                }
            }
        }
    }
)
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание нового устройства."""
    service = DeviceService(db, current_user.id)

    # Проверка на дубликат
    existing = service.get_device_by_name(device_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with name '{device_data.name}' already exists"
        )

    device = service.create_device(device_data)
    return DeviceResponse.model_validate(device)


@router.put(
    "/{device_id}", 
    response_model=DeviceResponse,
    summary="Полное обновление устройства",
    description="Заменяет все поля устройства новыми значениями.",
    responses={
        200: {
            "description": "Устройство успешно обновлено",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Обновленная лампа",
                        "device_type": "лампа",
                        "location": "Гостиная",
                        "status": True,
                        "value": 100,
                        "description": "Обновленное описание",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-16T14:20:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Устройство не найдено",
            "content": {
                "application/json": {
                    "example": {"detail": "Device not found"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        }
    }
)
async def put_device(
    device_id: int,
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Полное обновление устройства """
    service = DeviceService(db, current_user.id)
    device = service.update_device_full(device_id, device_data)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.patch(
    "/{device_id}", 
    response_model=DeviceResponse,
    summary="Частичное обновление устройства",
    description="Обновляет только указанные поля устройства.",
    responses={
        200: {
            "description": "Устройство успешно обновлено",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Гостиная лампа",
                        "device_type": "лампа",
                        "location": "Гостиная",
                        "status": False,
                        "value": 50,
                        "description": "LED лампа",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-16T14:20:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Устройство не найдено",
            "content": {
                "application/json": {
                    "example": {"detail": "Device not found"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        }
    }
)
async def patch_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ Частичное обновление устройства """
    service = DeviceService(db, current_user.id)
    device = service.update_device(device_id, device_data)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.delete(
    "/{device_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить устройство",
    description="Мягкое удаление устройства (устройство помечается как удаленное, но остается в БД).",
    responses={
        204: {
            "description": "Устройство успешно удалено (нет содержимого ответа)"
        },
        404: {
            "description": "Устройство не найдено",
            "content": {
                "application/json": {
                    "example": {"detail": "Device not found"}
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        }
    }
)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Мягкое удаление устройства."""
    service = DeviceService(db, current_user.id)
    success = service.delete_device(device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )


@router.get(
    "/types/", 
    response_model=list[str],
    summary="Получить типы устройств",
    description="Возвращает список уникальных типов устройств текущего пользователя.",
    responses={
        200: {
            "description": "Список типов устройств",
            "content": {
                "application/json": {
                    "example": ["лампа", "термостат", "датчик движения", "розетка"]
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        }
    }
)
async def get_device_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение всех типов устройств.
    
    Возвращает список уникальных типов устройств.
    """
    service = DeviceService(db, current_user.id)
    return service.get_device_types()


@router.get(
    "/locations/", 
    response_model=list[str],
    summary="Получить локации",
    description="Возвращает список уникальных расположений устройств текущего пользователя.",
    responses={
        200: {
            "description": "Список локаций",
            "content": {
                "application/json": {
                    "example": ["Гостиная", "Спальня", "Кухня", "Кабинет"]
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        }
    }
)
async def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение всех локаций.
    
    Возвращает список уникальных расположений устройств.
    """
    service = DeviceService(db, current_user.id)
    return service.get_locations()