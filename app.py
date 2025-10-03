#!/usr/bin/env python3
"""
Ядро блога на Python Flask
Современное веб-приложение с полным функционалом блога
"""

import os
import logging
from dotenv import load_dotenv
from blog import create_app, db
from blog.models import User, Post, Category, Comment

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

# Загружаем переменные окружения
load_dotenv()

# Создаем приложение
app = create_app()

# Контекст для работы с базой данных в shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Post': Post,
        'Category': Category,
        'Comment': Comment
    }

if __name__ == '__main__':
    with app.app_context():
        # Создаем таблицы базы данных
        db.create_all()
        
        # Создаем администратора по умолчанию, если его нет
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@blog.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info("Создан администратор: admin / admin123")
        
        # Инициализация системных компонентов
        try:
            from blog.fault_tolerance import init_fault_tolerance
            from blog.monitoring import monitoring_system
            from blog.seo_optimizer import seo_optimizer
            
            # Запуск системы отказоустойчивости
            init_fault_tolerance()
            logger.info("✅ Система отказоустойчивости запущена")
            
            # Запуск мониторинга
            monitoring_system.start()
            logger.info("✅ Система мониторинга запущена")
            
            # Обновление SEO файлов
            seo_optimizer.update_all_seo()
            logger.info("✅ SEO файлы обновлены")
            
        except Exception as e:
            logger.error(f"⚠️ Ошибка инициализации системных компонентов: {e}")
    
    # Запускаем приложение
    try:
        app.run(
            host=os.environ.get('FLASK_HOST', '0.0.0.0'),
            port=int(os.environ.get('FLASK_PORT', 5000)),
            debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        )
    except KeyboardInterrupt:
        logger.info("🛑 Завершение работы приложения...")
        
        # Корректное завершение системных компонентов
        try:
            from blog.fault_tolerance import shutdown_fault_tolerance
            from blog.monitoring import monitoring_system
            
            shutdown_fault_tolerance()
            monitoring_system.stop()
            logger.info("✅ Системные компоненты корректно завершены")
            
        except Exception as e:
            logger.error(f"⚠️ Ошибка завершения: {e}")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка приложения: {e}")