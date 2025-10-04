"""
Модуль сервисов

Предоставляет централизованный доступ ко всем сервисам системы
"""

# Базовые сервисы
from blog.services.post_service import post_service
from blog.services.user_service import user_service
from blog.services.comment_service import comment_service
from blog.services.category_service import category_service
from blog.services.tag_service import tag_service

# Дополнительные сервисы
from blog.services.notification_service import notification_service
from blog.services.bookmark_service import bookmark_service
from blog.services.view_service import view_service
from blog.services.like_service import like_service
from blog.services.session_service import session_service

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