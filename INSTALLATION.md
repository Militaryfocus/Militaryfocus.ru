# 📦 Руководство по установке

Пошаговое руководство по установке и настройке Military Focus Blog System.

## 🔧 Системные требования

### Минимальные требования
- **Python**: 3.8+
- **ОЗУ**: 2GB
- **Диск**: 1GB свободного места
- **ОС**: Linux, macOS, Windows

### Рекомендуемые требования
- **Python**: 3.11+
- **ОЗУ**: 8GB+
- **Диск**: 10GB+ SSD
- **ОС**: Ubuntu 20.04+, CentOS 8+, macOS 12+

## 🚀 Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/Militaryfocus/Militaryfocus.ru.git
cd Militaryfocus.ru
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_enhanced.txt
```

### 4. Настройка окружения
```bash
cp .env.example .env
```

Отредактируйте `.env` файл:
```env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///instance/blog.db
FLASK_ENV=development
FLASK_DEBUG=True

# ИИ API ключи (опционально)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_AI_KEY=your-google-key

# Настройки безопасности
SECURITY_PASSWORD_SALT=your-password-salt
WTF_CSRF_SECRET_KEY=your-csrf-secret

# Настройки производительности
CACHE_TYPE=simple
REDIS_URL=redis://localhost:6379/0
```

### 5. Инициализация базы данных
```bash
python3 -c "
from blog import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('База данных создана успешно!')
"
```

### 6. Создание администратора
```bash
python3 -c "
from blog import create_app, db
from blog.models_perfect import User
app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Администратор создан: admin/admin123')
"
```

### 7. Запуск сервера
```bash
python3 app.py
```

Откройте браузер и перейдите по адресу: http://localhost:5000

## 🔧 Детальная установка

### Установка Python зависимостей

#### Основные зависимости
```bash
pip install flask==2.3.3
pip install flask-sqlalchemy==3.0.5
pip install flask-login==0.6.3
pip install flask-wtf==1.1.1
pip install flask-migrate==4.0.5
pip install flask-admin==1.6.1
pip install werkzeug==2.3.7
pip install wtforms==3.0.1
pip install sqlalchemy==2.0.21
```

#### ИИ зависимости
```bash
pip install openai==1.3.0
pip install anthropic==0.7.0
pip install google-generativeai==0.3.0
pip install nltk==3.8.1
pip install transformers==4.35.0
pip install torch==2.1.0
pip install scikit-learn==1.3.2
```

#### SEO и аналитика
```bash
pip install beautifulsoup4==4.12.2
pip install requests==2.31.0
pip install lxml==4.9.3
pip install python-slugify==8.0.1
pip install bleach==6.0.0
pip install markdown==3.5.1
```

#### Производительность и кэширование
```bash
pip install redis==5.0.1
pip install psutil==5.9.6
pip install gunicorn==21.2.0
pip install gevent==23.9.1
```

#### Безопасность
```bash
pip install cryptography==41.0.7
pip install pyjwt==2.8.0
pip install geoip2==4.7.0
pip install flask-limiter==3.5.0
```

### Настройка базы данных

#### SQLite (по умолчанию)
```bash
# База данных создается автоматически
# Файл: instance/blog.db
```

#### PostgreSQL (рекомендуется для продакшна)
```bash
# Установка PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb blog_db
sudo -u postgres createuser blog_user

# Настройка .env
DATABASE_URL=postgresql://blog_user:password@localhost/blog_db
```

#### MySQL
```bash
# Установка MySQL
sudo apt-get install mysql-server

# Создание базы данных
mysql -u root -p
CREATE DATABASE blog_db;
CREATE USER 'blog_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON blog_db.* TO 'blog_user'@'localhost';
FLUSH PRIVILEGES;

# Настройка .env
DATABASE_URL=mysql://blog_user:password@localhost/blog_db
```

### Настройка Redis (опционально)

#### Установка Redis
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# CentOS/RHEL
sudo yum install redis

# macOS
brew install redis
```

