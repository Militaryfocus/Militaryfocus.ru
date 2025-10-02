#!/usr/bin/env python3
"""
Менеджер ИИ контента для блога
Команды для управления автоматической генерацией контента
"""

import os
import sys
import argparse
from datetime import datetime
import threading
import time

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import create_app, db
from blog.ai_content import (
    AIContentGenerator, 
    ContentScheduler, 
    populate_blog_with_ai_content,
    start_ai_content_generation
)
from blog.models import Post, User, Category, Comment

def create_sample_categories():
    """Создание примерных категорий"""
    categories_data = [
        {'name': 'технологии', 'description': 'Статьи о современных технологиях', 'color': '#007bff'},
        {'name': 'наука', 'description': 'Научные открытия и исследования', 'color': '#28a745'},
        {'name': 'общество', 'description': 'Социальные вопросы и культура', 'color': '#ffc107'},
        {'name': 'бизнес', 'description': 'Предпринимательство и экономика', 'color': '#dc3545'},
    ]
    
    created_count = 0
    for cat_data in categories_data:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
            created_count += 1
    
    db.session.commit()
    return created_count

def show_stats():
    """Показать статистику контента"""
    print("\n" + "="*60)
    print("📊 СТАТИСТИКА БЛОГА")
    print("="*60)
    
    # Общая статистика
    total_posts = Post.query.count()
    ai_posts = Post.query.filter(Post.content.contains('## ')).count()
    total_users = User.query.count()
    total_comments = Comment.query.count()
    
    print(f"📝 Всего постов: {total_posts}")
    print(f"🤖 ИИ постов: {ai_posts} ({ai_posts/total_posts*100:.1f}% от общего)" if total_posts > 0 else "🤖 ИИ постов: 0")
    print(f"👥 Пользователей: {total_users}")
    print(f"💬 Комментариев: {total_comments}")
    
    # Статистика по категориям
    categories = Category.query.all()
    print(f"\n📂 Категории ({len(categories)}):")
    for cat in categories:
        posts_count = cat.get_posts_count()
        print(f"  • {cat.name}: {posts_count} постов")
    
    # Последние ИИ посты
    recent_ai_posts = Post.query.filter(Post.content.contains('## ')).order_by(Post.created_at.desc()).limit(5).all()
    if recent_ai_posts:
        print(f"\n🤖 Последние ИИ посты:")
        for post in recent_ai_posts:
            print(f"  • {post.title[:50]}{'...' if len(post.title) > 50 else ''}")
            print(f"    {post.created_at.strftime('%d.%m.%Y %H:%M')} | Просмотров: {post.views_count}")
    
    print("="*60)

def generate_content(args):
    """Генерация контента"""
    print(f"🤖 Генерация {args.count} постов...")
    
    if args.count > 50:
        print("❌ Максимальное количество постов за раз: 50")
        return
    
    success_count = populate_blog_with_ai_content(args.count)
    print(f"✅ Успешно создано {success_count} из {args.count} постов")

def start_scheduler(args):
    """Запуск планировщика"""
    print("🚀 Запуск планировщика ИИ контента...")
    print("📅 Посты будут создаваться автоматически по расписанию")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    try:
        start_ai_content_generation()
    except KeyboardInterrupt:
        print("\n⏹️  Планировщик остановлен")

def test_generation(args):
    """Тест генерации"""
    print("🧪 Тестирование ИИ генератора...")
    
    try:
        generator = AIContentGenerator()
        post_data = generator.generate_human_like_post()
        
        print("✅ Тест успешен!")
        print(f"📝 Заголовок: {post_data['title']}")
        print(f"📂 Категория: {post_data['category']}")
        print(f"🏷️  Теги: {', '.join(post_data['tags'][:3])}...")
        print(f"⭐ Качество: {post_data['quality_score']:.2f}")
        print(f"⏱️  Время чтения: {post_data['reading_time']} мин")
        
        if args.show_content:
            print(f"\n📄 Содержание (первые 200 символов):")
            print(post_data['content'][:200] + "...")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

