#!/usr/bin/env python3
"""
Улучшенный запуск веб-сервера с оптимизациями
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blog_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_optimized_app():
    """Создание оптимизированного приложения"""
    try:
        from blog import create_app, db
        from blog.models import User, Post, Category, Comment
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        
        with app.app_context():
            # Создаем таблицы
            db.create_all()
            logger.info("✅ База данных инициализирована")
            
            # Создаем администратора
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123')
                )
                admin.is_admin = True
                db.session.add(admin)
                logger.info("✅ Администратор создан")
            
            # Создаем тестовую категорию
            category = Category.query.filter_by(slug='technology').first()
            if not category:
                category = Category(
                    name='Технологии',
                    slug='technology',
                    description='Статьи о технологиях и программировании',
                    color='#007bff'
                )
                db.session.add(category)
                logger.info("✅ Тестовая категория создана")
            
            # Создаем тестовый пост
            post = Post.query.filter_by(slug='welcome-post').first()
            if not post:
                post = Post(
                    title='Добро пожаловать в блог!',
                    slug='welcome-post',
                    content='''# Добро пожаловать в наш блог!

Это современный блог на Python Flask с поддержкой ИИ-генерации контента.

## Возможности блога:

- 📝 **Создание постов** с поддержкой Markdown
- 🤖 **ИИ-генерация контента** с помощью OpenAI, Anthropic и других провайдеров
- 🔍 **SEO оптимизация** с автоматическими мета-тегами
- 📊 **Мониторинг системы** в реальном времени
- 🔒 **Безопасность** с защитой от CSRF и других атак
- 📱 **Адаптивный дизайн** для всех устройств

## Технологии:

- **Backend**: Python Flask, SQLAlchemy
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **ИИ**: OpenAI GPT, Anthropic Claude, локальные модели
- **База данных**: SQLite (можно заменить на PostgreSQL/MySQL)
- **Безопасность**: Flask-WTF, Werkzeug, безопасные заголовки

Начните создавать свой контент прямо сейчас!''',
                    excerpt='Приветственный пост в современном блоге на Python Flask',
                    author_id=admin.id,
                    category_id=category.id,
                    is_published=True
                )
                db.session.add(post)
                logger.info("✅ Тестовый пост создан")
            
            db.session.commit()
            logger.info("✅ Тестовые данные загружены")
        
        return app
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания приложения: {e}")
        raise

def run_development_server():
    """Запуск сервера разработки"""
    try:
        app = create_optimized_app()
        
        # Настройки для разработки
        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        
        logger.info(f"🚀 Запуск сервера на http://{host}:{port}")
        logger.info(f"🔧 Режим отладки: {debug}")
        logger.info(f"👤 Админ: admin / admin123")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)

def run_production_server():
    """Запуск продакшен сервера с Gunicorn"""
    try:
        app = create_optimized_app()
        
        # Настройки для продакшена
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', 80))
        workers = int(os.environ.get('GUNICORN_WORKERS', 4))
        
        logger.info(f"🚀 Запуск продакшен сервера на {host}:{port}")
        logger.info(f"👥 Количество воркеров: {workers}")
        
        # Импортируем Gunicorn
        from gunicorn.app.wsgiapp import WSGIApplication
        
        class StandaloneApplication(WSGIApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                config = {
                    'bind': f'{host}:{port}',
                    'workers': workers,
                    'worker_class': 'sync',
                    'worker_connections': 1000,
                    'max_requests': 1000,
                    'max_requests_jitter': 50,
                    'timeout': 30,
                    'keepalive': 2,
                    'preload_app': True,
                    'accesslog': 'access.log',
                    'errorlog': 'error.log',
                    'loglevel': 'info'
                }
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)
        
        StandaloneApplication(app).run()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска продакшен сервера: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Проверяем режим запуска
    if len(sys.argv) > 1 and sys.argv[1] == '--production':
        run_production_server()
    else:
        run_development_server()