#### Запуск Redis
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Настройка .env
```env
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
```

### Настройка Nginx (продакшн)

#### Установка Nginx
```bash
sudo apt-get install nginx
```

#### Конфигурация
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/blog/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔐 Настройка безопасности

### Генерация секретных ключей
```bash
python3 -c "
import secrets
print('SECRET_KEY=' + secrets.token_hex(32))
print('SECURITY_PASSWORD_SALT=' + secrets.token_hex(16))
print('WTF_CSRF_SECRET_KEY=' + secrets.token_hex(32))
"
```

### Настройка SSL (Let's Encrypt)
```bash
# Установка Certbot
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Настройка файрвола
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## 🧪 Тестирование установки

### Проверка зависимостей
```bash
python3 -c "
import flask, sqlalchemy, openai, anthropic
print('✅ Все зависимости установлены')
"
```

### Проверка базы данных
```bash
python3 -c "
from blog import create_app, db
from blog.models_perfect import User
app = create_app()
with app.app_context():
    users = User.query.count()
    print(f'✅ База данных работает. Пользователей: {users}')
"
```

### Проверка ИИ системы
```bash
python3 test_ai_system.py
```

### Полная проверка системы
```bash
python3 comprehensive_test.py
```

## 🚀 Запуск в продакшне

### С Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 120 app:app
```

### С systemd
```bash
# Создание сервиса
sudo nano /etc/systemd/system/blog.service
```

```ini
[Unit]
Description=Blog System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/blog
Environment=PATH=/path/to/blog/venv/bin
ExecStart=/path/to/blog/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable blog
sudo systemctl start blog
```

### С Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements*.txt ./
RUN pip install -r requirements.txt -r requirements_enhanced.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

```bash
docker build -t blog-system .
docker run -p 8000:8000 blog-system
```

## 🔧 Настройка мониторинга

### Логирование
```bash
# Настройка ротации логов
sudo nano /etc/logrotate.d/blog
```

```
/path/to/blog/blog_system.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### Мониторинг системы
```bash
# Установка htop для мониторинга
sudo apt-get install htop

# Мониторинг логов
tail -f blog_system.log | grep ERROR
```

## 🐛 Устранение неполадок

### Частые проблемы

#### 1. Ошибки импорта
```bash
# Проверка виртуального окружения
which python3
pip list | grep flask
```

#### 2. Проблемы с базой данных
```bash
# Проверка подключения
python3 -c "
from blog import create_app, db
app = create_app()
with app.app_context():
    db.engine.execute('SELECT 1')
    print('✅ База данных доступна')
"
```

#### 3. Ошибки ИИ API
```bash
# Проверка ключей
python3 -c "
import os
print('OpenAI:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')
print('Anthropic:', 'OK' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')
"
```

#### 4. Проблемы с правами доступа
```bash
# Исправление прав
sudo chown -R www-data:www-data /path/to/blog
sudo chmod -R 755 /path/to/blog
```

### Логи ошибок
```bash
# Просмотр логов
tail -f blog_system.log

# Фильтрация ошибок
grep ERROR blog_system.log

# Мониторинг в реальном времени
tail -f blog_system.log | grep -E "(ERROR|CRITICAL)"
```

## 📞 Поддержка

Если у вас возникли проблемы с установкой:

1. **Проверьте логи**: `tail -f blog_system.log`
2. **Запустите тесты**: `python3 comprehensive_test.py`
3. **Создайте Issue**: [GitHub Issues](https://github.com/Militaryfocus/Militaryfocus.ru/issues)
4. **Обратитесь в поддержку**: support@militaryfocus.ru

---

**Установка завершена!** 🎉

Теперь вы можете перейти к [настройке системы](CONFIGURATION.md) или [изучению функций](BLOG_FUNCTIONS.md).