"""
Модуль инициализации базы данных
Решает проблему циклических зависимостей
"""
from flask_sqlalchemy import SQLAlchemy

# Глобальный объект базы данных
db = SQLAlchemy()

def init_db(app):
    """
    Инициализация базы данных с приложением
    
    Args:
        app: Flask приложение
        
    Returns:
        db: Инициализированный объект базы данных
    """
    db.init_app(app)
    return db

def get_db():
    """
    Получить объект базы данных
    
    Returns:
        db: Объект SQLAlchemy
    """
    return db

def create_all_tables():
    """Создать все таблицы в базе данных"""
    db.create_all()

def drop_all_tables():
    """Удалить все таблицы из базы данных"""
    db.drop_all()

def reset_database():
    """Сбросить базу данных (удалить и создать заново)"""
    drop_all_tables()
    create_all_tables()