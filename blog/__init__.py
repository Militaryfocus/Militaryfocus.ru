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
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app)
    
    # Инициализация безопасных заголовков
    from blog.security import init_security_headers
    init_security_headers(app)
    
    # Настройка Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from blog.models import User
        return User.query.get(int(user_id))
    
    # Регистрация Blueprint'ов
    from blog.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from blog.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from blog.routes.blog import bp as blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    from blog.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin', name='blog_admin')
    
    from blog.routes.ai_admin import bp as ai_admin_bp
    app.register_blueprint(ai_admin_bp, url_prefix='/ai')
    
    from blog.routes.system_admin import bp as system_admin_bp
    app.register_blueprint(system_admin_bp, url_prefix='/system')
    
    # Регистрация API
    from blog.routes.api import api_bp
    app.register_blueprint(api_bp)
    
    # Настройка Flask-Admin
    class SecureModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin
        
        def inaccessible_callback(self, name, **kwargs):
            from flask import redirect, url_for, flash
            flash('У вас нет прав доступа к админ-панели.', 'error')
            return redirect(url_for('main.index'))
    
    # Добавление моделей в админ-панель
    with app.app_context():
        from blog.models import User, Post, Category, Comment
        admin.add_view(SecureModelView(User, db.session, name='Пользователи'))
        admin.add_view(SecureModelView(Post, db.session, name='Посты'))
        admin.add_view(SecureModelView(Category, db.session, name='Категории'))
        admin.add_view(SecureModelView(Comment, db.session, name='Комментарии'))
    
    # Контекстные процессоры
    @app.context_processor
    def inject_categories():
        from blog.models import Category
        categories = Category.query.all()
        return dict(categories=categories)
    
    return app