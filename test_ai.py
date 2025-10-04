#!/usr/bin/env python3
"""
Тест ИИ системы для создания контента
"""

import os
import sys
import asyncio
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
from blog.models_perfect import User, Post, Category, Tag
from blog.ai_content_perfect import PerfectAIContentGenerator

def test_ai_content_generation():
    """Тест генерации ИИ контента"""
    print("🤖 Тестирование ИИ системы создания контента...")
    
    # Создаем контекст приложения
    app = create_app()
    
    with app.app_context():
        # Создаем таблицы базы данных
        db.create_all()
        
        # Создаем тестового пользователя
        test_user = User.query.filter_by(username='test_user').first()
        if not test_user:
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
            print("✅ Создан тестовый пользователь")
        else:
            print("✅ Используется существующий тестовый пользователь")
        
        # Создаем тестовую категорию
        test_category = Category.query.filter_by(name='Технологии').first()
        if not test_category:
            test_category = Category(
                name='Технологии',
                slug='tehnologii',
                description='Статьи о технологиях и программировании'
            )
            db.session.add(test_category)
            db.session.commit()
            print("✅ Создана тестовая категория")
        
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
        
        # Создаем пост с ИИ контентом
        print("\n💾 Тест 5: Создание поста в базе данных...")
        try:
            # Создаем теги в базе данных
            tag_objects = []
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(
                        name=tag_name,
                        slug=tag_name.lower().replace(' ', '-'),
                        description=f"Тег {tag_name}"
                    )
                    db.session.add(tag)
                tag_objects.append(tag)
            
            db.session.commit()
            
            # Создаем пост
            post = Post(
                title=title,
                content=content,
                excerpt=excerpt,
                author_id=test_user.id,
                category_id=test_category.id,
                is_published=True,
                is_featured=True,
                views_count=0,
                comments_count=0
            )
            
            # Добавляем теги к посту
            post.tags = tag_objects
            
            db.session.add(post)
            db.session.commit()
            
            print(f"✅ Пост создан успешно! ID: {post.id}")
            print(f"📊 Статистика поста:")
            print(f"   - Заголовок: {post.title}")
            print(f"   - Длина контента: {len(post.content)} символов")
            print(f"   - Количество тегов: {len(post.tags)}")
            print(f"   - Автор: {post.author.get_full_name()}")
            print(f"   - Категория: {post.category.name}")
            
        except Exception as e:
            print(f"❌ Ошибка создания поста: {e}")
        
        # Тестируем генерацию комментария
        print("\n💬 Тест 6: Генерация комментария...")
        try:
            comment = ai_generator.generate_comment(content[:300])
            print(f"✅ Комментарий сгенерирован: {comment}")
        except Exception as e:
            print(f"❌ Ошибка генерации комментария: {e}")
        
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
    test_ai_content_generation()