"""
Rate limiting для защиты от спама и DDoS
"""
import os
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from datetime import datetime, timedelta

# Инициализация rate limiter
def get_limiter(app=None):
    """Создает и настраивает rate limiter"""
    
    # Функция для получения ключа (IP адрес или user_id)
    def get_request_key():
        # Если пользователь авторизован, используем его ID
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            return f"user:{current_user.id}"
        
        # Иначе используем IP адрес
        return get_remote_address()
    
    # Настройки хранилища
    storage_uri = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    limiter = Limiter(
        app=app,
        key_func=get_request_key,
        default_limits=["1000 per hour", "100 per minute"],
        storage_uri=storage_uri,
        strategy="fixed-window",
        headers_enabled=True
    )
    
    return limiter

# Декораторы для разных типов ограничений
class RateLimiters:
    """Предустановленные ограничения для разных действий"""
    
    # Строгие ограничения для регистрации
    REGISTER = "3 per hour;10 per day"
    
    # Ограничения для входа
    LOGIN = "5 per minute;20 per hour"
    
    # Ограничения для создания контента
    CREATE_POST = "10 per hour;50 per day"
    CREATE_COMMENT = "20 per hour;100 per day"
    
    # Ограничения для API
    API_DEFAULT = "60 per minute;1000 per hour"
    API_SEARCH = "30 per minute;300 per hour"
    
    # Ограничения для отправки email
    SEND_EMAIL = "5 per hour;20 per day"
    
    # Ограничения для загрузки файлов
    FILE_UPLOAD = "10 per hour;50 per day"


class RateLimitManager:
    """Менеджер для управления rate limiting"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.prefix = "ratelimit:"
    
    def check_rate_limit(self, key, limit, window):
        """
        Проверяет, не превышен ли лимит
        
        Args:
            key: Уникальный ключ (например, IP или user_id)
            limit: Максимальное количество запросов
            window: Временное окно в секундах
            
        Returns:
            tuple: (allowed, remaining, reset_time)
        """
        if not self.redis_client:
            return True, limit, None
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        
        # Ключ для хранения в Redis
        redis_key = f"{self.prefix}{key}:{window}"
        
        try:
            # Удаляем старые записи
            self.redis_client.zremrangebyscore(
                redis_key, 
                0, 
                window_start.timestamp()
            )
            
            # Считаем текущее количество запросов
            current_count = self.redis_client.zcard(redis_key)
            
            if current_count >= limit:
                # Лимит превышен
                # Получаем время сброса
                oldest = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    reset_time = datetime.fromtimestamp(oldest[0][1]) + timedelta(seconds=window)
                else:
                    reset_time = now + timedelta(seconds=window)
                
                return False, 0, reset_time
            
            # Добавляем новый запрос
            self.redis_client.zadd(redis_key, {str(now.timestamp()): now.timestamp()})
            
            # Устанавливаем TTL
            self.redis_client.expire(redis_key, window)
            
            remaining = limit - current_count - 1
            reset_time = now + timedelta(seconds=window)
            
            return True, remaining, reset_time
            
        except Exception as e:
            # В случае ошибки разрешаем запрос
            print(f"Rate limit error: {e}")
            return True, limit, None
    
    def get_user_limits(self, user_id):
        """Получает текущие лимиты пользователя"""
        limits = {}
        
        if not self.redis_client:
            return limits
        
        try:
            # Получаем все ключи для пользователя
            pattern = f"{self.prefix}user:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                window = int(key_str.split(':')[-1])
                count = self.redis_client.zcard(key)
                ttl = self.redis_client.ttl(key)
                
                limits[window] = {
                    'count': count,
                    'ttl': ttl
                }
            
            return limits
            
        except Exception as e:
            print(f"Error getting user limits: {e}")
            return {}
    
    def reset_user_limits(self, user_id):
        """Сбрасывает все лимиты для пользователя"""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"{self.prefix}user:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
            
            return True
            
        except Exception as e:
            print(f"Error resetting user limits: {e}")
            return False


# Middleware для добавления заголовков rate limit
def add_rate_limit_headers(response, allowed, remaining, reset_time):
    """Добавляет заголовки с информацией о rate limiting"""
    response.headers['X-RateLimit-Limit'] = str(allowed)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    
    if reset_time:
        response.headers['X-RateLimit-Reset'] = str(int(reset_time.timestamp()))
    
    return response