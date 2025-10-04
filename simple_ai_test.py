#!/usr/bin/env python3
"""
Простой тест ИИ системы
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.insert(0, '/workspace')

# Загружаем переменные окружения
load_dotenv()

# Устанавливаем переменные окружения для тестирования
os.environ['SECRET_KEY'] = 'test-secret-key-for-development'
os.environ['DATABASE_URL'] = 'sqlite:///blog.db'

# Импортируем необходимые модули
from blog import create_app, db
from blog.models_perfect import User
from blog.ai_content_perfect import PerfectAIContentGenerator

def simple_ai_test():
    """Простой тест ИИ системы"""
    print("🤖 Простой тест ИИ системы...")
    
    # Создаем контекст приложения
    app = create_app()
    
    with app.app_context():
        # Создаем таблицы базы данных
        db.create_all()
        
        # Проверяем существующих пользователей
        users = User.query.all()
        print(f"📊 Найдено пользователей: {len(users)}")
        for user in users:
            print(f"   - {user.username} ({user.email})")
        
        # Используем первого пользователя или создаем нового
        if users:
            test_user = users[0]
            print(f"✅ Используем пользователя: {test_user.username}")
        else:
            test_user = User(
                username='test_user',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                is_active=True
            )
            test_user.set_password('test123456')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Создан новый пользователь")
        
        # Инициализируем ИИ генератор
        print("\n🔧 Инициализация ИИ генератора...")
        ai_generator = PerfectAIContentGenerator()
        
        # Тестируем генерацию заголовка
        print("\n📝 Тест 1: Генерация заголовка...")
        try:
            title = ai_generator.generate_post_title("Искусственный интеллект в веб-разработке")
            print(f"✅ Заголовок сгенерирован: {title}")
        except Exception as e:
            print(f"❌ Ошибка генерации заголовка: {e}")
            title = "Тестовый заголовок о ИИ в веб-разработке"
        
        # Тестируем генерацию контента
        print("\n📄 Тест 2: Генерация контента...")
        try:
            content = ai_generator.generate_post_content(
                title=title,
                topic="Искусственный интеллект в веб-разработке",
                length=500
            )
            print(f"✅ Контент сгенерирован (длина: {len(content)} символов)")
            print(f"📖 Превью: {content[:200]}...")
        except Exception as e:
            print(f"❌ Ошибка генерации контента: {e}")
            content = "Тестовый контент о ИИ в веб-разработке. " * 20
        
        # Тестируем генерацию описания
        print("\n📋 Тест 3: Генерация описания...")
        try:
            excerpt = ai_generator.generate_post_excerpt(content, length=150)
            print(f"✅ Описание сгенерировано: {excerpt}")
        except Exception as e:
            print(f"❌ Ошибка генерации описания: {e}")
            excerpt = "Краткое описание статьи о ИИ в веб-разработке."
        
        # Тестируем генерацию тегов
        print("\n🏷️ Тест 4: Генерация тегов...")
        try:
            tags = ai_generator.generate_tags(content, count=5)
            print(f"✅ Теги сгенерированы: {tags}")
        except Exception as e:
            print(f"❌ Ошибка генерации тегов: {e}")
            tags = ["ИИ", "веб-разработка", "технологии", "программирование", "машинное обучение"]
        
        # Получаем статистику ИИ системы
        print("\n📈 Статистика ИИ системы:")
        try:
            stats = ai_generator.get_system_stats()
            print(f"✅ Статистика получена:")
            print(f"   - Доступные провайдеры: {stats['available_providers']}")
            print(f"   - Размер кэша: {stats['cache_size']}")
            if stats['provider_stats']:
                print(f"   - Статистика провайдеров: {stats['provider_stats']}")
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
        
        print("\n🎉 Тестирование ИИ системы завершено!")
        print("=" * 50)

if __name__ == '__main__':
    simple_ai_test()