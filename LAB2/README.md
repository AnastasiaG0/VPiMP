# Лабораторная работа №7

## Хранение файлов с использованием MinIO (Object Storage)

## Описание проекта

## Технологии

- FastAPI - веб-фреймворк
- MongoDB - документоориентированная СУБД
- Motor - асинхронный драйвер MongoDB
- Redis - кеширование и хранение сессий
- JWT - аутентификация
- Docker - контейнеризация
- Swagger UI - автоматическая документация API
- MinIO - хранилище файлов

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

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=your_secure_password
MINIO_BUCKET=smart-home-files
MINIO_USE_SSL=false
MAX_FILE_SIZE=10485760
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/jpg

### Создание бакета в MinIO

При первом запуске бакет создается автоматически, но также можyj создать его вручную через консоль:

1. Откройте http://localhost:9001
2. Войдите с учетными данными из .env
3. Нажмите "Create Bucket"
4. Введите имя бакета (например, "smart-home-files")
5. Настройте политики доступа

### Доступ к сервисам

API Documentation: http://localhost:4200/api/docs
MinIO Console: http://localhost:9001 (login: minio_admin / ваш пароль)
MongoDB: localhost:27017
Redis: localhost:6379

### API Эндпоинты

| Метод  | URI                     | Описание                                    | Статус успеха  | Доступ                                    |
| ------ | ----------------------- | ------------------------------------------- | -------------- | ----------------------------------------- |
| POST   | /api/v1/files/          | Загрузка нового файла (multipart/form-data) | 201 Created    | Доступно для авторизованных пользователей |
| GET    | /api/v1/files/{file_id} | Скачивание файла по ID                      | 200 OK         | Только владелец                           |
| DELETE | /api/v1/files/{file_id} | Удаление файла (Soft Delete + MinIO)        | 204 No Content | Только владелец                           |
| GET    | /api/v1/files/          | Вывод списка файлов                         | 200 OK         | Только владелец                           |
| POST   | /api/v1/profile/        | Обновление профиля (включая avatarFileId)   | 200 OK         | Только владелец                           |
| GET    | /api/v1/profile/        | Получение текущего профиля                  | 200 OK         | Только владелец                           |

### Тестирование

1. Проверка здоровья всех сервисов

```bash
curl http://localhost:4200/health
```

#### Аутентификация пользователя

2. Регистрация пользователя

```bash
curl -X POST http://localhost:4200/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","password":"secret123","full_name":"User One"}'
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

#### Работа с файлами

5. Загрузка изображения

```bash
curl -X POST http://localhost:4200/api/v1/files/ \
  -b cookies_user1.txt \
  -F "file=@/path/to/avatar.jpg"
```

6. Получение списка файлов пользователя

```bash
curl -X GET "http://localhost:4200/api/v1/files/?skip=0&limit=10" \
  -b cookies_user1.txt
```

7. Скачивание файла

```bash
curl -X GET http://localhost:4200/api/v1/files/{file_id} \
  -b cookies_user1.txt \
  --output downloaded_file.jpg
```

#### Управление профилем

8. Обновление профиля с аватаром

```bash
curl -X POST http://localhost:4200/api/v1/profile/ \
  -b cookies_user1.txt \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Updated Name","bio":"My bio","avatar_file_id":"550e8400-e29b-41d4-a716-446655440000"}'
```

9. Получение обновленного профиля

```bash
curl -X GET http://localhost:4200/api/v1/profile/ \
  -b cookies_user1.txt
```

10. Удаление файла

```bash
curl -X DELETE http://localhost:4200/api/v1/files/550e8400-e29b-41d4-a716-446655440000 \
  -b cookies_user1.txt
```

11. Выход из системы

```bash
curl -X POST http://localhost:4200/auth/logout \
  -b cookies_user1.txt \
  -c cookies_user1.txt
```

#### Проверка кеширования

12. Подключение к Redis и просмотр ключей

```bash
redis-cli -a redis_secure_password
KEYS *
```

13. Просмотр TTL (времени жизни) кеша

```bash
TTL "smart_home:user:profile:673c4f5a8b1f2e3d4c5a6b7c"
```

14. Выход из Redis

```bash
EXIT
```

#### Проверка MinIO Object Storage

15. Проверка файлов через MinIO Client (mc)

```bash
docker exec smart_home_minio mc ls local/smart-home-files/
```

16. Просмотр файлов пользователя

```bash
docker exec smart_home_minio mc ls local/smart-home-files/users/673c4f5a8b1f2e3d4c5a6b7c/
```

17. Проверка метаданных объекта

```bash
docker exec smart_home_minio mc stat local/smart-home-files/users/673c4f5a8b1f2e3d4c5a6b7c/550e8400-e29b-41d4-a716-446655440000.jpg
```
