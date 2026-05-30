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
