# Лабораторная работа №5
## Кеширование данных и управление сессиями с использованием Redis

## Описание проекта
Данная работа является продолжением лабораторных работ №2 (CRUD устройства умного дома) и №3 (Аутентификация и OAuth 2.0). В рамках лабораторной работы №5 в приложение добавлен слой кеширования на базе Redis для кеширования списков устройств с автоматической инвалидацией, кеширования профилей пользователей, хранения JTI (JWT ID) токенов для мгновенного отзыва сессий и оптимизации производительности API.

## Технологии
- FastAPI - веб-фреймворк
- PostgreSQL 16 - реляционная СУБД
- SQLAlchemy - ORM для работы с БД
- Alembic - инструмент для миграций
- Docker / Docker Compose - контейнеризация
- JWT - токены доступа
- OAuth 2.0 - вход через Yandex ID
- OpenAPI/Swagger - автоматическая документация API
- Redis - кэширование

## Требования
- Docker и Docker Compose
- cURL / Postman / Insomia
- Настроенное окружение для работы с выбранным языком программирования (интерпретатор, компилятор, менеджер зависимостей, при необходимости)

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
APP_ENV=development

JWT_ACCESS_SECRET=super_secret_access_key
JWT_REFRESH_SECRET=super_secret_refresh_key
JWT_ACCESS_EXPIRATION=15
JWT_REFRESH_EXPIRATION=10080

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:4200/auth/oauth/yandex/callback

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password
REDIS_DB=0
CACHE_TTL_DEFAULT=300
```

### API Эндпоинты
| Метод | URI | Описание | Статус успеха | Доступ |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/auth/register` | Регистрация нового пользователя | 201 Created | Public |
| POST | `/auth/login` | Вход (установка cookies) | 200 OK | Public |
| POST | `/auth/refresh` | Обновление пары токенов | 200 OK | Public (требуется valid Refresh Cookie) |
| GET | `/auth/whoami` | Проверка статуса и данные пользователя | 200 OK | Private |
| POST | `/auth/logout` | Завершение текущей сессии | 200 OK | Private |
| POST | `/auth/logout-all` | Завершение всех сессий пользователя | 200 OK | Private |
| GET | `/auth/oauth/yandex` | Инициация входа через Yandex ID | 302 Redirect | Public |
| GET | `/auth/oauth/yandex/callback` | Обработка ответа от Yandex | 302 Redirect | Public |
| POST | `/auth/forgot-password` | Запрос на сброс пароля | 200 OK | Public |
| POST | `/auth/reset-password` | Установка нового пароля | 200 OK | Public |
| GET | `/api/v1/devices` | Получить список устройств (с пагинацией) | 200 OK | Private |
| GET | `/api/v1/devices/{id}` | Получить устройство по ID | 200 OK | Private |
| POST | `/api/v1/devices` | Создать устройство | 201 Created | Private |
| PUT | `/api/v1/devices/{id}` | Полное обновление устройства | 200 OK | Private |
| PATCH | `/api/v1/devices/{id}` | Частичное обновление устройства | 200 OK | Private |
| DELETE | `/api/v1/devices/{id}` | Пометить устройство как удаленное (Soft Delete) | 204 No Content | Private |
| GET | `/api/v1/devices/types/` | Получить список всех типов устройств | 200 OK | Private |
| GET | `/api/v1/devices/locations/` | Получить список всех локаций устройств | 200 OK | Private |


### Структура ключей Redis
| Тип данных | Формат ключа | TTL |
| :--- | :--- | :--- |
| Список устройств | smart_home:devices:list:{user_id}:{hash} | 300 сек |
| Конкретное устройство	| smart_home:devices:item:{user_id}:{device_id} | 300 сек |
| Профиль пользователя | smart_home:user:profile:{user_id} | 300 сек |
| JTI токен (сессия) | smart_home:auth:access:{user_id}:{jti} | 900 сек |


### Работа с Redis CLI
Подключение к Redis:
```bash
docker exec -it smart_home_redis redis-cli -a redis_secure_password
```

Просмотр ключей по паттерну:
```bash
KEYS 'smart_home:*'
KEYS smart_home:devices:*
```

Получение значений ключа:
```bash
GET smart_home:devices:list:1:xxx
GET "smart_home:user:profile:1"
```

Проверка времени жизни ключа (TTL):
```bash
TTL smart_home:devices:list:1:xxx
TTL "smart_home:user:profile:1"
TTL "smart_home:auth:access:1:xxx"
```

Удаление ключа (ручная инвалидация):
```bash
DEL smart_home:devices:list:1:xxx
```

Удаление по паттерну (массовая инвалидация):
```bash
UNLINK smart_home:devices:list:1:* 
```

Очистка всей базы (для тестов):
```bash
FLUSHDB
```

## Тестирование
1. После запуска приложения подключимся к Redis и проверим, что он работает
2. Зарегистрируем пользователя и войдём в систему
3. Создадим устройство и выведем список устройств пользователя
4. Подключимся к Redis и проверим ключи и TTL
5. Создадим новое устройство и проверим Redis. Старый ключ списка должен исчезнуть
6. Сделаем запрос на получения списка устройств и проверим кэш. Должен появиться ключ списка
7. Выйдем из системы при помощи logout. Должен исчезнуть JTI ключ