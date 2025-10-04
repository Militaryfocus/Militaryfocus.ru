#!/usr/bin/env python3
"""
Веб-установщик системы блога
Запустите этот файл для первоначальной настройки через браузер
"""
import os
import sys
import secrets
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем временное Flask приложение для установки
install_app = Flask(__name__)
install_app.secret_key = secrets.token_hex(32)
install_app.template_folder = 'blog/templates/install'
install_app.static_folder = 'blog/static'

# Проверка, установлена ли система
def is_installed():
    """Проверка, установлена ли система"""
    return os.path.exists('.env') and os.path.exists('instance/blog.db')

def check_requirements():
    """Проверка системных требований"""
    requirements = {
        'python_version': sys.version_info >= (3, 8),
        'pip': os.system('pip --version > /dev/null 2>&1') == 0,
        'write_permission': os.access('.', os.W_OK),
        'dependencies': True
    }
    
    # Проверка основных зависимостей
    try:
        import flask
        import sqlalchemy
        import flask_login
    except ImportError:
        requirements['dependencies'] = False
    
    return requirements

def create_env_file(config):
    """Создание .env файла"""
    env_content = f"""# Конфигурация блога
# Сгенерировано установщиком

# Основные настройки
SECRET_KEY={config['secret_key']}
FLASK_ENV={config['environment']}
FLASK_DEBUG={'True' if config['environment'] == 'development' else 'False'}

# База данных
DATABASE_URL={config['database_url']}

# Сайт
SITE_NAME={config['site_name']}
SITE_URL={config['site_url']}
SITE_DESCRIPTION={config['site_description']}

# Администратор
ADMIN_EMAIL={config['admin_email']}

# Email настройки (опционально)
MAIL_SERVER={config.get('mail_server', '')}
MAIL_PORT={config.get('mail_port', '587')}
MAIL_USE_TLS={config.get('mail_use_tls', 'True')}
MAIL_USERNAME={config.get('mail_username', '')}
MAIL_PASSWORD={config.get('mail_password', '')}

# AI провайдеры (опционально)
OPENAI_API_KEY={config.get('openai_api_key', '')}
ANTHROPIC_API_KEY={config.get('anthropic_api_key', '')}
GOOGLE_API_KEY={config.get('google_api_key', '')}

# SEO
GOOGLE_ANALYTICS_ID={config.get('google_analytics_id', '')}
YANDEX_METRIKA_ID={config.get('yandex_metrika_id', '')}

# Безопасность
ALLOWED_HOSTS={config.get('allowed_hosts', 'localhost,127.0.0.1')}
SESSION_COOKIE_SECURE={'True' if config['site_url'].startswith('https') else 'False'}
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Загрузки
UPLOAD_FOLDER=blog/static/uploads
MAX_CONTENT_LENGTH=16777216
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info(".env файл создан")

def create_database(admin_data):
    """Создание базы данных и администратора"""
    try:
        # Импортируем приложение
        from blog import create_app
        from blog.database import db
        from blog.models import User, Category
        
        # Создаем приложение
        app = create_app()
        
        with app.app_context():
            # Создаем таблицы
            db.create_all()
            logger.info("База данных создана")
            
            # Создаем администратора
            admin = User(
                username=admin_data['username'],
                email=admin_data['email'],
                first_name=admin_data.get('first_name', ''),
                last_name=admin_data.get('last_name', ''),
                is_admin=True,
                is_verified=True
            )
            admin.set_password(admin_data['password'])
            db.session.add(admin)
            
            # Создаем базовые категории
            categories = [
                {'name': 'Новости', 'slug': 'news', 'description': 'Последние новости и события', 'color': '#dc3545'},
                {'name': 'Технологии', 'slug': 'tech', 'description': 'IT и технологические тренды', 'color': '#007bff'},
                {'name': 'Образование', 'slug': 'education', 'description': 'Обучающие материалы', 'color': '#28a745'},
                {'name': 'Общее', 'slug': 'general', 'description': 'Разное', 'color': '#6c757d'},
            ]
            
            for cat_data in categories:
                category = Category(**cat_data)
                db.session.add(category)
            
            db.session.commit()
            logger.info("Администратор и категории созданы")
            
            return True
            
    except Exception as e:
        logger.error(f"Ошибка создания БД: {e}")
        return False

@install_app.route('/')
def index():
    """Главная страница установщика"""
    if is_installed():
        return render_template('install/already_installed.html')
    
    # Проверяем требования
    requirements = check_requirements()
    all_ok = all(requirements.values())
    
    return render_template('install/index.html', 
                         requirements=requirements,
                         all_ok=all_ok)

@install_app.route('/step1', methods=['GET', 'POST'])
def step1():
    """Шаг 1: Основные настройки"""
    if is_installed():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        session['config'] = {
            'site_name': request.form.get('site_name'),
            'site_url': request.form.get('site_url'),
            'site_description': request.form.get('site_description'),
            'environment': request.form.get('environment', 'production'),
            'secret_key': secrets.token_hex(32)
        }
        return redirect(url_for('step2'))
    
    return render_template('install/step1.html')

@install_app.route('/step2', methods=['GET', 'POST'])
def step2():
    """Шаг 2: База данных"""
    if is_installed() or 'config' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        db_type = request.form.get('db_type', 'sqlite')
        
        if db_type == 'sqlite':
            session['config']['database_url'] = 'sqlite:///blog.db'
        else:
            # PostgreSQL или MySQL
            db_config = {
                'host': request.form.get('db_host', 'localhost'),
                'port': request.form.get('db_port', '5432' if db_type == 'postgresql' else '3306'),
                'name': request.form.get('db_name'),
                'user': request.form.get('db_user'),
                'password': request.form.get('db_password')
            }
            
            if db_type == 'postgresql':
                session['config']['database_url'] = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
            else:
                session['config']['database_url'] = f"mysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        
        return redirect(url_for('step3'))
    
    return render_template('install/step2.html')

@install_app.route('/step3', methods=['GET', 'POST'])
def step3():
    """Шаг 3: Администратор"""
    if is_installed() or 'config' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        session['admin'] = {
            'username': request.form.get('admin_username'),
            'email': request.form.get('admin_email'),
            'password': request.form.get('admin_password'),
            'first_name': request.form.get('first_name', ''),
            'last_name': request.form.get('last_name', '')
        }
        
        session['config']['admin_email'] = session['admin']['email']
        
        return redirect(url_for('step4'))
    
    return render_template('install/step3.html')

@install_app.route('/step4', methods=['GET', 'POST'])
def step4():
    """Шаг 4: Дополнительные настройки"""
    if is_installed() or 'config' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Email настройки
        session['config']['mail_server'] = request.form.get('mail_server', '')
        session['config']['mail_port'] = request.form.get('mail_port', '587')
        session['config']['mail_username'] = request.form.get('mail_username', '')
        session['config']['mail_password'] = request.form.get('mail_password', '')
        
        # AI настройки
        session['config']['openai_api_key'] = request.form.get('openai_api_key', '')
        session['config']['anthropic_api_key'] = request.form.get('anthropic_api_key', '')
        session['config']['google_api_key'] = request.form.get('google_api_key', '')
        
        # SEO настройки
        session['config']['google_analytics_id'] = request.form.get('google_analytics_id', '')
        session['config']['yandex_metrika_id'] = request.form.get('yandex_metrika_id', '')
        
        return redirect(url_for('install'))
    
    return render_template('install/step4.html')

@install_app.route('/install')
def install():
    """Выполнение установки"""
    if is_installed() or 'config' not in session or 'admin' not in session:
        return redirect(url_for('index'))
    
    errors = []
    
    # Создаем .env файл
    try:
        create_env_file(session['config'])
    except Exception as e:
        errors.append(f"Ошибка создания .env: {str(e)}")
    
    # Создаем директории
    try:
        os.makedirs('instance', exist_ok=True)
        os.makedirs('blog/static/uploads/avatars', exist_ok=True)
        os.makedirs('blog/static/uploads/posts', exist_ok=True)
        os.makedirs('blog/static/uploads/temp', exist_ok=True)
        logger.info("Директории созданы")
    except Exception as e:
        errors.append(f"Ошибка создания директорий: {str(e)}")
    
    # Создаем базу данных
    if not errors:
        if create_database(session['admin']):
            # Очищаем сессию
            session.clear()
            return render_template('install/success.html')
        else:
            errors.append("Ошибка создания базы данных")
    
    return render_template('install/error.html', errors=errors)

@install_app.route('/remove-installer')
def remove_installer():
    """Удаление установщика"""
    try:
        os.remove('install.py')
        flash('Установщик удален', 'success')
    except Exception as e:
        flash(f'Ошибка удаления установщика: {e}', 'error')
    
    return redirect('/')

if __name__ == '__main__':
    # Создаем директорию для шаблонов установщика
    os.makedirs('blog/templates/install', exist_ok=True)
    
    print("""
╔══════════════════════════════════════════════════════╗
║          УСТАНОВЩИК MILITARY FOCUS BLOG              ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Откройте в браузере: http://localhost:5001         ║
║                                                      ║
║  Следуйте инструкциям для установки системы         ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
    """)
    
    install_app.run(host='0.0.0.0', port=5001, debug=True)