def cleanup_content(args):
    """Очистка ИИ контента"""
    if args.type == 'posts':
        ai_posts = Post.query.filter(Post.content.contains('## ')).all()
        count = len(ai_posts)
        
        if count == 0:
            print("ℹ️  Нет ИИ постов для удаления")
            return
            
        if not args.force:
            confirm = input(f"⚠️  Удалить {count} ИИ постов? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Отменено")
                return
        
        for post in ai_posts:
            db.session.delete(post)
        db.session.commit()
        print(f"✅ Удалено {count} ИИ постов")
        
    elif args.type == 'users':
        ai_users = User.query.filter(
            User.username.like('fake_%') | User.email.like('%@example.%')
        ).all()
        count = len(ai_users)
        
        if count == 0:
            print("ℹ️  Нет ИИ пользователей для удаления")
            return
            
        if not args.force:
            confirm = input(f"⚠️  Удалить {count} ИИ пользователей? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Отменено")
                return
        
        for user in ai_users:
            Comment.query.filter_by(author_id=user.id).delete()
            db.session.delete(user)
        db.session.commit()
        print(f"✅ Удалено {count} ИИ пользователей")
        
    elif args.type == 'all':
        if not args.force:
            confirm = input("⚠️  Удалить ВСЕ ИИ данные? Это действие нельзя отменить! (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Отменено")
                return
        
        # Удаляем ИИ посты
        ai_posts = Post.query.filter(Post.content.contains('## ')).all()
        for post in ai_posts:
            db.session.delete(post)
        
        # Удаляем ИИ пользователей
        ai_users = User.query.filter(
            User.username.like('fake_%') | User.email.like('%@example.%')
        ).all()
        for user in ai_users:
            Comment.query.filter_by(author_id=user.id).delete()
            db.session.delete(user)
        
        db.session.commit()
        print(f"✅ Удалены все ИИ данные ({len(ai_posts)} постов, {len(ai_users)} пользователей)")

def setup_blog(args):
    """Первоначальная настройка блога"""
    print("🔧 Настройка блога для ИИ контента...")
    
    # Создаем категории
    cat_count = create_sample_categories()
    print(f"📂 Создано категорий: {cat_count}")
    
    # Генерируем начальный контент
    if args.with_content:
        print("📝 Генерация начального контента...")
        success_count = populate_blog_with_ai_content(args.posts or 10)
        print(f"✅ Создано постов: {success_count}")
    
    print("🎉 Настройка завершена!")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Менеджер ИИ контента для блога')
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда статистики
    stats_parser = subparsers.add_parser('stats', help='Показать статистику')
    
    # Команда генерации
    generate_parser = subparsers.add_parser('generate', help='Сгенерировать контент')
    generate_parser.add_argument('count', type=int, help='Количество постов')
    
    # Команда планировщика
    scheduler_parser = subparsers.add_parser('scheduler', help='Запустить планировщик')
    
    # Команда тестирования
    test_parser = subparsers.add_parser('test', help='Тестировать генератор')
    test_parser.add_argument('--show-content', action='store_true', 
                           help='Показать содержимое поста')
    
    # Команда очистки
    cleanup_parser = subparsers.add_parser('cleanup', help='Очистить ИИ контент')
    cleanup_parser.add_argument('type', choices=['posts', 'users', 'all'],
                               help='Тип контента для очистки')
    cleanup_parser.add_argument('--force', action='store_true',
                               help='Не запрашивать подтверждение')
    
    # Команда настройки
    setup_parser = subparsers.add_parser('setup', help='Первоначальная настройка')
    setup_parser.add_argument('--with-content', action='store_true',
                             help='Создать начальный контент')
    setup_parser.add_argument('--posts', type=int, default=10,
                             help='Количество начальных постов')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Создаем контекст приложения
    app = create_app()
    with app.app_context():
        # Создаем таблицы если их нет
        db.create_all()
        
        # Выполняем команду
        if args.command == 'stats':
            show_stats()
        elif args.command == 'generate':
            generate_content(args)
        elif args.command == 'scheduler':
            start_scheduler(args)
        elif args.command == 'test':
            test_generation(args)
        elif args.command == 'cleanup':
            cleanup_content(args)
        elif args.command == 'setup':
            setup_blog(args)

if __name__ == '__main__':
    main()