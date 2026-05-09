# Лабораторная работа №4
## Автоматизированное документирование REST API с использованием OpenAPI (Swagger)

## Описание проекта
API для управления устройствами умного дома с поддержкой аутентификации (JWT + OAuth Яндекс).

## Технологии
- FastAPI - веб-фреймворк
- PostgreSQL 16 - реляционная СУБД
- SQLAlchemy - ORM для работы с БД
- Alembic - инструмент для миграций
- Docker / Docker Compose - контейнеризация
- JWT - токены доступа
- OAuth 2.0 - вход через Yandex ID
- OpenAPI/Swagger - автоматическая документация API

## Требования
- Docker и Docker Compose
- Git
- Настроенное окружение из Лабораторной работы №3 (приложение с авторизацией, CRUD ресурсами, Docker).

## Настройка переменных окружения
Скопируйте `.env.example` в `.env` и настройте переменные:
```bash
cp .env.example .env
```

### Пример файла переменных окружения:
```bash
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=postgres
DB_PORT=5432

APP_HOST=0.0.0.0
APP_PORT=4200
APP_ENV=development   # или production

JWT_ACCESS_SECRET=change_me_super_secret_access_key
JWT_REFRESH_SECRET=change_me_super_secret_refresh_key
JWT_ACCESS_EXPIRATION=15
JWT_REFRESH_EXPIRATION=10080

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:4200/auth/oauth/yandex/callback
```

## Запуск
### Development режим (с документацией)
Запустите приложение:
```bash
docker-compose up --build
```

Документация доступна по адресу:
http://localhost:4200/api/docs

### Production режим (без документации)
В файле .env измените строку:
```bash
APP_ENV=development
```

на:
```bash
APP_ENV=production
```

Запустите приложение:
```bash
docker-compose -f docker-compose.prod.yaml up --build
```

Проверьте ответ API:
http://localhost:4200/
Ожидаемый ответ:
```bash
{
    "message": "Smart Home API",
    "version": "2.0.0",
    "docs": "/api/docs"
}
```

Проверьте состояние сервера, перейдя по ссылке:
http://localhost:4200/health
Ожидаемый ответ:
```bash
{
    "status":"healthy"
}
```

Проверьте доступ к документации, перейдя по ссылке:
http://localhost:4200/api/docs
Ожидаемый ответ:
```bash
{
    "detail":"Not Found"
}
```

## API Эндпоинты
### Аутентификация
| Метод | URI | Описание | Доступ |
| :--- | :--- | :--- | :--- |
| POST | `/auth/register` | Регистрация нового пользователя | Public |
| POST | `/auth/login` | Вход (установка cookies) | Public |
| POST | `/auth/refresh` | Обновление пары токенов | Public (требуется valid Refresh Cookie) |
| GET | `/auth/whoami` | Проверка статуса и данные пользователя | Private |
| POST | `/auth/logout` | Завершение текущей сессии | Private |
| POST | `/auth/logout-all` | Завершение всех сессий пользователя | Private |
| GET | `/auth/oauth/yandex` | Инициация входа через Yandex ID | Public |
| GET | `/auth/oauth/yandex/callback` | Обработка ответа от Yandex | Public |
| POST | `/auth/forgot-password` | Запрос на сброс пароля | Public |
| POST | `/auth/reset-password` | Установка нового пароля | Public |

### Устройства
| Метод | URI | Описание | Доступ |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/devices` | Получить список устройств (с пагинацией) | Private |
| GET | `/api/v1/devices/{id}` | Получить устройство по ID | Private |
| POST | `/api/v1/devices` | Создать устройство | Private |
| PUT | `/api/v1/devices/{id}` | Полное обновление устройства | Private |
| PATCH | `/api/v1/devices/{id}` | Частичное обновление устройства | Private |
| DELETE | `/api/v1/devices/{id}` | Пометить устройство как удаленное (Soft Delete) | Private |
| GET | `/api/v1/devices/types/` | Получить список всех типов устройств | Private |
| GET | `/api/v1/devices/locations/` | Получить список всех локаций устройств | Private |