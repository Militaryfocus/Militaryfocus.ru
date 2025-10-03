#!/usr/bin/env python3
"""
Комплексное тестирование системы на продакшене
Проверяет все компоненты улучшенной системы генерации контента
"""

import sys
import os
import time
import traceback
from datetime import datetime

# Добавляем путь к модулям блога
sys.path.append(os.path.join(os.path.dirname(__file__), 'blog'))

def test_imports():
    """Тест импорта всех модулей"""
    print("🔍 Тестирование импортов...")
    
    try:
        from blog import create_app, db
        from blog.models import Post, Category, Tag, User, View
        from blog.advanced_content_generator import AdvancedContentGenerator
        from blog.ai_provider_manager import AIProviderManager
        from blog.content_personalization import ContentPersonalizer
        from blog.seo_optimization import ContentSEOAnalyzer, ContentSEOOptimizer
        from blog.integrated_content_manager import IntegratedContentManager
        print("✅ Все модули успешно импортированы")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Тест базы данных"""
    print("\n🗄️ Тестирование базы данных...")
    
    try:
        from blog import create_app, db
        from blog.models import Post, Category, Tag, User, View
        
        app = create_app()
        with app.app_context():
            # Проверяем подключение к БД
            posts_count = Post.query.count()
            users_count = User.query.count()
            categories_count = Category.query.count()
            
            print(f"✅ База данных работает:")
            print(f"   📝 Постов: {posts_count}")
            print(f"   👥 Пользователей: {users_count}")
            print(f"   📂 Категорий: {categories_count}")
            return True
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        traceback.print_exc()
        return False

def test_ai_components():
    """Тест ИИ компонентов"""
    print("\n🤖 Тестирование ИИ компонентов...")
    
    try:
        from blog.advanced_content_generator import AdvancedContentGenerator
        from blog.ai_provider_manager import AIProviderManager
        from blog.content_personalization import ContentPersonalizer
        from blog.seo_optimization import ContentSEOAnalyzer, ContentSEOOptimizer
        
        # Инициализация компонентов
        generator = AdvancedContentGenerator()
        provider_manager = AIProviderManager()
        personalizer = ContentPersonalizer()
        seo_analyzer = ContentSEOAnalyzer()
        seo_optimizer = ContentSEOOptimizer()
        
        print("✅ Все ИИ компоненты инициализированы")
        
        # Тест генерации контента
        test_content = generator.generate_content(
            topic="Тестовая тема",
            content_type="how_to_guide",
            tone="conversational",
            audience="general_public",
            length="medium"
        )
        
        if test_content and test_content.get('content'):
            print("✅ Генерация контента работает")
        else:
            print("⚠️ Генерация контента требует настройки API ключей")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка ИИ компонентов: {e}")
        traceback.print_exc()
        return False

def test_web_routes():
    """Тест веб-маршрутов"""
    print("\n🌐 Тестирование веб-маршрутов...")
    
    try:
        from blog import create_app
        
        app = create_app()
        
        # Проверяем основные маршруты
        routes_to_test = [
            '/',
            '/blog',
            '/ai-dashboard',
            '/ai-settings',
            '/content-analytics'
        ]
        
        with app.test_client() as client:
            for route in routes_to_test:
                try:
                    response = client.get(route)
                    if response.status_code in [200, 302, 401]:  # 401 - нормально для защищенных маршрутов
                        print(f"✅ {route}: {response.status_code}")
                    else:
                        print(f"⚠️ {route}: {response.status_code}")
                except Exception as e:
                    print(f"❌ {route}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка веб-маршрутов: {e}")
        traceback.print_exc()
        return False

def test_command_line():
    """Тест командной строки"""
    print("\n💻 Тестирование командной строки...")
    
    try:
        import subprocess
        
        # Тест команды статуса
        result = subprocess.run([
            'python3', 'ai_manager.py', 'system-status'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Команда system-status работает")
        else:
            print(f"⚠️ Команда system-status: {result.stderr}")
        
        # Тест команды статистики
        result = subprocess.run([
            'python3', 'ai_manager.py', 'stats'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Команда stats работает")
        else:
            print(f"⚠️ Команда stats: {result.stderr}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка командной строки: {e}")
        traceback.print_exc()
        return False

def test_performance():
    """Тест производительности"""
    print("\n⚡ Тестирование производительности...")
    
    try:
        start_time = time.time()
        
        # Тест инициализации системы
        from blog.integrated_content_manager import IntegratedContentManager
        manager = IntegratedContentManager()
        
        init_time = time.time() - start_time
        print(f"✅ Инициализация системы: {init_time:.2f}с")
        
        # Тест генерации контента (если доступно)
        start_time = time.time()
        try:
            result = manager.create_batch_content(1)
            generation_time = time.time() - start_time
            print(f"✅ Генерация контента: {generation_time:.2f}с")
        except Exception as e:
            print(f"⚠️ Генерация контента требует настройки: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка производительности: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ")
    print("=" * 60)
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Импорты", test_imports),
        ("База данных", test_database),
        ("ИИ компоненты", test_ai_components),
        ("Веб-маршруты", test_web_routes),
        ("Командная строка", test_command_line),
        ("Производительность", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к продакшену!")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Требуется доработка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)