"""
Модуль безопасности для блога
"""

import os
import secrets
import hashlib
import time
from functools import wraps
from flask import request, jsonify, current_app, g
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Конфигурация безопасности"""
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100  # запросов
    RATE_LIMIT_WINDOW = 3600   # в секундах (1 час)
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = False
    
    # Session security
    SESSION_TIMEOUT = 3600  # 1 час
    PERMANENT_SESSION_LIFETIME = 86400  # 24 часа
    
    # File upload security
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    # Content security
    MAX_CONTENT_LENGTH = 50000  # символов
    BLOCKED_WORDS = ['spam', 'scam', 'hack', 'crack']  # базовый список

class RateLimiter:
    """Простой rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key, limit=SecurityConfig.RATE_LIMIT_REQUESTS, window=SecurityConfig.RATE_LIMIT_WINDOW):
        """Проверяет, разрешен ли запрос"""
        now = time.time()
        
        # Очищаем старые записи
        if key in self.requests:
            self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        else:
            self.requests[key] = []
        
        # Проверяем лимит
        if len(self.requests[key]) >= limit:
            return False
        
        # Добавляем текущий запрос
        self.requests[key].append(now)
        return True

# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()

def rate_limit(limit=None, window=None):
    """Декоратор для ограничения частоты запросов"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Определяем ключ для rate limiting
            if current_user.is_authenticated:
                key = f"user_{current_user.id}"
            else:
                key = f"ip_{request.remote_addr}"
            
            # Проверяем лимит
            if not rate_limiter.is_allowed(key, limit or SecurityConfig.RATE_LIMIT_REQUESTS, 
                                         window or SecurityConfig.RATE_LIMIT_WINDOW):
                return jsonify({'error': 'Слишком много запросов. Попробуйте позже.'}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_password_strength(password):
    """Проверяет силу пароля"""
    errors = []
    
    if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
        errors.append(f"Пароль должен содержать минимум {SecurityConfig.MIN_PASSWORD_LENGTH} символов")
    
    if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Пароль должен содержать минимум одну заглавную букву")
    
    if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Пароль должен содержать минимум одну строчную букву")
    
    if SecurityConfig.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        errors.append("Пароль должен содержать минимум одну цифру")
    
    if SecurityConfig.REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Пароль должен содержать минимум один специальный символ")
    
    return errors

def sanitize_input(text):
    """Очищает пользовательский ввод от потенциально опасных символов"""
    if not text:
        return text
    
    # Удаляем HTML теги
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # Экранируем специальные символы
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#x27;')
    text = text.replace('&', '&amp;')
    
    return text

def check_content_safety(content):
    """Проверяет безопасность контента"""
    if not content:
        return True, []
    
    warnings = []
    content_lower = content.lower()
    
    # Проверяем заблокированные слова
    for word in SecurityConfig.BLOCKED_WORDS:
        if word in content_lower:
            warnings.append(f"Обнаружено подозрительное слово: {word}")
    
    # Проверяем длину контента
    if len(content) > SecurityConfig.MAX_CONTENT_LENGTH:
        warnings.append("Контент слишком длинный")
    
    # Проверяем на спам (повторяющиеся фразы)
    words = content.split()
    if len(words) > 10:
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        for word, freq in word_freq.items():
            if freq > len(words) * 0.3:  # слово встречается более 30% времени
                warnings.append(f"Возможный спам: слово '{word}' повторяется слишком часто")
    
    return len(warnings) == 0, warnings

def generate_secure_token():
    """Генерирует безопасный токен"""
    return secrets.token_urlsafe(32)

def hash_sensitive_data(data):
    """Хеширует чувствительные данные"""
    return hashlib.sha256(data.encode()).hexdigest()

def is_safe_filename(filename):
    """Проверяет безопасность имени файла"""
    if not filename:
        return False
    
    # Проверяем расширение
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in SecurityConfig.ALLOWED_EXTENSIONS:
        return False
    
    # Проверяем на опасные символы
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            return False
    
    return True

def log_security_event(event_type, details, user_id=None):
    """Логирует события безопасности"""
    log_data = {
        'timestamp': time.time(),
        'event_type': event_type,
        'user_id': user_id or (current_user.id if current_user.is_authenticated else None),
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'details': details
    }
    
    logger.warning(f"Security event: {log_data}")

def require_admin(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            log_security_event('unauthorized_admin_access', {
                'function': f.__name__,
                'user_id': current_user.id if current_user.is_authenticated else None
            })
            return jsonify({'error': 'Недостаточно прав доступа'}), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_csrf_token():
    """Проверяет CSRF токен"""
    # Flask-WTF автоматически проверяет CSRF токены
    # Эта функция может быть расширена для дополнительных проверок
    return True