"""
Конфигурация приложения
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin

class AppConfig:
    """Конфигурация приложения"""
    
    @staticmethod
    def create_app(config_name=None):
        """Фабрика приложений Flask"""
        app = Flask(__name__)
        
        # Конфигурация
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
        if not app.config['SECRET_KEY']:
            raise ValueError("SECRET_KEY environment variable is required")
        
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///blog.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER') or 'static/uploads'
        app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
        app.config['POSTS_PER_PAGE'] = int(os.environ.get('POSTS_PER_PAGE', 5))
        app.config['COMMENTS_PER_PAGE'] = int(os.environ.get('COMMENTS_PER_PAGE', 10))
        
        # Настройки безопасности
        app.config['CSRF_ENABLED'] = os.environ.get('CSRF_ENABLED', 'True').lower() == 'true'
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
        app.config['SESSION_COOKIE_HTTPONLY'] = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
        app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
        
        # Инициализация расширений
        from blog import db, login_manager, migrate
        db.init_app(app)
        login_manager.init_app(app)
        migrate.init_app(app, db)
        
        # Инициализация безопасных заголовков
        from blog.security_perfect import init_security_headers
        init_security_headers(app)
        
        # Настройка Flask-Login
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            from blog.models import User
            return User.query.get(int(user_id))
        
        # Контекстные процессоры
        @app.context_processor
        def inject_categories():
            from blog.models import Category
            categories = Category.query.all()
            return dict(categories=categories)
        
        @app.context_processor
        def inject_seo_meta():
            """Автоматическое добавление SEO мета-тегов"""
            from blog.advanced_seo import advanced_seo_optimizer
            from flask import request
            
            # Получение мета-тегов для текущей страницы
            meta_tags = {}
            
            try:
                # Определение типа страницы
                if request.endpoint == 'blog.post_detail':
                    # Для страниц постов
                    from blog.models import Post
                    slug = request.view_args.get('slug')
                    if slug:
                        post = Post.query.filter_by(slug=slug, is_published=True).first()
                        if post:
                            meta_tags = advanced_seo_optimizer.meta_generator.generate_post_meta(post)
                
                elif request.endpoint == 'blog.category_posts':
                    # Для страниц категорий
                    from blog.models import Category
                    slug = request.view_args.get('slug')
                    if slug:
                        category = Category.query.filter_by(slug=slug).first()
                        if category:
                            meta_tags = advanced_seo_optimizer.meta_generator.generate_category_meta(category)
                
                elif request.endpoint == 'main.index':
                    # Для главной страницы
                    meta_tags = advanced_seo_optimizer.meta_generator.generate_home_meta()
                
            except Exception as e:
                # В случае ошибки возвращаем базовые мета-теги
                meta_tags = {
                    'title': 'МойБлог - Современный блог с ИИ контентом',
                    'description': 'Современный блог на Python Flask с автоматическим наполнением контентом',
                    'keywords': 'блог, python, flask, искусственный интеллект'
                }
            
            return dict(seo_meta=meta_tags)
        
        return app