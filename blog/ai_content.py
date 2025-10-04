"""
Алиас для AI контента
Импортирует все классы из ai_content_perfect.py для обратной совместимости
"""

# Импорт всех классов из идеального модуля
from blog.ai_content_perfect import *

# Экспорт основных классов для совместимости
__all__ = [
    'AIContentGenerator', 'ContentScheduler', 'populate_blog_with_ai_content'
]