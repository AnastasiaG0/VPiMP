# Лабораторная работа №9
## Знакомство с масштабированием веб-приложений на примере Kubernetes

### Цель работы
Познакомиться с процессом горизонтального масштабирования веб-приложений на примере Kubernetes, изучить понятия liveness / readiness probes, познакомиться с распределёнными блокировками.

### Технические требования
- Наличие интернет-соединения.
- Наличие [cURL](https://curl.se/download.html) / [Postman](https://www.postman.com/downloads/) / [Insomnia](https://insomnia.rest/download).
- Наличие [Docker](https://docs.docker.com/desktop/) и [Docker Compose](https://docs.docker.com/compose/install/).
- Наличие [Kubernetes](https://docs.docker.com/desktop/features/kubernetes/) (в составе Docker Desktop)
- Наличие [k9s](https://k9scli.io/topics/install/) (опционально, для визуализации)

### Краткие теоретические сведения

#### 1. Что такое Kubernetes?

Kubernetes (K8s) — это открытая платформа для оркестрации контейнеризированных приложений, предоставляющая механизмы для автоматического развёртывания, масштабирования и управления контейнерами.

#### 2. Ключевые абстракции

##### Pod (Под)
- Минимальная единица развёртывания в Kubernetes
- Группа из одного или нескольких контейнеров с общими: сетевым пространством (один IP-адрес), томами хранения (volumes), конфигурацией.
- Поды эфемерны: при сбое создаётся новый, а не «чинится» старый

```yaml
# Пример минимального Pod
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: api
    image: wp-labs/api:1.0.0
    ports:
    - containerPort: 4200
```

##### Deployment (Деплоймент)
- Контроллер для управления стателесс-приложениями
- Обеспечивает:
  - декларативное обновление подов (rolling update)
  - откат к предыдущей версии (rollback)
  - горизонтальное масштабирование (`kubectl scale`)
- Поды в Deployment взаимозаменяемы

```yaml
# Фрагмент Deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: wp-labs/api:1.0.0
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 4200
          initialDelaySeconds: 10
          periodSeconds: 5
```

##### StatefulSet
- Контроллер для статейных приложений (БД, очереди)
- Гарантирует:
  - стабильные сетевые идентификаторы (`pod-0`, `pod-1`...)
  - упорядоченное развёртывание и удаление
  - привязку постоянного хранилища к конкретному поду
> Масштабирование StatefulSet не равносильно автоматической репликация данных

##### Service (Сервис)
- Абстракция для доступа к группе подов
- Типы:
  | Тип | Назначение |
  |-----|-----------|
  | `ClusterIP` (default) | Доступ только внутри кластера |
  | `NodePort` | Доступ через порт на каждом узле |
  | `LoadBalancer` | Внешний балансировщик (облачные провайдеры) |
  | `ExternalName` | DNS-перенаправление на внешний ресурс |

```yaml
# Пример Service
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
  - port: 4200
    targetPort: 4200
```

##### Namespace (Пространство имён)
- Логическая изоляция ресурсов внутри кластера
- Позволяет: разделять среды (dev/stage/prod), применять квоты и политики доступа (RBAC), избегать конфликтов имён

```bash
kubectl create namespace wp-labs
kubectl apply -f manifest.yaml -n wp-labs
```

##### Secret и ConfigMap
- ConfigMap: хранение нечувствительной конфигурации (переменные окружения, конфиг-файлы)
- Secret: хранение чувствительных данных (пароли, токены, ключи)
> Secrets не шифруются по умолчанию в etcd — для продакшена требуется включение шифрования на уровне хранилища

### 3. Probes (Диагностические проверки)

| Тип | Назначение | Действие при провале |
|-----|-----------|---------------------|
| livenessProbe | Проверка, что приложение живо | Перезапуск контейнера |
| readinessProbe | Проверка готовности принимать трафик | Исключение пода из балансировки |
| startupProbe | Для медленно стартующих приложений | Откладывает проверку liveness |

```yaml
# Пример конфигурации probes
livenessProbe:
  httpGet:
    path: /health/live
    port: 4200
  initialDelaySeconds: 30  # ждать 30 сек перед первой проверкой
  periodSeconds: 10        # проверять каждые 10 сек
  failureThreshold: 3      # перезапустить после 3 провалов

readinessProbe:
  httpGet:
    path: /health/ready
    port: 4200
  initialDelaySeconds: 5
  periodSeconds: 5
  successThreshold: 1      # достаточно 1 успеха для возврата в балансировку
```

> liveness-проверка должна быть «лёгкой» (без проверки зависимостей), readiness — «тяжёлой» (с проверкой БД, кэша).

### Важное примечание
> Работа выполнена в академических целях. Масштабирование stateful-сервисов (PostgreSQL, MongoDB, Redis, RabbitMQ, MinIO) через репликацию подов не гарантирует консистентность данных и не рекомендуется для боевой среды. В рамках лабораторной работы данный подход допустим для упрощения локального развёртывания.

### Ход работы

1. Изучите принцип работы liveness / readiness probes на примере кода, представленного в `api`. 

2. В директории `api` замените содержимое на ваш исходный код из предыдущих лабораторных работ.

3. Модифицируйте исходный код, добавив поддержку health-ендпоинтов:
   ```
   GET /health          # общий статус (опционально)
   GET /health/ready    # готовность принимать трафик (проверка БД, кэша, очереди)
   GET /health/live     # «живость» процесса (минимальная проверка)
   ```
   > Ендпоинт `/health/ready` должен возвращать `200` только если все зависимости доступны.

4. Соберите Docker-образ:
   ```bash
   cd api
   docker build -t wp-labs/api:1.0.0 .
   ```

5. Модифицируйте переменные окружения, секреты и манифесты в поддиректориях `k8s/` в соответствии с вашей конфигурацией.

6. Последовательно примените манифесты (удалите неиспользуемые сервисы из команды):
   ```bash
   kubectl apply -f k8s/00-namespace.yaml
   kubectl apply -f k8s/01-postgresql/ \
                -f k8s/02-mongodb/ \
                -f k8s/03-redis/ \
                -f k8s/04-minio/ \
                -f k8s/05-rabbitmq/ \
                -f k8s/06-api/
   ```

7. Проверьте корректность запуска:
   ```bash
   kubectl get all -n wp-labs
   # или используйте k9s: запустите k9s, переключитесь на namespace wp-labs
   # k9s -n wp-labs
   ```

8. Пробросьте порт сервиса `api` через CLI, либо посредством k9s:
   ```bash
   kubectl port-forward svc/api 4200:4200 -n wp-labs
   ```

9. Проверьте health-ендпоинты:
   ```bash
   curl http://localhost:4200/health
   curl http://localhost:4200/health/ready
   curl http://localhost:4200/health/live
   ```
   Убедитесь, что ответы соответствуют ожидаемым статус-кодам.

10. Выполните горизонтальное масштабирование:
   ```bash
   kubectl scale deployment/api --replicas=4 -n wp-labs
   ```

11. Создайте нового пользователя через `POST /users`.  
    В логах подов (`kubectl logs -f <pod-name> -n wp-labs`) убедитесь, что событие обрабатывается только на одном поде.  
    Если обработка дублируется: реализуйте распределённую блокировку в Redis перед критической секцией кода. Пример псевдокода:
    ```typescript
    const lockKey = `lock:user:create:${userId}`;
    const acquired = await redis.set(lockKey, lockId, { EX: 30, NX: true });
    if (acquired) {
      try {
        // критическая секция: создание пользователя
      } finally {
        // атомарное снятие блокировки
        await redis.eval(UNLOCK_SCRIPT, [lockKey, lockId]);
      }
    }
    ```

### Критерии приемки
Репозиторий: 
- Код загружен на GitHub, присутствует `.gitignore`.

Документация:
- Присутствует документация в виде README.md файла
- Присутствует описание основных команд, необходимых для развертывания приложения

Функциональность:
- Весь функционал, реализованный в предыдущих лабораторных работах, отрабатывает корректно

### Справочник CLI-команд

```bash
# === Сборка и деплой ===
docker build -t wp-labs/api:1.0.0 .

kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-postgresql/
kubectl apply -f k8s/02-mongodb/
kubectl apply -f k8s/03-redis/
kubectl apply -f k8s/04-minio/
kubectl apply -f k8s/05-rabbitmq/
kubectl apply -f k8s/06-api/

# === Мониторинг ===
kubectl get all -n wp-labs
kubectl get deployments,statefulsets -n wp-labs
kubectl get pods -n wp-labs -o wide
kubectl logs -f <pod-name> -n wp-labs
kubectl describe pod <pod-name> -n wp-labs

# === Масштабирование ===
kubectl scale deployment/api --replicas=4 -n wp-labs
kubectl autoscale deployment/api --min=2 --max=6 --cpu-percent=70 -n wp-labs

# === Отладка ===
kubectl port-forward svc/api 4200:4200 -n wp-labs
kubectl exec -it <pod-name> -n wp-labs -- /bin/sh

# === Очистка ===
kubectl delete namespace wp-labs
# или покомпонентно:
kubectl delete -f k8s/06-api/ -f k8s/05-rabbitmq/ ... -f k8s/00-namespace.yaml
```

### Контрольные вопросы
1. Что такое Kubernetes и какую проблему он решает?
2. В чём разница между `Pod`, `Deployment` и `StatefulSet`? Когда использовать каждый?
3. Какую роль играет `Service` в архитектуре Kubernetes? Перечислите типы и их отличия.
4. Как представлены секреты в Kubernetes? Какие меры безопасности необходимо учитывать при работе с ними?
5. Что такое горизонтальное и вертикальное масштабирование? Какой тип поддерживает `kubectl scale`?
6. В чём разница между `livenessProbe` и `readinessProbe`? Почему их не следует делать идентичными?
7. Как Kubernetes определяет, что под недоступен для получения трафика?
8. Что такое `Namespace` и зачем он нужен в многопользовательском кластере?
9. Почему масштабирование stateful-сервисов через репликацию подов не гарантирует консистентность данных?
10. Какие условия должны выполняться для корректной работы распределённой блокировки в Redis?

### Рекомендуемая литература и документация
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)
- [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [How to do distributed locking / Martin Kleppmann](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
- [Docker CLI Reference](https://docs.docker.com/reference/cli/)