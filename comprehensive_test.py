#!/usr/bin/env python3
"""
Упрощенные тесты для проверки работоспособности системы
"""

import os
import sys
import tempfile
import unittest
from werkzeug.security import generate_password_hash

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Тест базовой функциональности без Flask-Admin"""
    print("🧪 Тестирование базовой функциональности...")
    
    try:
        # Настройка окружения
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['FLASK_DEBUG'] = 'False'
        
        # Импорт после настройки окружения
        from blog.models import User, Post, Category, Comment, db
        from blog import create_app
        
        # Создание приложения без админки
        app = create_app()
        
        with app.app_context():
            # Создание таблиц
            db.create_all()
            print("✅ База данных создана")
            
            # Тест создания пользователя
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpass')
            )
            db.session.add(user)
            db.session.commit()
            print("✅ Пользователь создан")
            
            # Тест создания категории
            category = Category(
                name='Тестовая категория',
                slug='test-category',
                description='Описание тестовой категории',
                color='#007bff'
            )
            db.session.add(category)
            db.session.commit()
            print("✅ Категория создана")
            
            # Тест создания поста
            post = Post(
                title='Тестовый пост',
                slug='test-post',
                content='Содержимое тестового поста',
                excerpt='Краткое описание',
                author_id=user.id,
                category_id=category.id
            )
            db.session.add(post)
            db.session.commit()
            print("✅ Пост создан")
            
            # Тест создания комментария
            comment = Comment(
                content='Тестовый комментарий',
                author_id=user.id,
                post_id=post.id
            )
            db.session.add(comment)
            db.session.commit()
            print("✅ Комментарий создан")
            
            # Проверка связей
            assert post.author == user
            assert post.category == category
            assert comment.post == post
            assert comment.author == user
            print("✅ Связи между моделями работают")
            
            # Тест методов моделей
            assert user.get_full_name() == 'testuser'
            assert post.get_comments_count() == 1
            assert post.get_reading_time() > 0
            print("✅ Методы моделей работают")
            
            # Тест аватара пользователя
            avatar_url = user.get_avatar_url()
            assert avatar_url is not None
            print("✅ Аватар пользователя работает")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка в базовом тесте: {e}")
        return False

def test_ai_system():
    """Тест ИИ системы"""
    print("\n🤖 Тестирование ИИ системы...")
    
    try:
        from blog.ai_provider_manager import AIProviderManager
        from blog.ai_content import AIContentGenerator
        
        # Тест менеджера провайдеров
        manager = AIProviderManager()
        providers = manager.get_available_providers()
        print(f"✅ Доступные провайдеры: {providers}")
        
        # Тест генератора контента
        generator = AIContentGenerator()
        print("✅ Генератор контента инициализирован")
        
        # Тест базовой функциональности ИИ
        try:
            # Проверяем доступность OpenAI (без реального запроса)
            if hasattr(generator, 'openai_client'):
                print("✅ OpenAI клиент доступен")
        except Exception:
            print("⚠️ OpenAI клиент требует настройки API ключа")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в ИИ тесте: {e}")
        return False

def test_security():
    """Тест системы безопасности"""
    print("\n🔒 Тестирование безопасности...")
    
    try:
        from blog.security import init_security_headers
        from werkzeug.security import generate_password_hash, check_password_hash
        
        # Тест хеширования паролей
        password = 'testpassword123'
        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)
        
        assert check_password_hash(hash1, password)
        assert check_password_hash(hash2, password)
        assert hash1 != hash2  # Разные хеши для одного пароля
        print("✅ Хеширование паролей работает")
        
        # Тест безопасности заголовков
        from flask import Flask
        app = Flask(__name__)
        init_security_headers(app)
        print("✅ Безопасные заголовки инициализированы")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте безопасности: {e}")
        return False

def test_monitoring():
    """Тест системы мониторинга"""
    print("\n📊 Тестирование мониторинга...")
    
    try:
        from blog.monitoring import SystemMonitor
        import psutil
        
        # Тест мониторинга системы
        monitor = SystemMonitor()
        
        # Получение метрик
        cpu_usage = monitor.get_cpu_usage()
        memory_usage = monitor.get_memory_usage()
        disk_usage = monitor.get_disk_usage()
        
        assert 0 <= cpu_usage <= 100
        assert 0 <= memory_usage <= 100
        assert 0 <= disk_usage <= 100
        print(f"✅ CPU: {cpu_usage}%, RAM: {memory_usage}%, Disk: {disk_usage}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте мониторинга: {e}")
        return False

def test_seo():
    """Тест SEO системы"""
    print("\n🔍 Тестирование SEO...")
    
    try:
        from blog.seo_optimizer import SEOOptimizer
        
        optimizer = SEOOptimizer()
        
        # Тест генерации мета-тегов
        meta_tags = optimizer.generate_meta_tags(
            title="Тестовый пост",
            description="Описание тестового поста",
            keywords=["тест", "блог", "python"]
        )
        
        assert 'title' in meta_tags
        assert 'description' in meta_tags
        assert 'og:title' in meta_tags
        assert 'twitter:card' in meta_tags
        print("✅ SEO оптимизатор работает")
        
        # Тест анализатора SEO
        from blog.seo_optimizer import SEOAnalyzer
        analyzer = SEOAnalyzer()
        
        # Тест извлечения ключевых слов
        keywords = analyzer.extract_keywords("Это тестовый текст для анализа ключевых слов")
        assert len(keywords) > 0
        print("✅ Анализатор SEO работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в SEO тесте: {e}")
        return False

def run_stress_test():
    """Стресс-тест системы"""
    print("\n💪 Стресс-тестирование...")
    
    try:
        import time
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        def stress_task(task_id):
            """Задача для стресс-теста"""
            start_time = time.time()
            
            # Симуляция нагрузки
            for i in range(100):
                # Простые вычисления
                result = sum(range(i))
                
            end_time = time.time()
            return f"Задача {task_id}: {end_time - start_time:.3f}s"
        
        # Запуск множественных задач
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(stress_task, i) for i in range(50)]
            results = [future.result() for future in futures]
        
        print(f"✅ Выполнено {len(results)} задач параллельно")
        
        # Тест памяти
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"✅ Использование памяти: {memory_mb:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в стресс-тесте: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ БЛОГА")
    print("=" * 50)
    
    tests = [
        ("Базовая функциональность", test_basic_functionality),
        ("ИИ система", test_ai_system),
        ("Безопасность", test_security),
        ("Мониторинг", test_monitoring),
        ("SEO", test_seo),
        ("Стресс-тест", run_stress_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🏆 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Требуется доработка.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)