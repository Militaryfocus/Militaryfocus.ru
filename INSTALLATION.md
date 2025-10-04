# 📦 Руководство по установке

## 🔧 Требования

- Python 3.8+
- pip
- Git
- SQLite (включен в Python)
- Redis (опционально, для кеширования)

## 🚀 Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/Militaryfocus/Militaryfocus.ru.git
cd Militaryfocus.ru
```

### 2. Создание виртуального окружения
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
```bash
# Скопировать пример файла
cp .env.example .env

# Отредактировать .env
# Обязательно установить SECRET_KEY!
```

### 5. Инициализация базы данных
```bash
python app.py
# База данных создастся автоматически при первом запуске
```

### 6. Запуск приложения
```bash
python app.py
# Откройте http://localhost:5000
```

## 📋 Детальная настройка

### Переменные окружения (.env)

```bash
# Основные настройки
SECRET_KEY=your-secret-key-here  # ОБЯЗАТЕЛЬНО изменить!
FLASK_ENV=development
FLASK_DEBUG=True

# База данных
DATABASE_URL=sqlite:///blog.db  # или postgresql://user:pass@host/db

# AI провайдеры (опционально)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# SEO настройки
SITE_URL=http://localhost:5000
SITE_NAME=МойБлог
GOOGLE_ANALYTICS_ID=UA-...

# Email (для уведомлений)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password

# Безопасность
ADMIN_EMAIL=admin@example.com
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Настройка базы данных

**SQLite (по умолчанию):**
```bash
# Ничего дополнительно настраивать не нужно
DATABASE_URL=sqlite:///blog.db
```

**PostgreSQL:**
```bash
# Установить PostgreSQL
# Создать базу данных
createdb blog_db

# В .env
DATABASE_URL=postgresql://user:password@localhost/blog_db
```

**MySQL:**
```bash
# Установить MySQL
# Создать базу данных
mysql -u root -p
CREATE DATABASE blog_db;

# В .env
DATABASE_URL=mysql://user:password@localhost/blog_db
```

### Настройка Redis (опционально)

```bash
# Установка Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Запуск
redis-server

# В .env
REDIS_URL=redis://localhost:6379/0
```

## 🔐 Первоначальная настройка

### Создание администратора

При первом запуске автоматически создается администратор:
- Логин: `admin`
- Пароль: `admin123`

**ВАЖНО:** Сразу измените пароль через профиль!

### Создание категорий

```bash
python ai_manager.py setup --with-content
```

### Генерация тестового контента

```bash
# Создать 10 тестовых постов
python ai_manager.py generate 10
```

## 🐳 Docker установка

### 1. Создайте Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### 2. Создайте docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/blog
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./instance:/app/instance

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=blog
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine

volumes:
  postgres_data:
```

### 3. Запуск
```bash
docker-compose up -d
```

## 🚨 Решение проблем

### Ошибка "No module named 'flask'"
```bash
# Убедитесь, что виртуальное окружение активировано
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt
```

### Ошибка "SECRET_KEY not set"
```bash
# Создайте .env файл
cp .env.example .env

# Сгенерируйте секретный ключ
python -c "import secrets; print(secrets.token_hex(32))"

# Вставьте в .env
SECRET_KEY=сгенерированный_ключ
```

### Ошибка импорта модулей
```bash
# Проверьте структуру проекта
python -c "from blog import create_app; print('OK')"

# Если ошибка, проверьте PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Militaryfocus.ru"
```

### База данных не создается
```bash
# Создайте вручную
python
>>> from blog import create_app
>>> from blog.database import db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

## ✅ Проверка установки

1. **Проверка запуска:**
   - Откройте http://localhost:5000
   - Должна отобразиться главная страница

2. **Проверка админ-панели:**
   - Перейдите на http://localhost:5000/auth/login
   - Войдите как admin/admin123
   - Проверьте доступ к админ-панели

3. **Проверка AI функций:**
   ```bash
   python ai_manager.py test
   ```

4. **Проверка API:**
   ```bash
   curl http://localhost:5000/api/posts
   ```

## 📱 Настройка для production

### 1. Отключите debug режим
```bash
# .env
FLASK_ENV=production
FLASK_DEBUG=False
```

### 2. Используйте WSGI сервер
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Настройте Nginx
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/Militaryfocus.ru/blog/static;
    }
}
```

### 4. Используйте supervisor
```ini
[program:blog]
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=/path/to/Militaryfocus.ru
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/blog.log
```

## 🔄 Обновление

```bash
# Получить последние изменения
git pull origin main

# Обновить зависимости
pip install -r requirements.txt --upgrade

# Перезапустить приложение
# Если используете supervisor
sudo supervisorctl restart blog
```

---

*Руководство обновлено: 4 октября 2025*