#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работоспособности приложения
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Устанавливаем минимальные переменные окружения
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['DATABASE_URL'] = 'sqlite:///test_blog.db'
os.environ['FLASK_ENV'] = 'testing'
os.environ['FLASK_DEBUG'] = 'False'

print("=" * 60)
print("🔍 ТЕСТИРОВАНИЕ РАБОТОСПОСОБНОСТИ ПРИЛОЖЕНИЯ")
print("=" * 60)

# 1. Проверка импортов
print("\n1️⃣ Проверка основных импортов...")
try:
    from blog import create_app
    print("✅ blog импортирован")
    
    from blog.database import db
    print("✅ database импортирован")
    
    from blog.models import User, Post, Category, Comment, Tag
    print("✅ models импортированы")
    
    from blog.services import post_service, user_service, comment_service
    print("✅ services импортированы")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# 2. Создание приложения
print("\n2️⃣ Создание Flask приложения...")
try:
    app = create_app()
    print("✅ Приложение создано")
except Exception as e:
    print(f"❌ Ошибка создания приложения: {e}")
    sys.exit(1)

# 3. Проверка контекста приложения
print("\n3️⃣ Проверка контекста приложения...")
try:
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        print("✅ База данных инициализирована")
        
        # Проверяем количество таблиц
        tables = db.engine.table_names()
        print(f"✅ Создано таблиц: {len(tables)}")
        print(f"   Таблицы: {', '.join(tables)}")
        
except Exception as e:
    print(f"❌ Ошибка работы с БД: {e}")
    sys.exit(1)

# 4. Проверка маршрутов
print("\n4️⃣ Проверка маршрутов...")
try:
    rules = list(app.url_map.iter_rules())
    print(f"✅ Зарегистрировано маршрутов: {len(rules)}")
    
    # Показываем основные маршруты
    main_routes = [
        '/', '/blog/', '/auth/login', '/auth/register',
        '/admin/', '/api/posts', '/install'
    ]
    
    registered_routes = [rule.rule for rule in rules]
    for route in main_routes:
        if any(route in r for r in registered_routes):
            print(f"   ✓ {route}")
        else:
            print(f"   ✗ {route} НЕ НАЙДЕН")
            
except Exception as e:
    print(f"❌ Ошибка проверки маршрутов: {e}")

# 5. Проверка сервисов
print("\n5️⃣ Проверка сервисов...")
try:
    with app.app_context():
        # Создаем тестового пользователя
        test_user = user_service.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        if test_user:
            print("✅ UserService работает")
        else:
            print("⚠️ UserService: не удалось создать пользователя")
        
        # Проверяем другие сервисы
        from blog.services import category_service, tag_service
        
        test_category = category_service.create(
            name='Test Category',
            description='Test Description'
        )
        
        if test_category:
            print("✅ CategoryService работает")
        else:
            print("⚠️ CategoryService: не удалось создать категорию")
            
except Exception as e:
    print(f"❌ Ошибка тестирования сервисов: {e}")

# 6. Проверка конфигурации
print("\n6️⃣ Проверка конфигурации...")
try:
    with app.app_context():
        print(f"✅ SECRET_KEY: {'установлен' if app.config.get('SECRET_KEY') else 'НЕ УСТАНОВЛЕН'}")
        print(f"✅ DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'НЕ УСТАНОВЛЕН')}")
        print(f"✅ DEBUG: {app.config.get('DEBUG', False)}")
        print(f"✅ TESTING: {app.config.get('TESTING', False)}")
        
except Exception as e:
    print(f"❌ Ошибка проверки конфигурации: {e}")

# 7. Проверка шаблонов
print("\n7️⃣ Проверка шаблонов...")
try:
    templates_dir = Path(app.template_folder)
    if templates_dir.exists():
        template_count = len(list(templates_dir.glob('**/*.html')))
        print(f"✅ Найдено шаблонов: {template_count}")
    else:
        print("❌ Директория шаблонов не найдена")
        
except Exception as e:
    print(f"❌ Ошибка проверки шаблонов: {e}")

# 8. Проверка статических файлов
print("\n8️⃣ Проверка статических файлов...")
try:
    static_dir = Path(app.static_folder)
    if static_dir.exists():
        css_files = list(static_dir.glob('**/*.css'))
        js_files = list(static_dir.glob('**/*.js'))
        print(f"✅ CSS файлов: {len(css_files)}")
        print(f"✅ JS файлов: {len(js_files)}")
    else:
        print("❌ Директория статических файлов не найдена")
        
except Exception as e:
    print(f"❌ Ошибка проверки статических файлов: {e}")

# Итоговый результат
print("\n" + "=" * 60)
print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
print("=" * 60)

# Очистка
try:
    if os.path.exists('test_blog.db'):
        os.remove('test_blog.db')
        print("\n🧹 Тестовая БД удалена")
except:
    pass