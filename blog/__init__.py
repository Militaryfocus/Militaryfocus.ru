"""
Инициализация Flask приложения блога
"""

import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
admin = Admin()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name=None):
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    
    # Загружаем конфигурацию
    if config_name:
        from config import config
        app.config.from_object(config[config_name])
    else:
        # Определяем конфигурацию по переменной окружения
        config_name = os.environ.get('FLASK_ENV', 'development')
        from config import config
        app.config.from_object(config[config_name])
    
    # Дополнительные настройки безопасности для продакшена
    if config_name == 'production':
        # Настройки безопасности для продакшена
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 часа
        
        # Настройки для HTTPS
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        
        # Настройки для прокси
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
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
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from blog.routes.ai_admin import bp as ai_admin_bp
    app.register_blueprint(ai_admin_bp, url_prefix='/ai')
    
    from blog.routes.system_admin import bp as system_admin_bp
    app.register_blueprint(system_admin_bp, url_prefix='/system')
    
    from blog.routes.autonomous_ai import bp as autonomous_ai_bp
    app.register_blueprint(autonomous_ai_bp, url_prefix='/autonomous')
    
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