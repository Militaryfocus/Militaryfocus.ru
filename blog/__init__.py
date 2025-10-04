"""
Инициализация Flask приложения блога
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
admin = Admin()

def create_app(config_name=None):
    """Фабрика приложений Flask"""
    from blog.config import AppConfig, BlueprintConfig
    
    app = AppConfig.create_app(config_name)
    BlueprintConfig.register_blueprints(app)
    
    return app