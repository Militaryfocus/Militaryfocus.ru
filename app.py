#!/usr/bin/env python3
"""
Ядро блога на Python Flask
Современное веб-приложение с полным функционалом блога
"""

import os
from dotenv import load_dotenv
from blog import create_app, db
from blog.models import User, Post, Category, Comment

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
            import secrets
            
            # Генерируем безопасный пароль или используем из переменных окружения
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if not admin_password:
                admin_password = secrets.token_urlsafe(16)
                print(f"⚠️  ВНИМАНИЕ: Сгенерирован случайный пароль администратора!")
                print(f"🔑 Сохраните этот пароль: {admin_password}")
                print("💡 Для продакшена установите переменную ADMIN_PASSWORD")
            
            admin = User(
                username='admin',
                email=os.environ.get('ADMIN_EMAIL', 'admin@blog.com'),
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("✅ Создан администратор: admin")
        
        # Инициализация системных компонентов
        try:
            from blog.fault_tolerance import init_fault_tolerance
            from blog.monitoring import monitoring_system
            from blog.seo_optimizer import seo_optimizer
            
            # Запуск системы отказоустойчивости
            init_fault_tolerance()
            print("✅ Система отказоустойчивости запущена")
            
            # Запуск мониторинга
            monitoring_system.start()
            print("✅ Система мониторинга запущена")
            
            # Обновление SEO файлов
            seo_optimizer.update_all_seo()
            print("✅ SEO файлы обновлены")
            
        except Exception as e:
            print(f"⚠️ Ошибка инициализации системных компонентов: {e}")
    
    # Запускаем приложение
    try:
        # Безопасная конфигурация запуска
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        flask_env = os.environ.get('FLASK_ENV', 'development')
        
        # Предупреждение о debug режиме
        if debug_mode and flask_env == 'production':
            print("⚠️  ВНИМАНИЕ: Debug режим включен в продакшене!")
            print("🔒 Установите FLASK_DEBUG=False для продакшена")
        
        # HTTPS конфигурация для продакшена
        if flask_env == 'production':
            ssl_cert = os.environ.get('SSL_CERT_PATH')
            ssl_key = os.environ.get('SSL_KEY_PATH')
            
            if ssl_cert and ssl_key:
                import ssl
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                ssl_context.load_cert_chain(ssl_cert, ssl_key)
                print("🔒 Запуск с HTTPS сертификатом")
                app.run(host=host, port=443, ssl_context=ssl_context, debug=debug_mode)
            else:
                print("⚠️  ВНИМАНИЕ: Продакшен без HTTPS!")
                print("🔒 Установите SSL_CERT_PATH и SSL_KEY_PATH для безопасности")
                app.run(host=host, port=port, debug=debug_mode)
        else:
            app.run(host=host, port=port, debug=debug_mode)
    except KeyboardInterrupt:
        print("\n🛑 Завершение работы приложения...")
        
        # Корректное завершение системных компонентов
        try:
            from blog.fault_tolerance import shutdown_fault_tolerance
            from blog.monitoring import monitoring_system
            
            shutdown_fault_tolerance()
            monitoring_system.stop()
            print("✅ Системные компоненты корректно завершены")
            
        except Exception as e:
            print(f"⚠️ Ошибка завершения: {e}")
    except Exception as e:
        print(f"❌ Критическая ошибка приложения: {e}")