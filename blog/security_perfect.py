"""
Идеальная система безопасности для блога
Включает защиту от всех типов атак, мониторинг и аудит
"""

import os
import re
import time
import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
from collections import defaultdict, deque
import ipaddress
import geoip2.database
import geoip2.errors

from flask import request, current_app, g, session, abort, jsonify
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash
import redis
from sqlalchemy import and_, or_

from blog.models_perfect import User, UserSession, View
from blog import db
from blog import db as database

class SecurityConfig:
    """Конфигурация безопасности"""
    
    # Настройки паролей
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SYMBOLS = True
    PASSWORD_MAX_AGE_DAYS = 90
    
    # Настройки сессий
    SESSION_TIMEOUT_MINUTES = 30
    SESSION_MAX_CONCURRENT = 5
    SESSION_REMEMBER_DAYS = 30
    
    # Настройки блокировки
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    IP_BLOCK_DURATION_HOURS = 24
    
    # Настройки CSRF
    CSRF_TOKEN_EXPIRY_SECONDS = 3600
    CSRF_TOKEN_LENGTH = 32
    
    # Настройки rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_REQUESTS_PER_HOUR = 1000
    RATE_LIMIT_REQUESTS_PER_DAY = 10000
    
    # Настройки мониторинга
    SECURITY_LOG_RETENTION_DAYS = 30
    SUSPICIOUS_ACTIVITY_THRESHOLD = 10

class PasswordValidator:
    """Валидатор паролей"""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """Валидация пароля"""
        errors = []
        
        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.PASSWORD_MIN_LENGTH} characters long")
        
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if SecurityConfig.PASSWORD_REQUIRE_SYMBOLS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Проверка на простые пароли
        if PasswordValidator._is_common_password(password):
            errors.append("Password is too common, please choose a more unique password")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_common_password(password: str) -> bool:
        """Проверка на простые пароли"""
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        return password.lower() in common_passwords
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Генерация безопасного пароля"""
        import string
        import random
        
        # Определяем набор символов
        chars = string.ascii_lowercase
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE:
            chars += string.ascii_uppercase
        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS:
            chars += string.digits
        if SecurityConfig.PASSWORD_REQUIRE_SYMBOLS:
            chars += "!@#$%^&*(),.?\":{}|<>"
        
        # Генерируем пароль
        password = ''.join(random.choice(chars) for _ in range(length))
        
        # Проверяем, что пароль соответствует требованиям
        is_valid, _ = PasswordValidator.validate_password(password)
        if not is_valid:
            return PasswordValidator.generate_secure_password(length)
        
        return password

class CSRFProtection:
    """Защита от CSRF атак"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Генерация CSRF токена"""
        return secrets.token_urlsafe(SecurityConfig.CSRF_TOKEN_LENGTH)
    
    @staticmethod
    def validate_csrf_token(token: str) -> bool:
        """Валидация CSRF токена"""
        if not token:
            return False
        
        # Проверяем токен в сессии
        session_token = session.get('csrf_token')
        if not session_token:
            return False
        
        # Сравниваем токены
        return hmac.compare_digest(token, session_token)
    
    @staticmethod
    def get_csrf_token() -> str:
        """Получение CSRF токена"""
        token = session.get('csrf_token')
        if not token:
            token = CSRFProtection.generate_csrf_token()
            session['csrf_token'] = token
        return token

class RateLimiter:
    """Система ограничения скорости запросов"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.memory_store = defaultdict(lambda: deque())
    
    def is_rate_limited(self, identifier: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """Проверка ограничения скорости"""
        current_time = time.time()
        window_start = current_time - window
        
        # Очищаем старые записи
        while self.memory_store[identifier] and self.memory_store[identifier][0] < window_start:
            self.memory_store[identifier].popleft()
        
        # Проверяем лимит
        if len(self.memory_store[identifier]) >= limit:
            return True, {
                'limit': limit,
                'remaining': 0,
                'reset_time': int(self.memory_store[identifier][0] + window),
                'retry_after': int(self.memory_store[identifier][0] + window - current_time)
            }
        
        # Добавляем текущий запрос
        self.memory_store[identifier].append(current_time)
        
        return False, {
            'limit': limit,
            'remaining': limit - len(self.memory_store[identifier]),
            'reset_time': int(current_time + window),
            'retry_after': 0
        }
    
    def get_rate_limit_headers(self, identifier: str, limit: int, window: int) -> Dict[str, str]:
        """Получение заголовков для ограничения скорости"""
        is_limited, info = self.is_rate_limited(identifier, limit, window)
        
        headers = {
            'X-RateLimit-Limit': str(info['limit']),
            'X-RateLimit-Remaining': str(info['remaining']),
            'X-RateLimit-Reset': str(info['reset_time'])
        }
        
        if is_limited:
            headers['Retry-After'] = str(info['retry_after'])
        
        return headers

class IPWhitelist:
    """Система белого списка IP адресов"""
    
    def __init__(self):
        self.whitelist = set()
        self.load_whitelist()
    
    def load_whitelist(self):
        """Загрузка белого списка"""
        # Загружаем из файла или базы данных
        try:
            whitelist_file = os.path.join(current_app.root_path, 'security', 'ip_whitelist.txt')
        except RuntimeError:
            # Если нет контекста приложения, используем относительный путь
            whitelist_file = os.path.join('security', 'ip_whitelist.txt')
        
        if os.path.exists(whitelist_file):
            with open(whitelist_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.whitelist.add(line)
    
    def is_whitelisted(self, ip_address: str) -> bool:
        """Проверка, находится ли IP в белом списке"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for whitelist_ip in self.whitelist:
                if ip in ipaddress.ip_network(whitelist_ip, strict=False):
                    return True
        except (ipaddress.AddressValueError, ValueError):
            pass
        return False
    
    def add_to_whitelist(self, ip_address: str):
        """Добавление IP в белый список"""
        self.whitelist.add(ip_address)
    
    def remove_from_whitelist(self, ip_address: str):
        """Удаление IP из белого списка"""
        self.whitelist.discard(ip_address)

