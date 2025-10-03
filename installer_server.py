#!/usr/bin/env python3
"""
Серверная часть автоустановщика ИИ-блога
Обрабатывает запросы от веб-интерфейса и выполняет реальную установку
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Путь к проекту
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

class InstallerLogger:
    def __init__(self):
        self.logs = []
    
    def add_log(self, message, level='info'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'level': level
        }
        self.logs.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
    
    def get_logs(self):
        return self.logs

logger = InstallerLogger()

def run_command(command, cwd=None):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Команда превысила время выполнения',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

@app.route('/')
def index():
    """Главная страница установщика"""
    with open('installer.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/check-system', methods=['POST'])
def check_system():
    """Проверка системы"""
    logger.add_log('Начинаем проверку системы...', 'info')
    
    checks = []
    
    # Проверка Python
    python_check = run_command('python3 --version')
    if python_check['success']:
        logger.add_log('✅ Python обнаружен', 'success')
        checks.append({'name': 'Python', 'status': 'ok', 'version': python_check['stdout'].strip()})
    else:
        logger.add_log('❌ Python не найден', 'error')
        checks.append({'name': 'Python', 'status': 'error'})
    
    # Проверка pip
    pip_check = run_command('pip3 --version')
    if pip_check['success']:
        logger.add_log('✅ Pip доступен', 'success')
        checks.append({'name': 'Pip', 'status': 'ok'})
    else:
        logger.add_log('❌ Pip не найден', 'error')
        checks.append({'name': 'Pip', 'status': 'error'})
    
    # Проверка Git
    git_check = run_command('git --version')
    if git_check['success']:
        logger.add_log('✅ Git доступен', 'success')
        checks.append({'name': 'Git', 'status': 'ok'})
    else:
        logger.add_log('❌ Git не найден', 'error')
        checks.append({'name': 'Git', 'status': 'error'})
    
    # Проверка места на диске
    disk_usage = shutil.disk_usage(PROJECT_ROOT)
    free_gb = disk_usage.free / (1024**3)
    if free_gb > 1:  # Минимум 1 ГБ
        logger.add_log(f'✅ Достаточно места на диске: {free_gb:.1f} ГБ', 'success')
        checks.append({'name': 'Диск', 'status': 'ok', 'free': f'{free_gb:.1f} ГБ'})
    else:
        logger.add_log(f'❌ Недостаточно места на диске: {free_gb:.1f} ГБ', 'error')
        checks.append({'name': 'Диск', 'status': 'error', 'free': f'{free_gb:.1f} ГБ'})
    
    all_ok = all(check['status'] == 'ok' for check in checks)
    
    if all_ok:
        logger.add_log('🎉 Система готова к установке!', 'success')
    
    return jsonify({
        'success': all_ok,
        'checks': checks,
        'logs': logger.get_logs()
    })

@app.route('/api/install-dependencies', methods=['POST'])
def install_dependencies():
    """Установка зависимостей"""
    logger.add_log('Начинаем установку зависимостей...', 'info')
    
    # Основные зависимости
    dependencies = [
        'flask', 'flask-sqlalchemy', 'flask-migrate', 'flask-login',
        'flask-wtf', 'flask-admin', 'requests', 'numpy', 'scikit-learn',
        'nltk', 'textstat', 'faker', 'openai', 'anthropic',
        'google-generativeai', 'transformers', 'torch',
        'python-slugify', 'markdown', 'bleach', 'psutil',
        'pymorphy3', 'matplotlib', 'seaborn', 'aiohttp', 'backoff'
    ]
    
    installed = []
    failed = []
    
    for dep in dependencies:
        logger.add_log(f'📦 Устанавливаем {dep}...', 'info')
        
        result = run_command(f'pip3 install {dep}')
        
        if result['success']:
            logger.add_log(f'✅ {dep} установлен', 'success')
            installed.append(dep)
        else:
            logger.add_log(f'❌ Ошибка установки {dep}: {result["stderr"]}', 'error')
            failed.append(dep)
    
    # Загрузка данных NLTK
    logger.add_log('📚 Загружаем данные NLTK...', 'info')
    nltk_data = [
        'punkt_tab', 'punkt', 'stopwords', 'averaged_perceptron_tagger',
        'averaged_perceptron_tagger_eng'
    ]
    
    for data in nltk_data:
        result = run_command(f'python3 -c "import nltk; nltk.download(\'{data}\')"')
        if result['success']:
            logger.add_log(f'✅ NLTK {data} загружен', 'success')
        else:
            logger.add_log(f'⚠️ NLTK {data} не загружен', 'warning')
    
    success = len(failed) == 0
    
    if success:
        logger.add_log('🎉 Все зависимости установлены!', 'success')
    else:
        logger.add_log(f'⚠️ {len(failed)} зависимостей не установлено', 'warning')
    
    return jsonify({
        'success': success,
        'installed': installed,
        'failed': failed,
        'logs': logger.get_logs()
    })

@app.route('/api/setup-database', methods=['POST'])
def setup_database():
    """Настройка базы данных"""
    data = request.get_json()
    db_type = data.get('dbType', 'sqlite')
    
    logger.add_log(f'Настраиваем базу данных ({db_type})...', 'info')
    
    try:
        # Импортируем модули блога
        sys.path.append(os.path.join(PROJECT_ROOT, 'blog'))
        from blog import create_app, db
        from blog.models import User, Post, Category, Tag, Comment, View
        
        app = create_app()
        
        with app.app_context():
            # Создаем таблицы
            logger.add_log('📊 Создаем таблицы...', 'info')
            db.create_all()
            logger.add_log('✅ Таблицы созданы', 'success')
            
            # Создаем базовые категории
            logger.add_log('📂 Создаем категории...', 'info')
            categories = [
                'Технологии', 'Наука', 'Общество', 'Бизнес', 'Искусственный интеллект'
            ]
            
            for cat_name in categories:
                existing = Category.query.filter_by(name=cat_name).first()
                if not existing:
                    category = Category(name=cat_name)
                    db.session.add(category)
            
            db.session.commit()
            logger.add_log('✅ Категории созданы', 'success')
            
            logger.add_log('🎉 База данных настроена!', 'success')
            
            return jsonify({
                'success': True,
                'logs': logger.get_logs()
            })
            
    except Exception as e:
        logger.add_log(f'❌ Ошибка настройки БД: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': logger.get_logs()
        })

@app.route('/api/setup-ai', methods=['POST'])
def setup_ai():
    """Настройка ИИ сервисов"""
    data = request.get_json()
    
    logger.add_log('Настраиваем ИИ сервисы...', 'info')
    
    try:
        # Создаем файл конфигурации
        config = {
            'openai_api_key': data.get('openaiKey', ''),
            'anthropic_api_key': data.get('anthropicKey', ''),
            'google_api_key': data.get('googleKey', ''),
            'local_models_enabled': True,
            'cache_enabled': True
        }
        
        config_file = os.path.join(PROJECT_ROOT, 'ai_config.json')
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.add_log('📝 Конфигурация ИИ сохранена', 'success')
        
        # Проверяем доступность локальных моделей
        logger.add_log('🏠 Проверяем локальные модели...', 'info')
        
        # Тестируем импорт ИИ модулей
        sys.path.append(os.path.join(PROJECT_ROOT, 'blog'))
        try:
            from blog.advanced_content_generator import AdvancedContentGenerator
            from blog.ai_provider_manager import AIProviderManager
            
            generator = AdvancedContentGenerator()
            provider_manager = AIProviderManager()
            
            logger.add_log('✅ Локальные модели загружены', 'success')
            
        except Exception as e:
            logger.add_log(f'⚠️ Локальные модели: {str(e)}', 'warning')
        
        logger.add_log('🎉 ИИ сервисы настроены!', 'success')
        
        return jsonify({
            'success': True,
            'logs': logger.get_logs()
        })
        
    except Exception as e:
        logger.add_log(f'❌ Ошибка настройки ИИ: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': logger.get_logs()
        })

@app.route('/api/create-admin', methods=['POST'])
def create_admin():
    """Создание администратора"""
    data = request.get_json()
    
    username = data.get('username', 'admin')
    email = data.get('email', 'admin@example.com')
    password = data.get('password', '')
    
    if not password:
        return jsonify({
            'success': False,
            'error': 'Пароль не может быть пустым',
            'logs': logger.get_logs()
        })
    
    logger.add_log(f'Создаем администратора: {username}', 'info')
    
    try:
        sys.path.append(os.path.join(PROJECT_ROOT, 'blog'))
        from blog import create_app, db
        from blog.models import User
        
        app = create_app()
        
        with app.app_context():
            # Проверяем, существует ли пользователь
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                logger.add_log(f'⚠️ Пользователь {username} уже существует', 'warning')
                return jsonify({
                    'success': True,
                    'message': 'Пользователь уже существует',
                    'logs': logger.get_logs()
                })
            
            # Создаем нового пользователя
            user = User(
                username=username,
                email=email,
                is_admin=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.add_log('✅ Администратор создан', 'success')
            logger.add_log('🎉 Учетная запись готова!', 'success')
            
            return jsonify({
                'success': True,
                'logs': logger.get_logs()
            })
            
    except Exception as e:
        logger.add_log(f'❌ Ошибка создания админа: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': logger.get_logs()
        })

@app.route('/api/finalize-setup', methods=['POST'])
def finalize_setup():
    """Финальная настройка"""
    logger.add_log('Завершаем установку...', 'info')
    
    try:
        # Создаем файл конфигурации
        config = {
            'installation_date': datetime.now().isoformat(),
            'version': '1.0.0',
            'features': [
                'advanced_content_generation',
                'ai_provider_management',
                'seo_optimization',
                'content_personalization',
                'monitoring_analytics'
            ]
        }
        
        config_file = os.path.join(PROJECT_ROOT, 'installation_config.json')
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.add_log('📝 Конфигурация сохранена', 'success')
        
        # Запускаем тесты
        logger.add_log('🧪 Запускаем тесты...', 'info')
        
        test_result = run_command('python3 production_test.py')
        if test_result['success']:
            logger.add_log('✅ Все тесты пройдены', 'success')
        else:
            logger.add_log(f'⚠️ Некоторые тесты провалены: {test_result["stderr"]}', 'warning')
        
        # Создаем README
        readme_content = f"""# 🤖 ИИ-блог - Установка завершена

