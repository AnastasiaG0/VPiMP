# Лабораторная работа №3
## Авторизация и аутентификация (JWT, OAuth2, Cookies)

## Описание проекта
API для управления устройствами умного дома с полноценной системой аутентификации и авторизации.

### Основной функционал

**Управление устройствами (из ЛР2):**
- CRUD операции для устройств
- Пагинация и фильтрация
- Soft Delete (мягкое удаление)

**Система аутентификации (ЛР3):**
- Регистрация и вход пользователей
- JWT токены (Access и Refresh)
- HttpOnly cookies для безопасной передачи токенов
- Хеширование паролей с уникальной солью
- OAuth 2.0 (Yandex ID)
- Управление сессиями (logout, logout-all)
- Сброс пароля

## Технологии
- FastAPI - веб-фреймворк
- PostgreSQL 16 - реляционная СУБД
- SQLAlchemy - ORM для работы с БД
- Alembic - инструмент для миграций
- Docker / Docker Compose - контейнеризация
- JWT - токены доступа
- OAuth 2.0 - вход через Yandex ID

## Требования
- Docker и Docker Compose
- Git
- Аккаунт разработчика в системе OAuth-провайдера Yandex ID для получения ключа доступа

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

### Миграции
Создайте миграцию:
```bash
docker exec smart_home_app alembic revision --autogenerate -m "Add users and refresh_tokens"
```

Примените миграцию:
```bash
docker exec smart_home_app alembic upgrade head
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

JWT_ACCESS_SECRET=change_me_super_secret_access_key
JWT_REFRESH_SECRET=change_me_super_secret_refresh_key
JWT_ACCESS_EXPIRATION=15
JWT_REFRESH_EXPIRATION=10080

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:4200/auth/oauth/yandex/callback
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

7. Фильтрация устройств по типу
```bash
curl -X GET "http://localhost:4200/api/v1/devices?device_type=lamp" -b cookies_user1.txt
```

8. Фильтрация устройств по локации
```bash
curl -X GET "http://localhost:4200/api/v1/devices?location=Living%20Room" -b cookies_user1.txt
```

9. Фильтрация устройств по статусу
```bash
curl -X GET "http://localhost:4200/api/v1/devices?status=false" -b cookies_user1.txt
```

10. Получение устройства по ID
```bash
curl -X GET "http://localhost:4200/api/v1/devices/1" -b cookies_user1.txt
```

11. Частичное обновление устройства (PATCH)
```bash
curl -X PATCH http://localhost:4200/api/v1/devices/2 \
  -H "Content-Type: application/json" \
  -b cookies_user1.txt \
  -d '{"value":85,"status":false}'
```

12. Полное обновление устройства (PUT)
```bash
curl -X PUT http://localhost:4200/api/v1/devices/2 \
  -H "Content-Type: application/json" \
  -b cookies_user1.txt \
  -d '{"name":"Living Room Smart Lamp","device_type":"lamp","location":"Living Room","status":true,"value":90,"description":"Updated smart LED lamp"}'
```

13. Получение всех типов устройств пользователя
```bash
curl -X GET "http://localhost:4200/api/v1/devices/types/" -b cookies_user1.txt
```

14. Получение всех локаций устройств пользователя
```bash
curl -X GET "http://localhost:4200/api/v1/devices/locations/" -b cookies_user1.txt
```

15. Обновление токенов (Refresh)
```bash
curl -X POST http://localhost:4200/auth/refresh -b cookies_user1.txt -c cookies_user1.txt
```

16. Выход из текущей сессии (Logout)
```bash
curl -X POST http://localhost:4200/auth/logout -b cookies_user1.txt -c cookies_user1.txt
```

17. Завершение всех сессий пользователя (Logout-all)
```bash
curl -X POST http://localhost:4200/auth/logout-all -b cookies_user1.txt -c cookies_user1.txt
```

18. Попытка доступа к защищенному ресурсу без токена
```bash
curl -X GET "http://localhost:4200/api/v1/devices"
```

19. Попытка получить устройство другого пользователя
```bash
curl -X GET "http://localhost:4200/api/v1/devices/1" -b cookies_user2.txt
```

20. Мягкое удаление устройства (Soft Delete)
```bash
curl -X DELETE "http://localhost:4200/api/v1/devices/1" -b cookies_user1.txt
```

21. Проверить, что устройство не было удалено физически
```bash
docker exec -it smart_home_db psql -U student -d smart_home -c "SELECT id, name, deleted_at FROM devices WHERE deleted_at IS NOT NULL;"
```

22. Запрос на сброс пароля (Forgot Password)
```bash
curl -X POST http://localhost:4200/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com"}'
```

23. Сброс пароля (Reset Password)
```bash
curl -X POST http://localhost:4200/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","token":"user1@example.com","new_password":"newsecret456"}'
```

24. Инициация входа через Yandex OAuth.
Необходимо открыть в браузере http://localhost:4200/auth/oauth/yandex

25. Проверка Cookies после входа
```bash
cat cookies.txt
```

26. Очистить все таблицы базы данных
```bash
docker exec -it smart_home_db psql -U student -d smart_home -c "TRUNCATE TABLE refresh_tokens, devices, users RESTART IDENTITY CASCADE;"
```

27. Проверка в базе данных
Подключение к PostgreSQL
```bash
docker exec -it smart_home_db psql -U student -d smart_home -c "TRUNCATE TABLE refresh_tokens, devices, users RESTART IDENTITY CASCADE;"
```

Просмотр пользователей и их солей
```bash
SELECT id, email, salt, password_hash FROM users;
```

Просмотр устройств с меткой удаления
```bash
SELECT id, name, user_id, deleted_at FROM devices;
```

Просмотр активных Refresh токенов
```bash
SELECT id, user_id, expires_at, revoked_at FROM refresh_tokens;
```