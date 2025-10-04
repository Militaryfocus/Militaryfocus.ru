# 🔒 Руководство по безопасности

Комплексное руководство по безопасности Military Focus Blog System.

## 🛡️ Обзор безопасности

Система включает многоуровневую защиту от различных типов атак и угроз:

- **Аутентификация и авторизация**
- **Защита от веб-атак** (XSS, CSRF, SQL-инъекции)
- **Rate limiting** и защита от DDoS
- **Мониторинг безопасности** в реальном времени
- **Шифрование данных** и безопасные сессии
- **Аудит действий** пользователей

## 🔐 Аутентификация

### Система паролей

#### Требования к паролям
```python
# Минимальные требования
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SYMBOLS = True
PASSWORD_MAX_AGE_DAYS = 90
```

#### Хеширование паролей
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Создание хеша
password_hash = generate_password_hash('user_password', method='pbkdf2:sha256')

# Проверка пароля
is_valid = check_password_hash(password_hash, 'user_password')
```

#### Политика паролей
- Минимум 8 символов
- Обязательно: заглавные, строчные буквы, цифры, символы
- Запрещены: простые пароли, словарные слова
- Автоматическая смена каждые 90 дней
- История паролей (нельзя повторять последние 5)

### Двухфакторная аутентификация (2FA)

#### Настройка TOTP
```python
import pyotp
import qrcode

# Генерация секрета
secret = pyotp.random_base32()

# Создание QR-кода
totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
    name="user@example.com",
    issuer_name="Military Focus Blog"
)
qr = qrcode.make(totp_uri)
```

#### Проверка кода
```python
# Проверка 6-значного кода
totp = pyotp.TOTP(user.two_factor_secret)
is_valid = totp.verify(code, valid_window=1)
```

### Сессии и токены

#### Безопасные сессии
```python
# Настройки сессий
SESSION_COOKIE_SECURE = True  # Только HTTPS
SESSION_COOKIE_HTTPONLY = True  # Защита от XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF
SESSION_PERMANENT = False
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
```

#### JWT токены
```python
import jwt
from datetime import datetime, timedelta

