#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных в базе данных
"""

import os
import sys
from datetime import datetime, timedelta
import random
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Устанавливаем переменные окружения
os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-for-sample-data')
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/blog.db')

from . import create_app
from config.database import db
from models import User, Post, Category, Tag, Comment, Like, View, Bookmark
from services.core import user_service, post_service, category_service, tag_service, comment_service

app = create_app()

# Примерные данные
SAMPLE_CATEGORIES = [
    {'name': 'Технологии', 'description': 'Новости и статьи о современных технологиях', 'color': '#007bff'},
    {'name': 'Наука', 'description': 'Научные открытия и исследования', 'color': '#28a745'},
    {'name': 'Искусство', 'description': 'Мир искусства и культуры', 'color': '#dc3545'},
    {'name': 'Спорт', 'description': 'Спортивные новости и события', 'color': '#ffc107'},
    {'name': 'Путешествия', 'description': 'Путеводители и рассказы о путешествиях', 'color': '#17a2b8'},
]

SAMPLE_TAGS = [
    'python', 'javascript', 'ai', 'машинное обучение', 'веб-разработка',
    'data science', 'react', 'flask', 'django', 'postgresql',
    'docker', 'kubernetes', 'devops', 'security', 'blockchain',
    'космос', 'физика', 'биология', 'медицина', 'экология'
]

SAMPLE_TITLES = [
    "Как искусственный интеллект меняет мир разработки",
    "10 лучших практик в Python для начинающих",
    "Введение в машинное обучение: с чего начать",
    "Создание REST API с помощью Flask за 30 минут",
    "Docker для разработчиков: полное руководство",
    "Основы кибербезопасности в 2024 году",
    "React vs Vue: что выбрать для нового проекта",
    "PostgreSQL: оптимизация производительности",
    "Микросервисная архитектура: плюсы и минусы",
    "GraphQL: будущее API или временный тренд?",
    "Квантовые вычисления: что нужно знать разработчику",
    "Блокчейн технологии вне криптовалют",
    "CI/CD pipeline с GitHub Actions",
    "Kubernetes для начинающих: развертывание первого приложения",
    "Тестирование в Python: pytest vs unittest"
]

SAMPLE_CONTENT = """
<p>Это пример статьи, созданной автоматически для демонстрации возможностей блога. 
В реальной статье здесь был бы подробный и информативный контент.</p>

<h2>Введение</h2>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud 
exercitation ullamco laboris.</p>

<h2>Основная часть</h2>
<p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu 
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa 
qui officia deserunt mollit anim id est laborum.</p>

<h3>Подраздел 1</h3>
<p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque 
laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi 
architecto beatae vitae dicta sunt explicabo.</p>

<h3>Подраздел 2</h3>
<p>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia 
consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.</p>

