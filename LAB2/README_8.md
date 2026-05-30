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

Для перезапуска Docker используйте команду:

```bash
docker-compose restart app
```

Просмотр логов в реальном времени

```bash
docker logs smart_home_app -f
```

# Просмотр сообщения через API RabbitMQ

Остановите приложение

```bash
docker-compose stop app
```

Зарегистрируйте пользователя

```bash
curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"gummel545@gmail.com\",\"password\":\"123456\",\"full_name\":\"Test\"}'

```

Просмотрите сообщение

```bash
curl.exe -u student:student_secure_rabbit_pass -X POST "http://localhost:15672/api/queues/%2F/wp.auth.user.registered/get" -H "Content-Type: application/json" -d '{\"count\":1,\"ackmode\":\"ack_requeue_true\",\"encoding\":\"auto\",\"truncate\":50000}'
```

Запустите приложение

```bash
docker-compose start app
```

# Тестирование отказоустойчивости

Временно добавьте большую задержку в consumer
```bash
docker exec -it smart_home_app bash
```

```bash
sed -i 's/async def _process_message/async def _process_message\n        await asyncio.sleep(120)/' /app/app/core/queue/consumer.py
exit
```

Перезагрузите API

```bash
docker-compose restart app
```

Зарегистрируйте пользователей

```bash
curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user1@test.com\",\"password\":\"pass123\",\"full_name\":\"User1\"}'

curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user2@test.com\",\"password\":\"pass123\",\"full_name\":\"User2\"}'

curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user3@test.com\",\"password\":\"pass123\",\"full_name\":\"User3\"}'
```

После тестирования необходимо удалить строку с задержкой

```bash
docker exec -it smart_home_app bash
```

```bash
sed -i '/await asyncio.sleep(120)/d' /app/app/core/queue/consumer.py
exit
```

# Тестирование механизма повторных накоплений

Временно изменим данные в файле .env на неверные и выполним несколько запросов регистрации

```bash
curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user1@test.com\",\"password\":\"pass123\",\"full_name\":\"User1\"}'

curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user2@test.com\",\"password\":\"pass234\",\"full_name\":\"User2\"}'

curl.exe -X POST http://localhost:4200/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user3@test.com\",\"password\":\"pass345\",\"full_name\":\"User3\"}'
```

Просмотр очередей

```bash
docker exec -it smart_home_rabbitmq rabbitmqctl list_queues
```

Очистка очереди

```bash
docker exec -it smart_home_rabbitmq rabbitmqctl delete_queue wp.auth.user.registered
```

Проверка соединения

```bash
docker exec -it smart_home_app python -c "from app.core.queue.connection import RabbitMQConnection; import asyncio; asyncio.run(RabbitMQConnection().connect())"
```

Проверка количества consumers для очереди

```bash
docker exec -it smart_home_rabbitmq rabbitmqctl list_queues name consumers messages
```

Просмотр всех consumers для очереди

```bash
docker exec -it smart_home_rabbitmq rabbitmqctl list_consumers
```

Проверка binding

```bash
docker exec -it smart_home_rabbitmq rabbitmqctl list_bindings | findstr "user.registered"
```

# Настройка .env для SMTP

Для тестирования отправки приветственных писем потребуется реальный email аккаунт с поддержкой SMTP.

1. Создайте почтовый ящик на Яндексе
2. Получите пароль приложения

- Войдите в аккаунт Яндекса
- Перейдите в Управление аккаунтом → Безопасность
- Найдите раздел Пароли приложений
- Нажмите Создать новый пароль
- Выберите тип: Почта
- Назовите: Smart Home API
- Скопируйте сгенерированный пароль

тест
python test_smtp.py

docker-compose logs -f
