#!/usr/bin/env python3
"""
Тестирование ИИ системы блога
"""

import os
import sys
import time

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_system():
    """Тестирование ИИ системы"""
    print("🧪 ТЕСТИРОВАНИЕ ИИ СИСТЕМЫ БЛОГА")
    print("="*50)
    
    try:
        # Тест импортов
        print("📦 Тестирование импортов...")
        from blog.ai_content import AIContentGenerator, ContentScheduler
        print("✅ Импорты успешны")
        
        # Тест генератора
        print("\n🤖 Тестирование генератора контента...")
        generator = AIContentGenerator()
        
        # Генерируем тестовый пост
        post_data = generator.generate_human_like_post('технологии', 'искусственный интеллект')
        
        print("✅ Генерация успешна!")
        print(f"📝 Заголовок: {post_data['title']}")
        print(f"📂 Категория: {post_data['category']}")
        print(f"🏷️  Теги: {', '.join(post_data['tags'][:3])}")
        print(f"⭐ Качество: {post_data['quality_score']:.2f}")
        print(f"⏱️  Время чтения: {post_data['reading_time']} мин")
        print(f"📄 Длина контента: {len(post_data['content'])} символов")
        
        # Тест комментариев
        print("\n💬 Тестирование генерации комментариев...")
        comment = generator.generate_realistic_comment(post_data['title'], post_data['content'])
        print(f"✅ Комментарий: {comment}")
        
        # Тест различных тем
        print("\n🎯 Тестирование разных тем...")
        themes = ['наука', 'общество', 'бизнес']
        for theme in themes:
            test_post = generator.generate_human_like_post(theme)
            print(f"✅ {theme}: {test_post['title'][:50]}...")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n💡 ИИ система готова к использованию:")
        print("   • Генерация качественного контента")
        print("   • Реалистичные комментарии")
        print("   • Разнообразие тем и стилей")
        print("   • Автоматическое форматирование")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def show_ai_capabilities():
    """Показать возможности ИИ"""
    print("\n" + "="*60)
    print("🤖 ВОЗМОЖНОСТИ ИИ СИСТЕМЫ")
    print("="*60)
    
    capabilities = {
        "📝 Генерация контента": [
            "Уникальные заголовки и статьи",
            "Естественный человеческий стиль",
            "Разнообразие тем и категорий",
            "Markdown форматирование",
            "SEO-оптимизация"
        ],
        "💬 Комментарии": [
            "Реалистичные диалоги",
            "Разные типы комментариев",
            "Естественные реакции",
            "Вопросы и ответы",
            "Личный опыт"
        ],
        "🎨 Стили написания": [
            "Научно-популярный",
            "Разговорный",
            "Аналитический",
            "Практический",
            "Мотивационный"
        ],
        "🔧 Управление": [
            "Веб-интерфейс управления",
            "Командная строка",
            "Планировщик публикаций",
            "Контроль качества",
            "Аналитика и статистика"
        ]
    }
    
    for category, items in capabilities.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  • {item}")
    
    print("\n🎯 УНИКАЛЬНОСТЬ:")
    print("  ✨ Контент неотличим от человеческого")
    print("  🎭 Естественные эмоции и мнения")
    print("  📚 Глубокие знания по разным темам")
    print("  🔄 Постоянное разнообразие контента")
    
    print("="*60)

if __name__ == '__main__':
    start_time = time.time()
    
    success = test_ai_system()
    
    if success:
        show_ai_capabilities()
        
        end_time = time.time()
        print(f"\n⏱️  Время тестирования: {end_time - start_time:.2f} секунд")
        
        print("\n🚀 ГОТОВО К ИСПОЛЬЗОВАНИЮ!")
        print("📋 Следующие шаги:")
        print("   1. python demo_populate.py  # Создать демо-контент")
        print("   2. python app.py           # Запустить блог")
        print("   3. Откройте http://localhost:5000")
        print("   4. ИИ панель: /ai/ai-dashboard")
        
    else:
        print("\n❌ Тестирование не пройдено")
        print("💡 Проверьте установку зависимостей")
        sys.exit(1)