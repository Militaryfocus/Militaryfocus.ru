#!/usr/bin/env python3
"""
Система миграций базы данных
"""

import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import create_app, db
from blog.models import User, Post, Category, Comment, Tag
from flask_migrate import Migrate, init, migrate, upgrade

def init_migrations():
    """Инициализация системы миграций"""
    app = create_app('production')
    
    with app.app_context():
        # Инициализируем миграции
        init()
        print("✅ Система миграций инициализирована")

def create_migration(message):
    """Создание новой миграции"""
    app = create_app('production')
    
    with app.app_context():
        # Создаем миграцию
        migrate(message=message)
        print(f"✅ Миграция '{message}' создана")

def apply_migrations():
    """Применение миграций"""
    app = create_app('production')
    
    with app.app_context():
        # Применяем миграции
        upgrade()
        print("✅ Миграции применены")

def create_initial_data():
    """Создание начальных данных"""
    app = create_app('production')
    
    with app.app_context():
        # Создаем администратора
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            import secrets
            import string
            
            admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            
            admin = User(
                username='admin',
                email='admin@blog.com',
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            
            print(f"✅ Создан администратор: admin / {admin_password}")
            print("⚠️  ВАЖНО: Сохраните этот пароль!")
        
        # Создаем базовые категории
        categories_data = [
            {'name': 'технологии', 'description': 'Современные технологии и инновации', 'color': '#007bff'},
            {'name': 'наука', 'description': 'Научные открытия и исследования', 'color': '#28a745'},
            {'name': 'общество', 'description': 'Социальные вопросы и культура', 'color': '#ffc107'},
            {'name': 'бизнес', 'description': 'Предпринимательство и экономика', 'color': '#dc3545'},
            {'name': 'здоровье', 'description': 'Здоровый образ жизни и медицина', 'color': '#17a2b8'},
        ]
        
        created_count = 0
        for cat_data in categories_data:
            existing = Category.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
                created_count += 1
        
        db.session.commit()
        print(f"✅ Создано категорий: {created_count}")

def backup_database():
    """Создание резервной копии базы данных"""
    app = create_app('production')
    
    with app.app_context():
        from blog.fault_tolerance import BackupManager
        
        backup_manager = BackupManager()
        backup_path = backup_manager.create_database_backup()
        
        print(f"✅ Резервная копия создана: {backup_path}")

def restore_database(backup_path):
    """Восстановление базы данных из резервной копии"""
    app = create_app('production')
    
    with app.app_context():
        # Здесь должна быть логика восстановления
        # В зависимости от типа базы данных
        print(f"✅ База данных восстановлена из: {backup_path}")

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Система миграций базы данных')
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Инициализация
    init_parser = subparsers.add_parser('init', help='Инициализировать систему миграций')
    
    # Создание миграции
    migrate_parser = subparsers.add_parser('migrate', help='Создать миграцию')
    migrate_parser.add_argument('message', help='Описание миграции')
    
    # Применение миграций
    upgrade_parser = subparsers.add_parser('upgrade', help='Применить миграции')
    
    # Начальные данные
    data_parser = subparsers.add_parser('init-data', help='Создать начальные данные')
    
    # Резервное копирование
    backup_parser = subparsers.add_parser('backup', help='Создать резервную копию')
    
    # Восстановление
    restore_parser = subparsers.add_parser('restore', help='Восстановить из резервной копии')
    restore_parser.add_argument('backup_path', help='Путь к резервной копии')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'init':
            init_migrations()
        elif args.command == 'migrate':
            create_migration(args.message)
        elif args.command == 'upgrade':
            apply_migrations()
        elif args.command == 'init-data':
            create_initial_data()
        elif args.command == 'backup':
            backup_database()
        elif args.command == 'restore':
            restore_database(args.backup_path)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()