# Создание токена
payload = {
    'user_id': user.id,
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow()
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Проверка токена
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = payload['user_id']
except jwt.ExpiredSignatureError:
    return "Токен истек"
except jwt.InvalidTokenError:
    return "Неверный токен"
```

## 🚫 Защита от атак

### SQL-инъекции

#### Параметризованные запросы
```python
# Безопасно - параметризованный запрос
user = User.query.filter_by(username=username).first()

# Безопасно - SQLAlchemy ORM
posts = Post.query.filter(Post.title.contains(search_term)).all()

# Опасно - прямая конкатенация (НЕ ИСПОЛЬЗОВАТЬ!)
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

#### Валидация входных данных
```python
from wtforms import StringField, validators

class LoginForm(FlaskForm):
    username = StringField('Username', [
        validators.Length(min=3, max=20),
        validators.Regexp(r'^[a-zA-Z0-9_]+$', message='Только буквы, цифры и _')
    ])
    password = PasswordField('Password', [
        validators.Length(min=8),
        validators.DataRequired()
    ])
```

### XSS (Cross-Site Scripting)

#### Санитизация HTML
```python
import bleach

# Разрешенные теги и атрибуты
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'h1': ['id'], 'h2': ['id'], 'h3': ['id']
}

# Санитизация контента
clean_content = bleach.clean(user_input, 
                           tags=ALLOWED_TAGS, 
                           attributes=ALLOWED_ATTRIBUTES)
```

#### CSP (Content Security Policy)
```python
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'"
    )
    return response
```

### CSRF (Cross-Site Request Forgery)

#### CSRF токены
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# В формах
<form method="POST">
    {{ csrf_token() }}
    <!-- остальные поля -->
</form>

# В AJAX запросах
headers: {
    'X-CSRFToken': getCookie('csrf_token')
}
```

#### SameSite cookies
```python
# Настройка cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
```

### Rate Limiting

#### Ограничение запросов
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Ограничения для конкретных эндпоинтов
@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # логика входа
    pass

@app.route('/api/posts', methods=['POST'])
@limiter.limit("10 per hour")
def create_post():
    # создание поста
    pass
```

#### IP блокировка
```python
class IPBlocker:
    def __init__(self):
        self.blocked_ips = set()
        self.failed_attempts = defaultdict(int)
    
    def check_ip(self, ip):
        if ip in self.blocked_ips:
            return False
        
        # Проверка количества неудачных попыток
        if self.failed_attempts[ip] >= 5:
            self.block_ip(ip)
            return False
        
        return True
    
    def block_ip(self, ip, duration_hours=24):
        self.blocked_ips.add(ip)
        # Логирование блокировки
        self.log_security_event('ip_blocked', {'ip': ip})
```

## 🔍 Мониторинг безопасности

### Логирование событий

#### Система аудита
```python
import logging
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, username, ip, success):
        event = {
            'type': 'login_attempt',
            'username': username,
            'ip': ip,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.info(f"Login attempt: {event}")
    
    def log_security_violation(self, violation_type, details):
        event = {
            'type': 'security_violation',
            'violation': violation_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.warning(f"Security violation: {event}")
```

#### Отслеживание подозрительной активности
```python
class SecurityMonitor:
    def __init__(self):
        self.suspicious_patterns = {
            'multiple_failed_logins': 5,
            'rapid_requests': 100,  # запросов в минуту
            'unusual_user_agent': True,
            'sql_injection_patterns': [
                r'union\s+select',
                r'drop\s+table',
                r'insert\s+into',
                r'delete\s+from'
            ]
        }
    
    def analyze_request(self, request):
        # Проверка User-Agent
        if self.is_suspicious_user_agent(request.user_agent.string):
            self.flag_suspicious_activity('suspicious_user_agent', request)
        
        # Проверка на SQL-инъекции
        if self.detect_sql_injection(request):
            self.flag_suspicious_activity('sql_injection_attempt', request)
        
        # Проверка частоты запросов
        if self.check_request_frequency(request):
            self.flag_suspicious_activity('high_frequency_requests', request)
```

### Геолокация и анализ IP

#### Определение местоположения
```python
import geoip2.database

class GeoLocationAnalyzer:
    def __init__(self, db_path='GeoLite2-City.mmdb'):
        self.reader = geoip2.database.Reader(db_path)
    
    def get_location(self, ip):
        try:
            response = self.reader.city(ip)
            return {
                'country': response.country.name,
                'city': response.city.name,
                'latitude': response.location.latitude,
                'longitude': response.location.longitude,
                'timezone': response.location.time_zone
            }
        except:
            return None
    
    def is_suspicious_location(self, ip):
        location = self.get_location(ip)
        if not location:
            return True
        
        # Проверка на известные VPN/Proxy
        suspicious_countries = ['CN', 'RU', 'KP']  # пример
        return location['country'] in suspicious_countries
```

## 🔐 Шифрование данных

### Шифрование чувствительных данных

#### Шифрование в базе данных
```python
from cryptography.fernet import Fernet
import base64

class DataEncryption:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode()
    
    def encrypt_field(self, model, field_name):
        """Декоратор для автоматического шифрования полей"""
        original_value = getattr(model, field_name)
        if original_value:
            encrypted = self.encrypt(original_value)
            setattr(model, f"{field_name}_encrypted", encrypted)
            setattr(model, field_name, None)

# Использование
encryption = DataEncryption(SECRET_KEY.encode())

class User(db.Model):
    email_encrypted = db.Column(db.LargeBinary)
    
    @property
    def email(self):
        if self.email_encrypted:
            return encryption.decrypt(self.email_encrypted)
        return None
    
    @email.setter
    def email(self, value):
        if value:
            self.email_encrypted = encryption.encrypt(value)
```

### Безопасное хранение файлов

#### Проверка загружаемых файлов
```python
import magic
from werkzeug.utils import secure_filename

class FileSecurity:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    def is_safe_file(self, file):
        # Проверка расширения
        if not self.has_allowed_extension(file.filename):
            return False
        
        # Проверка MIME типа
        file_content = file.read(1024)
        file.seek(0)  # Сброс позиции
        mime_type = magic.from_buffer(file_content, mime=True)
        
        allowed_mimes = {
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf', 'text/plain'
        }
        
        return mime_type in allowed_mimes
    
    def secure_filename(self, filename):
        return secure_filename(filename)
```

## 🚨 Реагирование на инциденты

### Автоматические меры

#### Блокировка подозрительных IP
```python
class IncidentResponse:
    def __init__(self):
        self.blocked_ips = set()
        self.alert_thresholds = {
            'failed_logins': 5,
            'sql_injection_attempts': 1,
            'xss_attempts': 1
        }
    
    def handle_security_incident(self, incident_type, ip, details):
        # Логирование инцидента
        self.log_incident(incident_type, ip, details)
        
        # Автоматические меры
        if incident_type == 'sql_injection_attempt':
            self.block_ip_permanently(ip)
            self.send_security_alert(incident_type, ip, details)
        
        elif incident_type == 'multiple_failed_logins':
            self.block_ip_temporarily(ip, duration_hours=24)
        
        elif incident_type == 'xss_attempt':
            self.block_ip_temporarily(ip, duration_hours=1)
    
    def send_security_alert(self, incident_type, ip, details):
        # Отправка уведомления администратору
        alert_data = {
            'type': incident_type,
            'ip': ip,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': self.get_severity(incident_type)
        }
        
        # Отправка email/SMS/Telegram
        self.notify_admin(alert_data)
```

### Ручные меры

#### Процедуры реагирования
1. **Немедленные действия:**
   - Блокировка подозрительного IP
   - Отключение скомпрометированного аккаунта
   - Сохранение логов и доказательств

2. **Анализ инцидента:**
   - Определение масштаба атаки
   - Анализ векторов атаки
   - Оценка ущерба

3. **Восстановление:**
   - Патчирование уязвимостей
   - Обновление системы безопасности
   - Мониторинг повторных атак

## 🔧 Настройка безопасности

### Конфигурация .env
```env
# Безопасность
SECRET_KEY=your-super-secret-key-here
SECURITY_PASSWORD_SALT=your-password-salt
WTF_CSRF_SECRET_KEY=your-csrf-secret

# Сессии
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/1
RATELIMIT_DEFAULT=100 per hour

# Шифрование
ENCRYPTION_KEY=your-encryption-key-base64

# Мониторинг
SECURITY_LOG_LEVEL=INFO
SECURITY_ALERT_EMAIL=admin@example.com
```

### Настройка файрвола
```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Блокировка подозрительных IP
sudo ufw deny from 192.168.1.100
```

### SSL/TLS настройка
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Современные SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Другие заголовки безопасности
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

## 📊 Мониторинг и отчеты

### Дашборд безопасности
```python
@app.route('/admin/security-dashboard')
@admin_required
def security_dashboard():
    stats = {
        'blocked_ips': len(get_blocked_ips()),
        'failed_logins_today': get_failed_logins_count(),
        'security_events_today': get_security_events_count(),
        'active_threats': get_active_threats(),
        'top_attack_vectors': get_top_attack_vectors()
    }
    
    return render_template('admin/security_dashboard.html', stats=stats)
```

### Еженедельные отчеты
```python
def generate_security_report():
    report = {
        'period': 'last_week',
        'summary': {
            'total_incidents': 0,
            'blocked_ips': 0,
            'failed_logins': 0,
            'security_score': 95
        },
        'incidents': [],
        'recommendations': []
    }
    
    # Генерация отчета
    return report
```

## 🎯 Рекомендации по безопасности

### Для разработчиков
1. **Всегда валидируйте входные данные**
2. **Используйте параметризованные запросы**
3. **Регулярно обновляйте зависимости**
4. **Проводите код-ревью с фокусом на безопасность**
5. **Тестируйте на уязвимости**

### Для администраторов
1. **Регулярно мониторьте логи безопасности**
2. **Обновляйте систему и зависимости**
3. **Настройте автоматические уведомления**
4. **Проводите регулярные аудиты безопасности**
5. **Обучайте пользователей основам безопасности**

### Для пользователей
1. **Используйте сложные пароли**
2. **Включите двухфакторную аутентификацию**
3. **Не переходите по подозрительным ссылкам**
4. **Регулярно обновляйте браузер**
5. **Сообщайте о подозрительной активности**

---

**Безопасность - это процесс, а не состояние!** 🛡️

Регулярно обновляйте систему безопасности и следите за новыми угрозами.