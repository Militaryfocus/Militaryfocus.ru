# Dockerfile для продакшена
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash blog

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директории для логов и загрузок
RUN mkdir -p /app/logs /app/uploads && \
    chown -R blog:blog /app

# Переключаемся на пользователя blog
USER blog

# Открываем порт
EXPOSE 5000

# Переменные окружения
ENV FLASK_ENV=production
ENV FLASK_APP=app.py

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]