class GeolocationTracker:
    """Отслеживание геолокации"""
    
    def __init__(self):
        self.geoip_db = None
        self.load_geoip_database()
    
    def load_geoip_database(self):
        """Загрузка базы данных GeoIP"""
        try:
            try:
                db_path = os.path.join(current_app.root_path, 'security', 'GeoLite2-City.mmdb')
            except RuntimeError:
                db_path = os.path.join('security', 'GeoLite2-City.mmdb')
            if os.path.exists(db_path):
                self.geoip_db = geoip2.database.Reader(db_path)
        except Exception as e:
            # Используем стандартный логгер вместо current_app
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load GeoIP database: {e}")
    
    def get_location(self, ip_address: str) -> Dict[str, str]:
        """Получение геолокации по IP"""
        if not self.geoip_db:
            return {'country': None, 'city': None, 'region': None}
        
        try:
            response = self.geoip_db.city(ip_address)
            return {
                'country': response.country.iso_code,
                'city': response.city.name,
                'region': response.subdivisions.most_specific.name
            }
        except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error):
            return {'country': None, 'city': None, 'region': None}

class SecurityAuditLogger:
    """Система аудита безопасности"""
    
    def __init__(self):
        try:
            self.log_file = os.path.join(current_app.root_path, 'logs', 'security.log')
        except RuntimeError:
            self.log_file = os.path.join('logs', 'security.log')
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Создание директории для логов"""
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_event(self, event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
        """Логирование события безопасности"""
        timestamp = datetime.utcnow().isoformat()
        ip_address = request.remote_addr if request else 'unknown'
        user_id = current_user.id if current_user.is_authenticated else None
        
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'severity': severity,
            'ip_address': ip_address,
            'user_id': user_id,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details
        }
        
        # Записываем в файл
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} [{severity}] {event_type}: {log_entry}\n")
        
        # Записываем в базу данных
        self._log_to_database(log_entry)
    
    def _log_to_database(self, log_entry: Dict[str, Any]):
        """Запись в базу данных"""
        try:
            from blog.models_perfect import SecurityLog
            security_log = SecurityLog(
                event_type=log_entry['event_type'],
                severity=log_entry['severity'],
                ip_address=log_entry['ip_address'],
                user_id=log_entry['user_id'],
                user_agent=log_entry['user_agent'],
                details=log_entry['details']
            )
            database.session.add(security_log)
            database.session.commit()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log security event to database: {e}")

class SuspiciousActivityDetector:
    """Детектор подозрительной активности"""
    
    def __init__(self):
        self.activity_patterns = defaultdict(list)
        self.suspicious_ips = set()
        self.blocked_ips = set()
    
    def analyze_request(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Анализ запроса на подозрительную активность"""
        ip_address = request_data.get('ip_address')
        user_agent = request_data.get('user_agent', '')
        path = request_data.get('path', '')
        
        # Проверка на SQL инъекции
        if self._detect_sql_injection(request_data):
            return True, "SQL injection attempt detected"
        
        # Проверка на XSS
        if self._detect_xss(request_data):
            return True, "XSS attempt detected"
        
        # Проверка на подозрительные пути
        if self._detect_suspicious_paths(path):
            return True, "Suspicious path detected"
        
        # Проверка на подозрительные User-Agent
        if self._detect_suspicious_user_agent(user_agent):
            return True, "Suspicious user agent detected"
        
        # Проверка на частые запросы
        if self._detect_frequent_requests(ip_address):
            return True, "Frequent requests detected"
        
        return False, ""
    
    def _detect_sql_injection(self, request_data: Dict[str, Any]) -> bool:
        """Детекция SQL инъекций"""
        sql_patterns = [
            r'union\s+select', r'drop\s+table', r'delete\s+from',
            r'insert\s+into', r'update\s+set', r'exec\s*\(',
            r'script\s*>', r'<script', r'javascript:',
            r'onload\s*=', r'onerror\s*='
        ]
        
        for key, value in request_data.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
        return False
    
    def _detect_xss(self, request_data: Dict[str, Any]) -> bool:
        """Детекция XSS атак"""
        xss_patterns = [
            r'<script[^>]*>', r'javascript:', r'vbscript:',
            r'onload\s*=', r'onerror\s*=', r'onclick\s*=',
            r'onmouseover\s*=', r'onfocus\s*=', r'onblur\s*='
        ]
        
        for key, value in request_data.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
        return False
    
    def _detect_suspicious_paths(self, path: str) -> bool:
        """Детекция подозрительных путей"""
        suspicious_paths = [
            '/admin', '/wp-admin', '/phpmyadmin', '/.env',
            '/config', '/backup', '/.git', '/.svn',
            '/shell', '/cmd', '/exec', '/eval'
        ]
        
        for suspicious_path in suspicious_paths:
            if suspicious_path in path.lower():
                return True
        return False
    
    def _detect_suspicious_user_agent(self, user_agent: str) -> bool:
        """Детекция подозрительных User-Agent"""
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan',
            'zap', 'burp', 'w3af', 'havij'
        ]
        
        user_agent_lower = user_agent.lower()
        for agent in suspicious_agents:
            if agent in user_agent_lower:
                return True
        return False
    
    def _detect_frequent_requests(self, ip_address: str) -> bool:
        """Детекция частых запросов"""
        current_time = time.time()
        window_start = current_time - 60  # 1 минута
        
        # Очищаем старые записи
        self.activity_patterns[ip_address] = [
            timestamp for timestamp in self.activity_patterns[ip_address]
            if timestamp > window_start
        ]
        
        # Добавляем текущий запрос
        self.activity_patterns[ip_address].append(current_time)
        
        # Проверяем лимит
        if len(self.activity_patterns[ip_address]) > 100:  # 100 запросов в минуту
            return True
        
        return False

