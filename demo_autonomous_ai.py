#!/usr/bin/env python3
"""
Демонстрация автономной ИИ системы
Показывает, как ИИ самостоятельно создает категории, теги и контент
"""

import os
import sys
import time

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_autonomous_ai():
    """Демонстрация автономной ИИ системы"""
    print("🤖 ДЕМОНСТРАЦИЯ АВТОНОМНОЙ ИИ СИСТЕМЫ")
    print("="*60)
    print("Эта система показывает, как ИИ может:")
    print("• Анализировать тренды и популярные темы")
    print("• Автоматически создавать категории")
    print("• Генерировать релевантные теги")
    print("• Создавать качественный контент")
    print("• Планировать публикации")
    print("="*60)
    
    try:
        from blog import create_app, db
        from blog.autonomous_ai import start_autonomous_content_generation, get_autonomous_stats
        from blog.models import Category, Tag, Post
        
        app = create_app()
        with app.app_context():
            # Создаем таблицы если их нет
            db.create_all()
            
            print("\n🚀 Запуск автономной генерации...")
            print("ИИ анализирует тренды и создает контент...")
            
            # Запускаем автономную генерацию
            results = start_autonomous_content_generation()
            
            print("\n" + "="*60)
            print("📊 РЕЗУЛЬТАТЫ АВТОНОМНОЙ ГЕНЕРАЦИИ")
            print("="*60)
            
            print(f"📂 Создано категорий: {results.get('categories_created', 0)}")
            print(f"🏷️ Создано тегов: {results.get('tags_created', 0)}")
            print(f"📝 Создано постов: {results.get('posts_generated', 0)}")
            print(f"📈 Проанализировано трендов: {results.get('trends_analyzed', 0)}")
            
            if results.get('errors'):
                print(f"\n⚠️ Ошибки:")
                for error in results['errors']:
                    print(f"   • {error}")
            
            print("="*60)
            
            # Показываем созданные категории
            categories = Category.query.all()
            if categories:
                print(f"\n📂 СОЗДАННЫЕ КАТЕГОРИИ ({len(categories)}):")
                for cat in categories:
                    posts_count = cat.get_posts_count()
                    print(f"   • {cat.name}: {posts_count} постов")
                    print(f"     Описание: {cat.description}")
                    print(f"     Цвет: {cat.color}")
            
            # Показываем популярные теги
            popular_tags = db.session.query(Tag.name, db.func.count(Tag.id)).join(
                Tag.posts
            ).group_by(Tag.name).order_by(db.func.count(Tag.id).desc()).limit(10).all()
            
            if popular_tags:
                print(f"\n🏷️ ПОПУЛЯРНЫЕ ТЕГИ:")
                for tag_name, count in popular_tags:
                    print(f"   • {tag_name}: {count} постов")
            
            # Показываем последние посты
            recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
            if recent_posts:
                print(f"\n📝 ПОСЛЕДНИЕ СОЗДАННЫЕ ПОСТЫ:")
                for post in recent_posts:
                    print(f"   • {post.title}")
                    print(f"     Категория: {post.category.name if post.category else 'Без категории'}")
                    print(f"     Теги: {', '.join([tag.name for tag in post.tags[:3]])}")
                    print(f"     Создан: {post.created_at.strftime('%d.%m.%Y %H:%M')}")
                    print()
            
            # Показываем общую статистику
            stats = get_autonomous_stats()
            print(f"\n📈 ОБЩАЯ СТАТИСТИКА АВТОНОМНОЙ СИСТЕМЫ:")
            print(f"   Всего создано категорий: {stats.get('categories_created', 0)}")
            print(f"   Всего создано тегов: {stats.get('tags_created', 0)}")
            print(f"   Всего создано постов: {stats.get('posts_generated', 0)}")
            print(f"   Последний анализ: {stats.get('last_analysis', 'Никогда')}")
            
            print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
            print("\n💡 Что произошло:")
            print("   1. ИИ проанализировал текущие тренды")
            print("   2. Создал новые категории на основе популярных тем")
            print("   3. Сгенерировал релевантные теги для каждой категории")
            print("   4. Создал качественный контент по актуальным темам")
            print("   5. Автоматически спланировал публикации")
            
            print("\n🚀 Следующие шаги:")
            print("   1. python app.py                    # Запустить блог")
            print("   2. Откройте http://localhost:5000")
            print("   3. Перейдите в /autonomous/dashboard # Панель автономной ИИ")
            print("   4. Используйте команду: python ai_manager.py autonomous")
            
            return True
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")
        return False

def show_autonomous_capabilities():
    """Показать возможности автономной системы"""
    print("\n" + "="*60)
    print("🤖 ВОЗМОЖНОСТИ АВТОНОМНОЙ ИИ СИСТЕМЫ")
    print("="*60)
    
    capabilities = {
        "📊 Анализ трендов": [
            "Анализ существующего контента",
            "Мониторинг внешних источников",
            "Сезонные тренды",
            "Популярные темы",
            "Статистика просмотров"
        ],
        "📂 Управление категориями": [
            "Автоматическое создание категорий",
            "Умная категоризация тем",
            "Динамические описания",
            "Цветовое кодирование",
            "Статистика по категориям"
        ],
        "🏷️ Генерация тегов": [
            "Контекстные теги",
            "Популярные темы",
            "Семантический анализ",
            "Автоматическая группировка",
            "Статистика использования"
        ],
        "✍️ Создание контента": [
            "Качественные статьи",
            "Разнообразные стили",
            "SEO-оптимизация",
            "Автоматическое форматирование",
            "Контроль качества"
        ],
        "📅 Планирование": [
            "Автоматическое планирование",
            "Приоритизация тем",
            "Оптимальное время публикации",
            "Балансировка контента",
            "Адаптивное расписание"
        ],
        "🔧 Управление": [
            "Веб-интерфейс",
            "Командная строка",
            "API для интеграции",
            "Мониторинг в реальном времени",
            "Детальная аналитика"
        ]
    }
    
    for category, items in capabilities.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  • {item}")
    
    print("\n🎯 УНИКАЛЬНЫЕ ОСОБЕННОСТИ:")
    print("  ✨ Полная автономность - ИИ работает без вмешательства")
    print("  🧠 Самообучение - система улучшается со временем")
    print("  📈 Адаптивность - подстраивается под аудиторию")
    print("  🔄 Непрерывность - работает 24/7")
    print("  🎨 Креативность - создает уникальный контент")
    
    print("="*60)

if __name__ == '__main__':
    start_time = time.time()
    
    success = demo_autonomous_ai()
    
    if success:
        show_autonomous_capabilities()
        
        end_time = time.time()
        print(f"\n⏱️  Время демонстрации: {end_time - start_time:.2f} секунд")
        
        print("\n🚀 АВТОНОМНАЯ ИИ СИСТЕМА ГОТОВА!")
        print("📋 Доступные команды:")
        print("   • python ai_manager.py autonomous        # Автономная генерация")
        print("   • python ai_manager.py autonomous-status  # Статус системы")
        print("   • python ai_manager.py stats              # Общая статистика")
        
    else:
        print("\n❌ Демонстрация не пройдена")
        print("💡 Проверьте установку зависимостей")
        sys.exit(1)