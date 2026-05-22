# Лабораторная работа №6
## Тема: Знакомство с MongoDB. Сравнение реляционных и документоориентированных СУБД

### Цель работы
- Изучить принципы работы документоориентированных баз данных (NoSQL) на примере MongoDB.
- Освоить различия между реляционной СУБД (PostgreSQL) и документной СУБД (MongoDB).
- Получить практические навыки подключения MongoDB к веб-приложению.
- Реализовать миграцию слоя персистентности существующего приложения с PostgreSQL на MongoDB.

### Технические требования
- Наличие интернет-соединения.
- Наличие [cURL](https://curl.se/download.html) / [Postman](https://www.postman.com/downloads/) / [Insomnia](https://insomnia.rest/download).
- Наличие [Docker](https://docs.docker.com/desktop/) и [Docker Compose](https://docs.docker.com/compose/install/).
- Наличие настроенного окружения для работы с выбранным языком программирования (интерпретатор, компилятор, менеджер зависимостей).
- Наличие клиента для работы с MongoDB (например, [MongoDB Compass](https://www.mongodb.com/products/compass) или CLI).

### Технические ограничения
- СУБД: MongoDB (версия 6 или выше). PostgreSQL не используется в данной работе.
- Архитектура: Модульная (разделение на контроллеры, сервисы, модели/схемы, DTO).
- Конфигурация: Использование переменных окружения (`.env`) для чувствительных данных и настроек подключения.
- Наследование: Данная работа является продолжением Лабораторной работы №2-№5. Все механизмы аутентификации (JWT, OAuth), кеширования (Redis), документирования (Swagger) и бизнес-логика (CRUD, Soft Delete) должны оставаться работоспособными.

### Ход работы

В рамках данной работы необходимо модифицировать существующее приложение, заменив слой работы с данными с PostgreSQL на MongoDB, и провести сравнительный анализ подходов.

#### 1. Подготовка инфраструктуры (Docker)
Обновите конфигурацию `docker-compose.yml`, заменив сервис PostgreSQL на сервис MongoDB. Убедитесь, что переменные окружения для подключения к новой базе данных добавлены в `.env` файл.

Пример обновленного `docker-compose.yml` (фрагмент инфраструктуры):
```yaml
version: "3.8"

services:
  mongo:
    image: mongo:6
    container_name: wp_labs_mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${DB_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${DB_PASSWORD}
    ports:
      - "27017:27017"
    volumes:
      - wp_labs_mongo:/data/db
    networks:
      - wp_labs_network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    # Конфигурация Redis из Лабораторной работы №5 остается без изменений
    ...

  app:
    build: .
    container_name: wp_labs_app
    restart: unless-stopped
    environment:
      MONGO_URI: ${MONGO_URI}
      # Остальные переменные окружения (Redis, JWT, etc.)
      ...
    depends_on:
      mongo:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - wp_labs_network
```

Пример файла `.env`:
```bash
DB_USER=student
DB_PASSWORD=student_secure_password
DB_NAME=wp_labs
MONGO_URI="mongodb://student:student_secure_password@mongo:27017/wp_labs?authSource=admin"
```

#### 2. Проектирование модели данных
Перепроектируйте модели данных с учетом документной ориентированности MongoDB.
- Идентификаторы: Вместо автоинкремента, используйте стандартный `_id` типа ObjectId (или UUID), генерируемый драйвером базы данных.
- Схема: Определите схему документа. В отличие от строгой типизации SQL, MongoDB позволяет организовать гибкую схему, однако рекомендуется использовать валидацию на уровне приложения (ODM/ORM) для целостности данных.
- Связи: Проанализируйте связи между сущностями. Рассмотрите возможность встраивания (Embedding) связанных данных внутрь основного документа вместо использования ссылок (References), если это целесообразно для производительности чтения.
- Soft Delete: Реализуйте механизм мягкого удаления аналогично Лабораторной работе №2 (например, поле `deletedAt` или `isDeleted`). Убедитесь, что запросы на получение данных автоматически фильтруют удаленные документы.

#### 3. Реализация слоя данных (ODM/Driver)
Настройте подключение к базе данных, используя библиотеку, соответствующую вашему стеку (например, Mongoose для NestJS, Spring Data MongoDB для Java, PyMongo/Beanie для Python и тп).
- Конфигурацию подключения (URI, имя БД) приложение должно получать из переменных окружения.
- Реализуйте репозитории или сервисы для работы с данными.

#### 4. Тестирование и валидация
Протестируйте ваше API с помощью консольной утилиты cURL или аналогов.
- CRUD: Убедитесь, что создание, чтение, обновление и удаление работают корректно.
- Пагинация: Проверьте работу пагинации. В MongoDB пагинация часто реализуется через `skip` и `limit` или курсоры.
- Авторизация: Проверьте вход, получение токенов, доступ к защищенным ресурсам.
- Redis: Убедитесь, что кеширование работает и инвалидация происходит при изменении данных.
- Данные: Проверьте через MongoDB Compass или CLI, что данные сохраняются в виде документов.

### Критерии приемки
- Репозиторий: Код загружен на GitHub/GitLab.
- Документация: Файл `README.md` содержит:
    - Краткое описание проекта.
    - Инструкция по запуску через `docker-compose up --build`.
    - Пример файла переменных окружения (`.env.example`).
    - Описание API (список эндпоинтов).
- Функциональность:
    - Все HTTP методы работают корректно.
    - Реализовано мягкое удаление.
    - Реализована пагинация.
    - Авторизация и кеширование работают корректно с новой БД.
    - Запросы на получение не возвращают удаленные записи.
- Код и Инфраструктура:
    - Соблюдена модульная структура.
    - Присутствует валидация данных.
    - Используются переменные окружения.
    - Приложение успешно развертывается на чистой базе данных MongoDB.
    - Сервис MongoDB защищен паролем.

### Контрольные вопросы
1.  В чем заключается основное отличие документоориентированной базы данных от реляционной?
2.  Что такое BSON и чем он отличается от JSON?
3.  Какие преимущества и недостатки имеет встраивание документов (Embedding) по сравнению со ссылками (References) в MongoDB?
4.  Как обеспечивается целостность данных в MongoDB по сравнению с PostgreSQL (транзакции, валидация схем)?
5.  Что произойдет, если попытаться записать данные неверного типа в поле, объявленное в схеме ODM?
6.  Как влияет отсутствие JOIN-ов на проектирование структуры данных в MongoDB?
7.  Зачем нужны индексы в MongoDB и как они влияют на производительность записи?
8.  Как реализовать уникальность поля (например, email) в MongoDB?
10. Какие сценарии использования существуют для MongoDB, а какие для PostgreSQL?

### Рекомендуемая литература и документация
- MongoDB: [Официальная документация MongoDB](https://www.mongodb.com/docs/)
- MongoDB University: [Бесплатные курсы по MongoDB](https://learn.mongodb.com/)
- SQL vs NoSQL: [Различия между SQL и NoSQL базами данных](https://www.mongodb.com/resources/basics/databases/sql-vs-nosql)
- Документация по ODM/Driver для допустимых стеков:
    - TypeScript (NestJS): [Mongoose](https://mongoosejs.com/docs/) или [@nestjs/mongoose](https://docs.nestjs.com/techniques/mongodb)
    - Java (Spring Boot): [Spring Data MongoDB](https://spring.io/projects/spring-data-mongodb)
    - Python (FastAPI/Flask): [Beanie](https://beanie-odm.dev/) или [PyMongo](https://pymongo.readthedocs.io/)
    - Go (Gin/Fiber): [MongoDB Go Driver](https://www.mongodb.com/docs/drivers/go/)
    - PHP (Laravel): [Laravel MongoDB](https://www.mongodb.com/docs/laravel/)
- Индексы: [Документация по индексам MongoDB](https://www.mongodb.com/docs/manual/indexes/)
- Агрегации: [MongoDB Aggregation Pipeline](https://www.mongodb.com/docs/manual/aggregation/)