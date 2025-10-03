"""
Продакшен конфигурация для блога
"""

import os
import secrets
from datetime import timedelta

class ProductionConfig:
    """Конфигурация для продакшена"""
    
    # Основные настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    FLASK_ENV = 'production'
    DEBUG = False
    
    # База данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/blog_prod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # Redis для кэширования
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = "1000 per hour"
    
    # Безопасность
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_ENABLED = True
    
    # Загрузка файлов
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/var/www/blog/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Логирование
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/blog/app.log')
    
    # Email настройки
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Мониторинг
    ENABLE_MONITORING = True
    MONITORING_INTERVAL = 60  # секунд
    
    # ИИ настройки
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    AI_RATE_LIMIT = 100  # запросов в час
    
    # SEO
    BASE_URL = os.environ.get('BASE_URL', 'https://yourdomain.com')
    
    # Бэкапы
    BACKUP_ENABLED = True
    BACKUP_INTERVAL = 24  # часов
    BACKUP_RETENTION_DAYS = 30

class DevelopmentConfig:
    """Конфигурация для разработки"""
    
    SECRET_KEY = 'dev-secret-key'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///blog_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Простое кэширование для разработки
    CACHE_TYPE = 'simple'
    
    # Отключенный rate limiting для разработки
    RATELIMIT_ENABLED = False
    
    # Логирование в консоль
    LOG_LEVEL = 'DEBUG'

class TestingConfig:
    """Конфигурация для тестирования"""
    
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Отключенное кэширование для тестов
    CACHE_TYPE = 'null'
    
    # Отключенный rate limiting для тестов
    RATELIMIT_ENABLED = False
    
    # Отключенные внешние сервисы
    OPENAI_API_KEY = None

# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}