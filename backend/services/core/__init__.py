"""
Модуль сервисов

Предоставляет централизованный доступ ко всем сервисам системы
"""

# Базовые сервисы
from services.core.post_service import post_service
from services.core.user_service import user_service
from services.core.comment_service import comment_service
from services.core.category_service import category_service
from services.core.tag_service import tag_service

# Дополнительные сервисы
from services.core.notification_service import notification_service
from services.core.bookmark_service import bookmark_service
from services.core.view_service import view_service
from services.core.like_service import like_service
from services.core.session_service import session_service

# Экспортируем все сервисы
__all__ = [
    'post_service',
    'user_service',
    'comment_service',
    'category_service',
    'tag_service',
    'notification_service',
    'bookmark_service',
    'view_service',
    'like_service',
    'session_service'
]

# Словарь для удобного доступа к сервисам
services = {
    'post': post_service,
    'user': user_service,
    'comment': comment_service,
    'category': category_service,
    'tag': tag_service,
    'notification': notification_service,
    'bookmark': bookmark_service,
    'view': view_service,
    'like': like_service,
    'session': session_service
}

def get_service(name: str):
    """
    Получить сервис по имени
    
    Args:
        name: Имя сервиса
        
    Returns:
        Экземпляр сервиса или None
    """
    return services.get(name)