# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

EXPOSE 4200

# Отключаем создание .pyc файлов и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для psycopg2 (драйвер PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN python -m pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Создаем непривилегированного пользователя для запуска приложения и переключаемся на него
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Команда для запуска приложения (будет переопределена в docker-compose.yml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4200"]
