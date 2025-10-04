"""
Backend API для блога
"""
import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from datetime import timedelta

from config.config import Config
from config.database import db, migrate

# Инициализация расширений
ma = Marshmallow()
jwt = JWTManager()

def create_app(config_class=Config):
    """Фабрика приложения"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)
    
    # CORS настройка
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Регистрация blueprints
    from api import auth, posts, users, categories, comments, tags, uploads
    
    app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
    app.register_blueprint(posts.bp, url_prefix='/api/v1/posts')
    app.register_blueprint(users.bp, url_prefix='/api/v1/users')
    app.register_blueprint(categories.bp, url_prefix='/api/v1/categories')
    app.register_blueprint(comments.bp, url_prefix='/api/v1/comments')
    app.register_blueprint(tags.bp, url_prefix='/api/v1/tags')
    app.register_blueprint(uploads.bp, url_prefix='/api/v1/uploads')
    
    # Обработчики ошибок
    from api.errors import register_error_handlers
    register_error_handlers(app)
    
    # Здоровье API
    @app.route('/api/v1/health')
    def health_check():
        return {'status': 'healthy', 'version': '1.0.0'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)