class SecurityManager:
    """Главный менеджер безопасности"""
    
    def __init__(self):
        self.password_validator = PasswordValidator()
        self.csrf_protection = CSRFProtection()
        self.rate_limiter = RateLimiter()
        self.ip_whitelist = IPWhitelist()
        self.geolocation_tracker = GeolocationTracker()
        self.audit_logger = SecurityAuditLogger()
        self.activity_detector = SuspiciousActivityDetector()
    
    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Валидация запроса"""
        ip_address = request_data.get('ip_address')
        
        # Проверка белого списка
        if self.ip_whitelist.is_whitelisted(ip_address):
            return True, ""
        
        # Проверка на подозрительную активность
        is_suspicious, reason = self.activity_detector.analyze_request(request_data)
        if is_suspicious:
            self.audit_logger.log_event('suspicious_activity', {
                'ip_address': ip_address,
                'reason': reason,
                'request_data': request_data
            }, 'WARNING')
            return False, reason
        
        # Проверка ограничения скорости
        is_rate_limited, _ = self.rate_limiter.is_rate_limited(
            ip_address, 
            SecurityConfig.RATE_LIMIT_REQUESTS_PER_MINUTE, 
            60
        )
        if is_rate_limited:
            self.audit_logger.log_event('rate_limit_exceeded', {
                'ip_address': ip_address,
                'request_data': request_data
            }, 'WARNING')
            return False, "Rate limit exceeded"
        
        return True, ""
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
        """Логирование события безопасности"""
        self.audit_logger.log_event(event_type, details, severity)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Получение заголовков безопасности"""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self';",
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-CSRF-Token': self.csrf_protection.get_csrf_token()
        }
        return headers

# Декораторы безопасности
def security_required(f):
    """Декоратор для проверки безопасности"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Получаем данные запроса
        request_data = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'path': request.path,
            'method': request.method,
            'args': dict(request.args),
            'form': dict(request.form) if request.form else {},
            'json': request.get_json() if request.is_json else {}
        }
        
        # Валидируем запрос
        security_manager = SecurityManager()
        is_valid, reason = security_manager.validate_request(request_data)
        
        if not is_valid:
            security_manager.log_security_event('request_blocked', {
                'reason': reason,
                'request_data': request_data
            }, 'WARNING')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def csrf_protect(f):
    """Декоратор для защиты от CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not CSRFProtection.validate_csrf_token(token):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(limit: int, window: int = 60):
    """Декоратор для ограничения скорости"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            rate_limiter = RateLimiter()
            
            is_limited, info = rate_limiter.is_rate_limited(identifier, limit, window)
            if is_limited:
                response = jsonify({'error': 'Rate limit exceeded'})
                response.status_code = 429
                response.headers.update(rate_limiter.get_rate_limit_headers(identifier, limit, window))
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def verified_user_required(f):
    """Декоратор для проверки верифицированного пользователя"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_verified:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Глобальный экземпляр менеджера безопасности
security_manager = SecurityManager()

def init_security_headers(app):
    """Инициализация заголовков безопасности"""
    @app.after_request
    def set_security_headers(response):
        """Установка заголовков безопасности"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    
    return app 
    return app