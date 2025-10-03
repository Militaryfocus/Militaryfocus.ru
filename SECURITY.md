# 🔒 РУКОВОДСТВО ПО БЕЗОПАСНОСТИ

## 🚨 КРИТИЧЕСКИ ВАЖНО - ОБЯЗАТЕЛЬНО ВЫПОЛНИТЕ!

### 1. 🔑 Настройка переменных окружения

**СОЗДАЙТЕ ФАЙЛ `.env` НА ОСНОВЕ `.env.example`:**

```bash
cp .env.example .env
```

**ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ:**
- `SECRET_KEY` - сгенерируйте случайную строку длиной 32+ символов
- `DATABASE_URL` - настройте для вашей БД
- `FLASK_DEBUG=False` - для продакшена
- `FLASK_ENV=production` - для продакшена

### 2. 🛡️ Безопасные заголовки HTTP

Система автоматически добавляет следующие заголовки:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy` - строгая политика
- `Strict-Transport-Security` - для HTTPS

### 3. 🔐 CSRF Защита

Все формы автоматически защищены CSRF токенами через Flask-WTF.

### 4. 🔒 Хеширование паролей

Пароли хешируются с помощью Werkzeug:
```python
user.set_password('password')  # Автоматическое хеширование
user.check_password('password')  # Проверка пароля
```

### 5. 🚫 Защита от SQL-инъекций

Используется SQLAlchemy ORM - все запросы параметризованы:
```python
# ✅ Безопасно
User.query.filter_by(username=username).first()

# ❌ Опасно (не используется в проекте)
db.session.execute(f"SELECT * FROM users WHERE username='{username}'")
```

### 6. 📁 Безопасная загрузка файлов

- Ограничение размера файлов: `MAX_CONTENT_LENGTH`
- Проверка типов файлов
- Безопасные пути загрузки

### 7. 🔍 Валидация входных данных

Все формы используют WTForms с валидацией:
- Обязательные поля
- Проверка email
- Ограничение длины
- Санитизация HTML

### 8. 🚨 Мониторинг безопасности

Система отслеживает:
- Попытки входа
- Ошибки аутентификации
- Подозрительную активность
- Производительность системы

## 🚀 РЕКОМЕНДАЦИИ ДЛЯ ПРОДАКШЕНА

### 1. HTTPS
```nginx
# Nginx конфигурация
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Firewall
```bash
# Разрешить только необходимые порты
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### 3. База данных
- Используйте PostgreSQL или MySQL для продакшена
- Настройте SSL соединение
- Регулярно делайте бэкапы
- Используйте отдельного пользователя БД

### 4. Мониторинг
- Настройте алерты на критические ошибки
- Мониторьте использование ресурсов
- Ведите логи всех операций
- Настройте автоматические бэкапы

### 5. Обновления
- Регулярно обновляйте зависимости
- Следите за уязвимостями безопасности
- Используйте автоматические обновления безопасности

## 🔧 НАСТРОЙКА ПРОДАКШЕНА

### 1. Переменные окружения
```bash
# .env для продакшена
SECRET_KEY=your-very-secure-secret-key-here
FLASK_DEBUG=False
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/blog_db
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### 2. WSGI сервер
```bash
# Установка Gunicorn
pip install gunicorn

# Запуск
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 3. Systemd сервис
```ini
# /etc/systemd/system/blog.service
[Unit]
Description=Blog Application
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

## 🧪 ТЕСТИРОВАНИЕ БЕЗОПАСНОСТИ

### 1. Запуск тестов
```bash
python run_tests.py
```

### 2. Проверка уязвимостей
```bash
# Установка safety
pip install safety

# Проверка зависимостей
safety check
```

### 3. Аудит кода
```bash
# Установка bandit
pip install bandit

# Проверка безопасности
bandit -r blog/
```

## 📞 ПОДДЕРЖКА

При обнаружении уязвимостей безопасности:
1. Немедленно сообщите администратору
2. Не публикуйте информацию публично
3. Следуйте принципам ответственного раскрытия

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Python Security](https://python-security.readthedocs.io/)