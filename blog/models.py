"""
Алиас для моделей базы данных
Импортирует все модели из models_perfect.py для обратной совместимости
"""

from datetime import datetime

# Импорт всех моделей из идеального модуля
from blog.models_perfect import *

# Экспорт db для совместимости
from blog import db

# Дополнительные импорты для совместимости
from blog.models_perfect import (
    User, Post, Category, Comment, Tag, Bookmark, 
    Notification, UserSession, View, PostLike, CommentLike
)

# Создаем заглушки для несуществующих моделей
class SecurityLog(db.Model):
    """Заглушка для SecurityLog"""
    __tablename__ = 'security_logs'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemMetric(db.Model):
    """Заглушка для SystemMetric"""
    __tablename__ = 'system_metrics'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIContent(db.Model):
    """Заглушка для AIContent"""
    __tablename__ = 'ai_content'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SEOData(db.Model):
    """Заглушка для SEOData"""
    __tablename__ = 'seo_data'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PerformanceMetric(db.Model):
    """Заглушка для PerformanceMetric"""
    __tablename__ = 'performance_metrics'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

__all__ = [
    'User', 'Post', 'Category', 'Comment', 'Tag', 'Bookmark',
    'Notification', 'UserSession', 'View', 'PostLike', 'CommentLike',
    'SecurityLog', 'SystemMetric', 'AIContent', 'SEOData', 'PerformanceMetric',
    'db'
]