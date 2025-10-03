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
from blog.integrated_content_manager import (
    integrated_content_manager,
    create_content,
    batch_create_content,
    get_content_manager_stats,
    get_system_status,
    optimize_existing_content,
    get_user_content_recommendations,
    get_user_analytics
)
from blog.ai_provider_manager import get_ai_provider_stats, get_available_ai_models
from blog.content_personalization import analyze_user_behavior, get_personalized_recommendations
from blog.seo_optimization import research_keywords, analyze_content_seo
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

def advanced_generate(args):
    """Продвинутая генерация контента"""
    print(f"🚀 Продвинутая генерация {args.count} постов...")
    
    if args.count > 20:
        print("❌ Максимальное количество постов за раз: 20")
        return
    
    try:
        import asyncio
        
        # Создаем запросы на генерацию
        requests = []
        for i in range(args.count):
            from blog.integrated_content_manager import ContentCreationRequest, ContentWorkflow
            
            workflow = ContentWorkflow.SEO_OPTIMIZED_GENERATION if args.seo else ContentWorkflow.AI_GENERATION
            
            request = ContentCreationRequest(
                topic=f"Тема {i+1}",
                content_type=args.content_type or "how_to_guide",
                tone=args.tone or "conversational",
                target_audience=args.audience or "general_public",
                keywords=args.keywords.split(',') if args.keywords else None,
                seo_optimized=args.seo,
                personalized=args.personalized,
                user_id=args.user_id if args.personalized else None
            )
            requests.append(request)
        
        # Запускаем асинхронную генерацию
        async def generate_async():
            return await batch_create_content(requests)
        
        results = asyncio.run(generate_async())
        
        # Показываем результаты
        print(f"📊 Результаты генерации:")
        print(f"   ✅ Успешно создано: {len(results)}")
        
        for result in results:
            print(f"   • {result.title[:50]}{'...' if len(result.title) > 50 else ''}")
            print(f"     Качество: {result.quality_score:.2f}, SEO: {result.seo_score:.2f}")
        
        # Показываем статистику
        stats = get_content_manager_stats()
        print(f"\n📈 Статистика системы:")
        print(f"   Всего создано: {stats['total_created']}")
        print(f"   Среднее качество: {stats['avg_quality_score']:.2f}")
        print(f"   Средний SEO балл: {stats['avg_seo_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка продвинутой генерации: {e}")

def keyword_research_cmd(args):
    """Исследование ключевых слов"""
    print(f"🔍 Исследование ключевых слов для темы: {args.topic}")
    
    try:
        keywords = research_keywords(args.topic, args.language)
        
        print(f"\n📊 Найдено {len(keywords)} ключевых слов:")
        print("-" * 80)
        
        for i, kw in enumerate(keywords[:10], 1):
            print(f"{i:2d}. {kw.keyword}")
            print(f"    Объем поиска: {kw.search_volume:,}")
            print(f"    Сложность: {kw.difficulty.value}")
            print(f"    CPC: ${kw.cpc:.2f}")
            print(f"    Тренд: {kw.trend}")
            print()
        
        if len(keywords) > 10:
            print(f"... и еще {len(keywords) - 10} ключевых слов")
        
    except Exception as e:
        print(f"❌ Ошибка исследования ключевых слов: {e}")

def seo_analyze(args):
    """SEO анализ контента"""
    if not args.post_id:
        print("❌ Укажите ID поста для анализа")
        return
    
    try:
        post = Post.query.get(args.post_id)
        if not post:
            print(f"❌ Пост с ID {args.post_id} не найден")
            return
        
        print(f"🔍 SEO анализ поста: {post.title}")
        
        # Извлекаем ключевые слова из тегов
        keywords = [tag.name for tag in post.tags]
        
        # Проводим SEO анализ
        seo_analysis = analyze_content_seo(post.content, post.title, "", keywords)
        
        print(f"\n📊 Результаты SEO анализа:")
        print("-" * 50)
        print(f"Общий SEO балл: {seo_analysis.overall_seo_score:.2f}")
        print(f"Заголовок: {seo_analysis.title_score:.2f}")
        print(f"Мета-описание: {seo_analysis.meta_description_score:.2f}")
        print(f"Контент: {seo_analysis.content_score:.2f}")
        print(f"Структура: {seo_analysis.structure_score:.2f}")
        print(f"Плотность ключевых слов: {seo_analysis.keyword_density_score:.2f}")
        print(f"Читаемость: {seo_analysis.readability_score:.2f}")
        
        if seo_analysis.recommendations:
            print(f"\n💡 Рекомендации:")
            for rec in seo_analysis.recommendations:
                print(f"   • {rec}")
        
        if seo_analysis.issues:
            print(f"\n⚠️ Проблемы:")
            for issue in seo_analysis.issues:
                print(f"   • {issue}")
        
    except Exception as e:
        print(f"❌ Ошибка SEO анализа: {e}")

