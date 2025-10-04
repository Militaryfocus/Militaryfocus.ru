"""
Инициализация базы данных
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Инициализация базы данных"""
    db.init_app(app)
    migrate.init_app(app, db)
    return db