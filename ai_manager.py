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
from blog.integrated_ai_system import (
    integrated_ai_system,
    generate_safe_content,
    batch_generate_safe_content,
    get_ai_system_status,
    optimize_ai_system
)
from blog.ai_monitoring import ai_monitoring_dashboard
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
    print(f"🤖 Генерация {args.count} постов с улучшенной системой ИИ...")
    
    if args.count > 50:
        print("❌ Максимальное количество постов за раз: 50")
        return
    
    # Используем новую интегрированную систему
    if hasattr(args, 'safe') and args.safe:
        print("🛡️ Используем безопасную генерацию с полной проверкой...")
        results = batch_generate_safe_content(args.count)
        success_count = len([r for r in results if r.status.value in ['approved', 'published']])
        
        # Показываем детальную статистику
        approved = len([r for r in results if r.status.value == 'approved'])
        needs_review = len([r for r in results if r.status.value == 'needs_review'])
        rejected = len([r for r in results if r.status.value == 'rejected'])
        
        print(f"📊 Результаты генерации:")
        print(f"   ✅ Одобрено: {approved}")
        print(f"   👁️ Требует проверки: {needs_review}")
        print(f"   ❌ Отклонено: {rejected}")
        print(f"   📈 Общий успех: {success_count}/{args.count}")
    else:
        # Используем старую систему для совместимости
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

def ai_status(args):
    """Показать статус ИИ системы"""
    print("🔍 Получаем статус ИИ системы...")
    
    try:
        status = get_ai_system_status()
        
        print("\n" + "="*60)
        print("🤖 СТАТУС ИИ СИСТЕМЫ")
        print("="*60)
        
        # Общий статус
        ai_health = status.get('ai_health', {})
        print(f"🏥 Здоровье системы: {ai_health.get('status', 'unknown').upper()}")
        print(f"📊 Оценка здоровья: {ai_health.get('score', 0):.2f}")
        
        # Статистика генерации
        gen_stats = status.get('generator_stats', {})
        print(f"\n📈 Статистика генерации:")
        print(f"   Всего попыток: {gen_stats.get('total_attempts', 0)}")
        print(f"   Успешных: {gen_stats.get('successful_generations', 0)}")
        print(f"   Автоисправлений: {gen_stats.get('auto_corrections', 0)}")
        print(f"   На проверке: {gen_stats.get('manual_reviews', 0)}")
        print(f"   Отклонено: {gen_stats.get('rejections', 0)}")
        
        if gen_stats.get('total_attempts', 0) > 0:
            print(f"   Успешность: {gen_stats.get('success_rate', 0):.1%}")
        
        # Статистика модерации
        mod_stats = status.get('moderation_stats', {})
        print(f"\n👁️ Статистика модерации:")
        print(f"   В очереди: {mod_stats.get('queue_size', 0)}")
        print(f"   Одобрено: {mod_stats.get('approved_count', 0)}")
        print(f"   Отклонено: {mod_stats.get('rejected_count', 0)}")
        
        if mod_stats.get('total_moderated', 0) > 0:
            print(f"   Уровень одобрения: {mod_stats.get('approval_rate', 0):.1%}")
        
        # Рекомендации
        recommendations = status.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Рекомендации:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")

def ai_optimize(args):
    """Оптимизация ИИ системы"""
    print("🔧 Запуск оптимизации ИИ системы...")
    
    try:
        optimize_ai_system()
        print("✅ Оптимизация завершена успешно")
        
        # Показываем обновленный статус
        print("\n📊 Обновленный статус:")
        ai_status(args)
        
    except Exception as e:
        print(f"❌ Ошибка оптимизации: {e}")

def ai_monitor(args):
    """Мониторинг ИИ системы"""
    print("📊 Генерация отчета мониторинга ИИ...")
    
    try:
        report = ai_monitoring_dashboard.get_comprehensive_report()
        
        print("\n" + "="*60)
        print("📈 ОТЧЕТ МОНИТОРИНГА ИИ")
        print("="*60)
        
        # Метрики качества
        quality_metrics = report.get('quality_metrics', {})
        if 'average_metrics' in quality_metrics:
            avg_metrics = quality_metrics['average_metrics']
            print(f"🎯 Средние метрики качества:")
            print(f"   Валидация: {avg_metrics.get('validation_score', 0):.3f}")
            print(f"   Предвзятость: {avg_metrics.get('bias_score', 0):.3f}")
            print(f"   Безопасность: {avg_metrics.get('safety_score', 0):.3f}")
            print(f"   Время обработки: {avg_metrics.get('processing_time', 0):.2f}с")
        
        # Предупреждения
        alerts = report.get('quality_alerts', [])
        if alerts:
            print(f"\n⚠️ Предупреждения ({len(alerts)}):")
            for alert in alerts[:5]:  # Показываем первые 5
                severity = alert.get('severity', 'unknown')
                message = alert.get('message', 'Нет описания')
                print(f"   [{severity.upper()}] {message}")
        
        # Статус системы
        system_health = report.get('system_health', {})
        if system_health:
            print(f"\n🏥 Здоровье системы: {system_health.get('status', 'unknown').upper()}")
            
            recommendations = system_health.get('recommendations', [])
            if recommendations:
                print(f"💡 Рекомендации:")
                for rec in recommendations:
                    print(f"   • {rec}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка генерации отчета: {e}")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Менеджер ИИ контента для блога')
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда статистики
    stats_parser = subparsers.add_parser('stats', help='Показать статистику')
    
    # Команда генерации
    generate_parser = subparsers.add_parser('generate', help='Сгенерировать контент')
    generate_parser.add_argument('count', type=int, help='Количество постов')
    generate_parser.add_argument('--safe', action='store_true', 
                               help='Использовать безопасную генерацию с полной проверкой')
    
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
    
    # Новые команды для улучшенной ИИ системы
    ai_status_parser = subparsers.add_parser('ai-status', help='Показать статус ИИ системы')
    
    ai_optimize_parser = subparsers.add_parser('ai-optimize', help='Оптимизировать ИИ систему')
    
    ai_monitor_parser = subparsers.add_parser('ai-monitor', help='Мониторинг ИИ системы')
    
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
        elif args.command == 'ai-status':
            ai_status(args)
        elif args.command == 'ai-optimize':
            ai_optimize(args)
        elif args.command == 'ai-monitor':
            ai_monitor(args)

if __name__ == '__main__':
    main()