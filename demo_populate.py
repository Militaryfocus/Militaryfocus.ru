#!/usr/bin/env python3
"""
Демонстрационный скрипт для наполнения блога ИИ контентом
Создает реалистичный контент, неотличимый от человеческого
"""

import os
import sys
import time
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import create_app, db
from blog.ai_content import populate_blog_with_ai_content, ContentScheduler
from blog.models import Category, User

def create_demo_data():
    """Создание демонстрационных данных"""
    print("🎬 ДЕМОНСТРАЦИЯ ИИ БЛОГА")
    print("="*50)
    
    app = create_app()
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Проверяем администратора
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
            print("👤 Создан администратор: admin / admin123")
        
        # Создаем категории
        categories_data = [
            {'name': 'технологии', 'description': 'Современные технологии и инновации', 'color': '#007bff'},
            {'name': 'наука', 'description': 'Научные открытия и исследования', 'color': '#28a745'},
            {'name': 'общество', 'description': 'Социальные вопросы и культура', 'color': '#ffc107'},
            {'name': 'бизнес', 'description': 'Предпринимательство и экономика', 'color': '#dc3545'},
            {'name': 'образование', 'description': 'Обучение и развитие', 'color': '#17a2b8'},
        ]
        
        created_categories = 0
        for cat_data in categories_data:
            existing = Category.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
                created_categories += 1
        
        db.session.commit()
        print(f"📂 Создано категорий: {created_categories}")
        
        # Генерируем ИИ контент
        print("\n🤖 Генерация ИИ контента...")
        print("📝 Создаем посты с помощью искусственного интеллекта...")
        
        # Создаем 15 постов для демонстрации
        success_count = populate_blog_with_ai_content(15)
        
        print(f"\n✅ Создано {success_count} постов с помощью ИИ")
        print("\n🎯 ОСОБЕННОСТИ ИИ КОНТЕНТА:")
        print("  • Уникальные заголовки и содержание")
        print("  • Естественный человеческий стиль")
        print("  • Разнообразные темы и категории")
        print("  • Автоматические теги и описания")
        print("  • Реалистичные комментарии")
        print("  • Markdown форматирование")
        
        print("\n🚀 ГОТОВО! Блог наполнен ИИ контентом")
        print("🌐 Запустите приложение: python app.py")
        print("🔗 Откройте: http://localhost:5000")
        print("👤 Войдите как admin / admin123")
        print("🤖 ИИ панель: http://localhost:5000/ai/ai-dashboard")

def show_ai_features():
    """Показать возможности ИИ системы"""
    print("\n" + "="*60)
    print("🤖 ВОЗМОЖНОСТИ ИИ СИСТЕМЫ")
    print("="*60)
    
    features = [
        "📝 Автоматическая генерация постов",
        "🎯 Разнообразные темы и стили написания", 
        "💬 Реалистичные комментарии от ИИ пользователей",
        "📅 Планировщик автоматической публикации",
        "⭐ Контроль качества контента",
        "🏷️  Автоматическая генерация тегов",
        "📊 Аналитика и статистика ИИ контента",
        "🔧 Гибкие настройки генерации",
        "🌐 Интеграция с OpenAI API",
        "🎨 Markdown форматирование",
        "📱 Адаптивный дизайн постов",
        "🔍 SEO-оптимизированный контент"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n💡 УНИКАЛЬНОСТЬ:")
    print("  • Контент неотличим от человеческого")
    print("  • Естественные диалоги в комментариях")
    print("  • Разнообразие стилей и тем")
    print("  • Высокое качество и читаемость")
    
    print("="*60)

if __name__ == '__main__':
    print("🎭 Создание демонстрационного блога с ИИ контентом...")
    print("⚡ Это займет несколько минут...")
    
    start_time = time.time()
    
    try:
        create_demo_data()
        show_ai_features()
        
        end_time = time.time()
        print(f"\n⏱️  Время выполнения: {end_time - start_time:.1f} секунд")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("💡 Убедитесь, что все зависимости установлены:")
        print("   pip install -r requirements.txt")
        sys.exit(1)