def user_analytics(args):
    """Аналитика пользователя"""
    if not args.user_id:
        print("❌ Укажите ID пользователя")
        return
    
    try:
        user = User.query.get(args.user_id)
        if not user:
            print(f"❌ Пользователь с ID {args.user_id} не найден")
            return
        
        print(f"👤 Аналитика пользователя: {user.username}")
        
        # Получаем аналитику
        analytics = get_user_analytics(args.user_id)
        
        print(f"\n📊 Профиль пользователя:")
        print("-" * 40)
        print(f"Сегменты: {', '.join(analytics.get('user_segments', []))}")
        print(f"Предпочитаемая длина: {analytics.get('preferred_content_length', 'medium')}")
        print(f"Предпочитаемый тон: {analytics.get('preferred_tone', 'conversational')}")
        print(f"Скорость чтения: {analytics.get('reading_speed', 200)} слов/мин")
        print(f"Средняя сессия: {analytics.get('average_session_duration', 5):.1f} мин")
        
        print(f"\n📈 Активность:")
        print(f"Создано постов: {analytics.get('posts_created', 0)}")
        print(f"Просмотров: {analytics.get('total_views', 0)}")
        print(f"Комментариев: {analytics.get('comments_made', 0)}")
        print(f"Уровень вовлеченности: {analytics.get('engagement_level', 'medium')}")
        
        # Предпочтения по категориям
        category_prefs = analytics.get('preferred_categories', {})
        if category_prefs:
            print(f"\n📂 Предпочтения по категориям:")
            for category, score in sorted(category_prefs.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {category}: {score:.2f}")
        
        # Рекомендации контента
        recommendations = get_user_content_recommendations(args.user_id, 5)
        if recommendations:
            print(f"\n🎯 Рекомендации контента:")
            for rec in recommendations:
                print(f"   • {rec['title'][:50]}{'...' if len(rec['title']) > 50 else ''}")
                print(f"     Оценка: {rec['score']:.2f}, Причины: {', '.join(rec['reasons'][:2])}")
        
    except Exception as e:
        print(f"❌ Ошибка получения аналитики: {e}")

def system_status(args):
    """Статус системы"""
    print("🔍 Получаем статус интегрированной системы...")
    
    try:
        status = get_system_status()
        
        print("\n" + "="*60)
        print("🤖 СТАТУС ИНТЕГРИРОВАННОЙ СИСТЕМЫ")
        print("="*60)
        
        # Общий статус
        print(f"📅 Время: {status['timestamp']}")
        print(f"📊 Очередь задач: {status['queue_size']}")
        print(f"🔄 Активных задач: {status['active_tasks']}")
        
        # Статистика создания контента
        creation_stats = status['creation_stats']
        print(f"\n📝 Статистика создания контента:")
        print(f"   Всего создано: {creation_stats['total_created']}")
        print(f"   Среднее качество: {creation_stats['avg_quality_score']:.2f}")
        print(f"   Средний SEO балл: {creation_stats['avg_seo_score']:.2f}")
        print(f"   Среднее время обработки: {creation_stats['avg_processing_time']:.2f}с")
        
        # Статистика по рабочим процессам
        if creation_stats['by_workflow']:
            print(f"\n🔄 По рабочим процессам:")
            for workflow, count in creation_stats['by_workflow'].items():
                print(f"   • {workflow}: {count}")
        
        # Статистика по статусам
        if creation_stats['by_status']:
            print(f"\n📊 По статусам:")
            for status_name, count in creation_stats['by_status'].items():
                print(f"   • {status_name}: {count}")
        
        # Статус компонентов
        components = status['components_status']
        print(f"\n🔧 Статус компонентов:")
        for component, status_name in components.items():
            emoji = "✅" if status_name == "active" else "❌"
            print(f"   {emoji} {component}: {status_name}")
        
        # Статистика ИИ провайдеров
        ai_stats = status['ai_provider_stats']
        if ai_stats:
            print(f"\n🤖 Статистика ИИ провайдеров:")
            print(f"   Всего запросов: {ai_stats.get('total_requests', 0)}")
            print(f"   Всего токенов: {ai_stats.get('total_tokens', 0)}")
            print(f"   Общая стоимость: ${ai_stats.get('total_cost', 0):.2f}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")

def optimize_content_cmd(args):
    """Оптимизация контента"""
    if not args.post_id:
        print("❌ Укажите ID поста для оптимизации")
        return
    
    try:
        post = Post.query.get(args.post_id)
        if not post:
            print(f"❌ Пост с ID {args.post_id} не найден")
            return
        
        print(f"🔧 Оптимизация поста: {post.title}")
        
        import asyncio
        
        async def optimize_async():
            return await optimize_existing_content(args.post_id, args.type)
        
        result = asyncio.run(optimize_async())
        
        print(f"✅ Оптимизация завершена!")
        print(f"Тип оптимизации: {result['optimization_type']}")
        
        if 'changes_made' in result:
            print(f"\n📝 Внесенные изменения:")
            for change in result['changes_made']:
                print(f"   • {change}")
        
        if 'seo_improvements' in result:
            print(f"\n🚀 SEO улучшения:")
            for improvement in result['seo_improvements']:
                print(f"   • {improvement}")
        
    except Exception as e:
        print(f"❌ Ошибка оптимизации: {e}")

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
    
    # Новые команды интегрированной системы
    advanced_parser = subparsers.add_parser('advanced-generate', help='Продвинутая генерация контента')
    advanced_parser.add_argument('count', type=int, help='Количество постов для генерации')
    advanced_parser.add_argument('--content-type', choices=['how_to_guide', 'comparison_review', 'analytical_article', 'news_article', 'listicle'], help='Тип контента')
    advanced_parser.add_argument('--tone', choices=['professional', 'conversational', 'authoritative', 'friendly', 'technical'], help='Тон контента')
    advanced_parser.add_argument('--audience', choices=['beginners', 'intermediate', 'experts', 'general_public', 'professionals'], help='Целевая аудитория')
    advanced_parser.add_argument('--keywords', help='Ключевые слова через запятую')
    advanced_parser.add_argument('--seo', action='store_true', help='SEO оптимизация')
    advanced_parser.add_argument('--personalized', action='store_true', help='Персонализация')
    advanced_parser.add_argument('--user-id', type=int, help='ID пользователя для персонализации')
    
    keywords_parser = subparsers.add_parser('keywords', help='Исследование ключевых слов')
    keywords_parser.add_argument('topic', help='Тема для исследования')
    keywords_parser.add_argument('--language', default='ru', help='Язык исследования')
    
    seo_parser = subparsers.add_parser('seo-analyze', help='SEO анализ контента')
    seo_parser.add_argument('post_id', type=int, help='ID поста для анализа')
    
    analytics_parser = subparsers.add_parser('user-analytics', help='Аналитика пользователя')
    analytics_parser.add_argument('user_id', type=int, help='ID пользователя')
    
    status_parser = subparsers.add_parser('system-status', help='Статус интегрированной системы')
    
    optimize_parser = subparsers.add_parser('optimize-content', help='Оптимизация существующего контента')
    optimize_parser.add_argument('post_id', type=int, help='ID поста для оптимизации')
    optimize_parser.add_argument('--type', choices=['seo', 'personalization'], default='seo', help='Тип оптимизации')
    
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
        elif args.command == 'advanced-generate':
            advanced_generate(args)
        elif args.command == 'keywords':
            keyword_research_cmd(args)
        elif args.command == 'seo-analyze':
            seo_analyze(args)
        elif args.command == 'user-analytics':
            user_analytics(args)
        elif args.command == 'system-status':
            system_status(args)
        elif args.command == 'optimize-content':
            optimize_content_cmd(args)

if __name__ == '__main__':
    main()