<h2>Заключение</h2>
<p>At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium 
voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati 
cupiditate non provident.</p>
"""

SAMPLE_COMMENTS = [
    "Отличная статья! Очень информативно и понятно написано.",
    "Спасибо за подробное объяснение. Буду ждать продолжения.",
    "Интересный подход к решению проблемы. А как насчет альтернативных методов?",
    "Применил описанные техники в своем проекте - работает отлично!",
    "Хотелось бы увидеть больше примеров кода.",
    "Согласен с автором. Это действительно важная тема.",
    "А есть ли исходный код примеров на GitHub?",
    "Очень полезная информация для начинающих разработчиков.",
    "Статья помогла разобраться в сложной теме. Благодарю!",
    "Ждем больше статей на эту тему!"
]

def create_sample_data():
    """Создание тестовых данных"""
    with app.app_context():
        print("🚀 Начинаем создание тестовых данных...")
        
        # Создаем таблицы
        db.create_all()
        
        # 1. Создаем пользователей
        print("\n👥 Создание пользователей...")
        users = []
        
        # Админ
        admin = user_service.create_user(
            username='admin',
            email='admin@blog.com',
            password='admin123',
            is_admin=True
        )
        if admin:
            users.append(admin)
            print(f"✅ Создан администратор: admin / admin123")
        
        # Обычные пользователи
        for i in range(1, 6):
            user = user_service.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password=f'password{i}',
                first_name=f'Имя{i}',
                last_name=f'Фамилия{i}'
            )
            if user:
                users.append(user)
                print(f"✅ Создан пользователь: user{i}")
        
        # 2. Создаем категории
        print("\n📁 Создание категорий...")
        categories = []
        for cat_data in SAMPLE_CATEGORIES:
            category = category_service.create(**cat_data)
            if category:
                categories.append(category)
                print(f"✅ Создана категория: {category.name}")
        
        # 3. Создаем теги
        print("\n🏷️ Создание тегов...")
        tags = []
        for tag_name in SAMPLE_TAGS:
            tag = tag_service.get_or_create_tag(tag_name)
            if tag:
                tags.append(tag)
        print(f"✅ Создано тегов: {len(tags)}")
        
        # 4. Создаем посты
        print("\n📝 Создание постов...")
        posts = []
        
        for i, title in enumerate(SAMPLE_TITLES):
            # Выбираем случайного автора
            author = random.choice(users[1:])  # Исключаем админа
            
            # Выбираем случайную категорию
            category = random.choice(categories)
            
            # Выбираем случайные теги (2-4 штуки)
            post_tags = random.sample(tags, random.randint(2, 4))
            
            # Генерируем дату публикации в прошлом
            days_ago = random.randint(1, 60)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            # Создаем пост
            post_data = {
                'title': title,
                'content': SAMPLE_CONTENT,
                'excerpt': f"Это краткое описание статьи '{title}'. Здесь представлена основная идея и ключевые моменты.",
                'author_id': author.id,
                'category_id': category.id,
                'is_published': True,
                'created_at': created_at,
                'updated_at': created_at
            }
            
            post = post_service.create(**post_data)
            
            if post:
                # Добавляем теги
                for tag in post_tags:
                    post.tags.append(tag)
                
                # Генерируем случайное количество просмотров
                post.views = random.randint(10, 1000)
                
                db.session.commit()
                posts.append(post)
                print(f"✅ Создан пост: {post.title[:50]}...")
        
        # 5. Создаем комментарии
        print("\n💬 Создание комментариев...")
        comment_count = 0
        
        for post in posts:
            # Случайное количество комментариев (0-5)
            num_comments = random.randint(0, 5)
            
            for _ in range(num_comments):
                commenter = random.choice(users)
                comment_text = random.choice(SAMPLE_COMMENTS)
                
                comment = comment_service.create_comment(
                    post_id=post.id,
                    user_id=commenter.id,
                    content=comment_text,
                    is_approved=True
                )
                
                if comment:
                    comment_count += 1
        
        print(f"✅ Создано комментариев: {comment_count}")
        
        # 6. Создаем лайки
        print("\n❤️ Создание лайков...")
        like_count = 0
        
        for post in posts:
            # Случайные лайки от пользователей
            likers = random.sample(users, random.randint(0, len(users)))
            
            for user in likers:
                like = Like(
                    user_id=user.id,
                    item_type='post',
                    item_id=post.id
                )
                db.session.add(like)
                like_count += 1
        
        db.session.commit()
        print(f"✅ Создано лайков: {like_count}")
        
        # 7. Создаем закладки
        print("\n🔖 Создание закладок...")
        bookmark_count = 0
        
        for user in users[1:]:  # Исключаем админа
            # Каждый пользователь добавляет в закладки 1-3 поста
            bookmarked_posts = random.sample(posts, random.randint(1, min(3, len(posts))))
            
            for post in bookmarked_posts:
                bookmark = Bookmark(
                    user_id=user.id,
                    post_id=post.id
                )
                db.session.add(bookmark)
                bookmark_count += 1
        
        db.session.commit()
        print(f"✅ Создано закладок: {bookmark_count}")
        
        # 8. Итоговая статистика
        print("\n📊 Итоговая статистика:")
        print(f"   - Пользователей: {len(users)}")
        print(f"   - Категорий: {len(categories)}")
        print(f"   - Тегов: {len(tags)}")
        print(f"   - Постов: {len(posts)}")
        print(f"   - Комментариев: {comment_count}")
        print(f"   - Лайков: {like_count}")
        print(f"   - Закладок: {bookmark_count}")
        
        print("\n✅ Тестовые данные успешно созданы!")
        print("\n🔑 Данные для входа:")
        print("   Администратор: admin / admin123")
        for i in range(1, 6):
            print(f"   Пользователь {i}: user{i} / password{i}")

if __name__ == '__main__':
    create_sample_data()