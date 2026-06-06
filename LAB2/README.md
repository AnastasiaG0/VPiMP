# Лабораторная работа №9
## Знакомство с масштабированием веб-приложений на примере Kubernetes

## Описание проекта
В данной лабораторной работе выполнено развёртывание веб-приложения Smart Home API в оркестраторе Kubernetes с поддержкой горизонтального масштабирования. Реализованы liveness и readiness пробы для проверки состояния приложения, настроены распределённые блокировки для предотвращения дублирования операций при масштабировании, а также проведено тестирование балансировки нагрузки между несколькими репликами приложения.

## Технологии

- FastAPI - веб-фреймворк
- MongoDB - документоориентированная СУБД
- Motor - асинхронный драйвер MongoDB
- Redis - кеширование и хранение сессий
- JWT - аутентификация
- Docker - контейнеризация
- Swagger UI - автоматическая документация API
- MinIO - хранилище файлов
- RabbitMQ - брокер сообщений
- SMTP (Gmail) - отправка приветственных писем и уведомлений
- Kubernetes (K8s) - оркестрация контейнеров
- kubectl - CLI для управления Kubernetes

## Требования

- Docker и Docker Compose
- cURL / Postman / Insomia
- Kubernetes

## Используемые абстракции Kubernetes

| Абстракция | Назначение | Где используется |
|------------|------------|------------------|
| **Namespace** | Логическая изоляция ресурсов | `smart-home` |
| **Pod** | Минимальная единица развёртывания | API, MongoDB, Redis, MinIO, RabbitMQ |
| **Deployment** | Управление stateless приложениями | API, Redis |
| **StatefulSet** | Управление stateful приложениями | MongoDB, MinIO, RabbitMQ |
| **Service (ClusterIP)** | Внутренняя балансировка нагрузки | Все сервисы |
| **ConfigMap** | Хранение несекретной конфигурации | API (переменные окружения) |
| **Secret** | Хранение секретов | Пароли, токены, ключи |
| **PersistentVolumeClaim** | Постоянное хранение данных | MongoDB, MinIO, RabbitMQ |

## Health-ендпоинты (Probes)

В приложении реализованы три диагностических эндпоинта:

| Эндпоинт | Тип пробы | Назначение | Код ответа |
|----------|-----------|------------|-------------|
| `GET /health/live` | livenessProbe | Проверка, живо ли приложение | 200 OK |
| `GET /health/ready` | readinessProbe | Проверка готовности принимать трафик | 200 OK / 503 |
| `GET /health` | Общий статус | Сводная информация о состоянии | 200 OK |

## Конфигурация probes в deployment.yaml

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
  successThreshold: 1

readinessProbe:
  httpGet:
    path: /health/ready
    port: http
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
  successThreshold: 1
```

## Установка и запуск

Скопируйте `.env.example` в `.env` и настройте переменные:
```bash
cp .env.example .env
```

Соберите Docker образ:
 ```bash
docker build -t smart-home/api:1.0.0 .
 ```

Проверьте, что образ был создан:
```bash
docker images | findstr smart-home
```

Убедитесь, что Kubernetes включен в Docker Desktop:
```bash
kubectl version
```

Создайте namespace:
```bash
kubectl create namespace smart-home
```

Примените манифесты:
```bash
kubectl apply -f k8s/01-mongodb/
kubectl apply -f k8s/02-redis/
kubectl apply -f k8s/03-minio/
kubectl apply -f k8s/04-rabbitmq/
kubectl apply -f k8s/05-api/
```

Проверьте статус:
```bash
kubectl get pods -n smart-home -w
```

Пробросьте порт для доступа к API:
```bash
kubectl port-forward svc/api 4200:4200 -n smart-home
```

Проверьте health-ендпоинты:
```bash
curl.exe http://localhost:4200/health/live
curl.exe http://localhost:4200/health/ready
curl.exe http://localhost:4200/health
```

Выполните горизонтальное масштабирование:
```bash
kubectl scale deployment/api --replicas=4 -n smart-home
```

Проверьте, что появились поды:
```bash
kubectl get pods -n smart-home -l app=api
```

Проверьте балансировку нагрузки
В одном терминале откройте логи всех подов:
```bash
kubectl logs -f -l app=api -n smart-home --tail=0 --prefix=true
```

В другом окне создайте тестовый под:
```bash
kubectl run test-pod --image=curlimages/curl -it --rm --restart=Never -n smart-home -- sh
```

Внутри test-pod выполните:
```bash
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -X POST http://api:4200/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"test$i@example.com\",\"password\":\"test123\",\"full_name\":\"Test$i\"}"
  echo ""
done
exit
```

Перейдите в окно с логами и убедитесь, что запросы распределяются между разными подами и все запросы создают пользователя, т.к. в параллельных запросах email’ы не повторялись 

Проверьие распределённую блокировку
В одном терминале откройте логи всех подов:
```bash
kubectl logs -f -l app=api -n smart-home --tail=0 --prefix=true
```

В другом окне создайте тестовый под:
```bash
kubectl run test-pod --image=curlimages/curl -it --rm --restart=Never -n smart-home -- sh
```

Внутри test-pod выполните:
```bash
for i in 1 2 3 4 5; do
  curl -X POST http://api:4200/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"duplicate@test.com\",\"password\":\"test123\",\"full_name\":\"Duplicate\"}" &
done
```

Перейдите в окно с логами и убедитесь, что запросы распределяются между разными подами, но при параллельных запросах с одинаковым email только один запрос создаёт пользователя

Очистите ресурсы
```bash
kubectl delete namespace smart-home
```