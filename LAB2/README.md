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

### Конфигурация probes в deployment.yaml

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

  