# Лабораторная работа №2
## Проектирование и реализация RESTful API

## Описание проекта
RESTful API для управления устройствами умного дома. Реализован полный CRUD с мягким удалением и пагинацией.

## Технологии
- FastAPI - веб-фреймворк
- PostgreSQL 16 - реляционная СУБД
- SQLAlchemy - ORM для работы с БД
- Alembic - инструмент для миграций
- Docker / Docker Compose - контейнеризация

## Требования
- Docker и Docker Compose
- Git

## Установка и запуск

Скопируйте `.env.example` в `.env` и настройте переменные:
```bash
cp .env.example .env
```

Запустите приложение:
```bash
docker-compose up --build
```

Создайте новый терминал и проверьте, что контейнеры работают:
```bash
docker ps
```

В конце работы с приложением остановите контейнеры:
```bash
docker-compose stop
```

Для остановки и удаления контейнеров используйте команду:
```bash
docker-compose down
```

Чтобы остановить и удалить контейнеры вместе с томами, используйте команду:
```bash
docker-compose down -v
```

### API Эндпоинты
| Метод | URI | Описание | Статус успеха |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/devices/` | Получить список устройств (с пагинацией) | `200 OK` |
| `GET` | `/api/v1/devices/{id}` | Получить устройство по ID | `200 OK` |
| `POST` | `/api/v1/devices/` | Создать устройство | `201 Created` |
| `PUT` | `/api/v1/devices/{id}` | Полное обновление устройства | `200 OK` |
| `PATCH` | `/api/v1/devices/{id}` | Частичное обновление устройства | `200 OK` |
| `DELETE` | `/api/v1/devices/{id}` | Пометить устройство как удаленное (Soft Delete) | `204 No Content` |
| `GET` | `/api/v1/devices/types/` | Получить список всех типов устройств | `200 OK` |
| `GET` | `/api/v1/devices/locations/` | Получить список всех локаций устройств | `200 OK` |
| `GET` | `/health` | Проверить здоровье | `200 OK` |

### Пагинация
Параметры для списка всех устройств:
```bash
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 10,
    "total_pages": 10
  }
}
```

### Миграции
Для создания миграции войдите в контейнер приложения:
```bash
docker exec -it smart_home_app bash
```

Создайте миграцию:
```bash
alembic revision --autogenerate -m "Add devices table"
```

Примените миграцию:
```bash
alembic upgrade head
```

Для выхода из контейнера используйте:
```bash
exit
```

Проверьте, что таблица создана:
```bash
docker exec -it smart_home_db psql -U student -d smart_home -c "\dt"
```

### Переменные окружения
Пример файла переменных окружения:
```bash
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=postgres
DB_PORT=5432
APP_HOST=0.0.0.0
APP_PORT=4200
```

### Примеры запросов (cURL)
1. Создание устройства
```bash
curl.exe -X POST http://localhost:4200/api/v1/devices/ -H "Content-Type: application/json" -d '{"name": "Smart lamp", "device_type": "light", "location": "Living room", "status": true, "value": 75}'
```

2.  Получить список всех устройств с пагинацией
```bash
curl.exe -X GET "http://localhost:4200/api/v1/devices/?page=1&limit=10"
```

3. Получить устройство по ID
```bash
curl.exe -X GET http://localhost:4200/api/v1/devices/1
```

4. Частичное обновление - выключить лампу
```bash
curl.exe -X PATCH http://localhost:4200/api/v1/devices/1 -H "Content-Type: application/json" -d '{"status": false, "value": 0}'
```

5. Полное обновление
```bash
curl.exe -X PUT http://localhost:4200/api/v1/devices/1 -H "Content-Type: application/json" -d '{"name": "New Smart Lamp", "device_type": "light", "location": "Kitchen", "status": true, "value": 100, "description": "Updated lamp"}'
```

6. Получить список всех типов устройств
```bash
curl.exe -X GET http://localhost:4200/api/v1/devices/types/
```

7. Получить список всех локаций
```bash
curl.exe -X GET http://localhost:4200/api/v1/devices/locations/
```

8. Мягкое удаление устройства
```bash
curl.exe -X DELETE http://localhost:4200/api/v1/devices/1
```

9. Проверить, что устройство не найдено (должен быть 404)
```bash
curl.exe -X GET http://localhost:4200/api/v1/devices/1
```

10. Проверить, что удаленное устройство не отображается в списке
```bash
curl.exe -X GET "http://localhost:4200/api/v1/devices/?page=1&limit=10"
```

11. Проверить, что устройство не было удалено физически:
```bash
docker exec -it smart_home_db psql -U student -d smart_home -c "SELECT id, name, deleted_at FROM devices WHERE deleted_at IS NOT NULL;"
```