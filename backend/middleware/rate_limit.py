"""
Middleware для rate limiting
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import current_app

# Создаем экземпляр Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True,
    swallow_errors=True,
)

def init_limiter(app):
    """Инициализация rate limiter"""
    limiter.init_app(app)
    
    # Настройка Redis если доступен
    if app.config.get('REDIS_URL'):
        limiter._storage_uri = app.config['REDIS_URL']
    
    return limiter

# Декораторы для разных лимитов
strict_limit = limiter.limit("5 per minute")
medium_limit = limiter.limit("20 per minute")
relaxed_limit = limiter.limit("60 per minute")