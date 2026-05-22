# Лабораторная работа №6

## Знакомство с MongoDB. Сравнение реляционных и документоориентированных СУБД

## Описание проекта

API для управления устройствами умного дома, переписанное с PostgreSQL на MongoDB. Проект демонстрирует миграцию с реляционной базы данных на документоориентированную с сохранением всей функциональности. Поддерживает аутентификацию JWT, OAuth через Яндекс ID, кеширование через Redis и мягкое удаление.

## Технологии

- FastAPI - веб-фреймворк
- MongoDB - документоориентированная СУБД
- Motor - асинхронный драйвер MongoDB
- Redis - кеширование и хранение сессий
- JWT - аутентификация
- Docker - контейнеризация
- Swagger UI - автоматическая документация API

## Требования

- Docker и Docker Compose
- cURL / Postman / Insomia
- Настроенное окружение для работы с выбранным языком программирования (интерпретатор, компилятор, менеджер зависимостей, при необходимости)
- Наличие клиента для работы с MongoDB (например, MongoDB Compas или CLI)

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
DB_PORT=27017

MONGO_URI=mongodb://student:student_secure_password@mongodb:27017/smart_home?authSource=admin

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

| Метод  | URI                           | Описание                                        | Статус успеха  | Доступ                                  |
| :----- | :---------------------------- | :---------------------------------------------- | :------------- | :-------------------------------------- |
| POST   | `/auth/register`              | Регистрация нового пользователя                 | 201 Created    | Public                                  |
| POST   | `/auth/login`                 | Вход (установка cookies)                        | 200 OK         | Public                                  |
| POST   | `/auth/refresh`               | Обновление пары токенов                         | 200 OK         | Public (требуется valid Refresh Cookie) |
| GET    | `/auth/whoami`                | Проверка статуса и данные пользователя          | 200 OK         | Private                                 |
| POST   | `/auth/logout`                | Завершение текущей сессии                       | 200 OK         | Private                                 |
| POST   | `/auth/logout-all`            | Завершение всех сессий пользователя             | 200 OK         | Private                                 |
| GET    | `/auth/oauth/yandex`          | Инициация входа через Yandex ID                 | 302 Redirect   | Public                                  |
| GET    | `/auth/oauth/yandex/callback` | Обработка ответа от Yandex                      | 302 Redirect   | Public                                  |
| POST   | `/auth/forgot-password`       | Запрос на сброс пароля                          | 200 OK         | Public                                  |
| POST   | `/auth/reset-password`        | Установка нового пароля                         | 200 OK         | Public                                  |
| GET    | `/api/v1/devices`             | Получить список устройств (с пагинацией)        | 200 OK         | Private                                 |
| GET    | `/api/v1/devices/{id}`        | Получить устройство по ID                       | 200 OK         | Private                                 |
| POST   | `/api/v1/devices`             | Создать устройство                              | 201 Created    | Private                                 |
| PUT    | `/api/v1/devices/{id}`        | Полное обновление устройства                    | 200 OK         | Private                                 |
| PATCH  | `/api/v1/devices/{id}`        | Частичное обновление устройства                 | 200 OK         | Private                                 |
| DELETE | `/api/v1/devices/{id}`        | Пометить устройство как удаленное (Soft Delete) | 204 No Content | Private                                 |
| GET    | `/api/v1/devices/types/`      | Получить список всех типов устройств            | 200 OK         | Private                                 |
| GET    | `/api/v1/devices/locations/`  | Получить список всех локаций устройств          | 200 OK         | Private                                 |

### Структура ключей Redis

| Тип данных            | Формат ключа                                  | TTL     |
| :-------------------- | :-------------------------------------------- | :------ |
| Список устройств      | smart_home:devices:list:{user_id}:{hash}      | 300 сек |
| Конкретное устройство | smart_home:devices:item:{user_id}:{device_id} | 300 сек |
| Профиль пользователя  | smart_home:user:profile:{user_id}             | 300 сек |
| JTI токен (сессия)    | smart_home:auth:access:{user_id}:{jti}        | 900 сек |

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
GET smart_home:devices:list:id:xxx
GET "smart_home:user:profile:id"
```

Проверка времени жизни ключа (TTL):

```bash
TTL smart_home:devices:list:id:xxx
TTL "smart_home:user:profile:id"
TTL "smart_home:auth:access:id:xxx"
```

Удаление ключа (ручная инвалидация):

```bash
DEL smart_home:devices:list:id:xxx
```

Удаление по паттерну (массовая инвалидация):

```bash
UNLINK smart_home:devices:list:id:*
```

Очистка всей базы (для тестов):

```bash
FLUSHDB
```

### Примеры запросов (cURL)

1. Регистрация пользователя

```bash
curl -X POST http://localhost:4200/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","password":"secret123","full_name":"User One"}'
```

2. Регистрация второго пользователя (с таким же паролем для проверки соли)

```bash
curl -X POST http://localhost:4200/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user2@example.com","password":"secret123","full_name":"User Two"}'
```

3.  Вход пользователя

```bash
curl -X POST http://localhost:4200/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","password":"secret123"}' \
  -c cookies_user1.txt
```

4. Проверка статуса и данных пользователя

```bash
curl -X GET http://localhost:4200/auth/whoami -b cookies_user1.txt
```

5. Создание устройства

```bash
curl -X POST http://localhost:4200/api/v1/devices \
  -H "Content-Type: application/json" \
  -b cookies_user1.txt \
  -d '{"name":"Living Room Lamp","device_type":"lamp","location":"Living Room","status":true,"value":75,"description":"Smart LED lamp"}'
```

6. Получение списка всех устройств с пагинацией

```bash
curl -X GET "http://localhost:4200/api/v1/devices?page=1&limit=10" -b cookies_user1.txt
```