## 🎉 Система успешно установлена!

**Дата установки:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Версия:** 1.0.0

## 🚀 Быстрый старт

### Запуск сервера:
```bash
python3 app.py
```

### Доступные адреса:
- **Главная страница:** http://localhost:5000
- **ИИ панель:** http://localhost:5000/ai-dashboard
- **Админ панель:** http://localhost:5000/admin

### Командная строка:
```bash
# Генерация контента
python3 ai_manager.py advanced-generate 5 --content-type how_to_guide

# SEO анализ
python3 ai_manager.py seo-analyze 1

# Статус системы
python3 ai_manager.py system-status
```

## 📚 Документация

- `ENHANCED_SYSTEM_GUIDE.md` - Подробное руководство
- `AI_SYSTEM_DOCUMENTATION.md` - Техническая документация

## 🔧 Настройка

Для использования внешних ИИ сервисов настройте API ключи в файле `ai_config.json`.

## 🆘 Поддержка

При возникновении проблем проверьте логи в файле `blog_system.log`.
"""
        
        with open(os.path.join(PROJECT_ROOT, 'INSTALLATION_COMPLETE.md'), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.add_log('📚 Документация создана', 'success')
        logger.add_log('🎉 Установка завершена!', 'success')
        
        return jsonify({
            'success': True,
            'logs': logger.get_logs(),
            'urls': {
                'main': 'http://localhost:5000',
                'ai_dashboard': 'http://localhost:5000/ai-dashboard',
                'admin': 'http://localhost:5000/admin'
            }
        })
        
    except Exception as e:
        logger.add_log(f'❌ Ошибка финализации: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': logger.get_logs()
        })

@app.route('/api/start-server', methods=['POST'])
def start_server():
    """Запуск сервера"""
    logger.add_log('🚀 Запускаем сервер...', 'info')
    
    try:
        # Запускаем сервер в фоновом режиме
        result = run_command('python3 app.py &')
        
        if result['success']:
            logger.add_log('✅ Сервер запущен на http://localhost:5000', 'success')
            return jsonify({
                'success': True,
                'message': 'Сервер запущен',
                'logs': logger.get_logs()
            })
        else:
            logger.add_log(f'❌ Ошибка запуска сервера: {result["stderr"]}', 'error')
            return jsonify({
                'success': False,
                'error': result['stderr'],
                'logs': logger.get_logs()
            })
            
    except Exception as e:
        logger.add_log(f'❌ Ошибка запуска: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': logger.get_logs()
        })

if __name__ == '__main__':
    print("🚀 Запуск автоустановщика ИИ-блога...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)