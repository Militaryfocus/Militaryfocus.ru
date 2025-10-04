#!/usr/bin/env python3
"""
Тест локального ИИ провайдера
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
from blog.ai_content_perfect import PerfectAIContentGenerator, AIRequest, AIProvider, ContentType

def test_local_ai():
    """Тест локального ИИ провайдера"""
    print("🤖 Тестирование локального ИИ провайдера...")
    
    # Создаем контекст приложения
    app = create_app()
    
    with app.app_context():
        # Создаем таблицы базы данных
        db.create_all()
        
        # Инициализируем ИИ генератор
        print("\n🔧 Инициализация ИИ генератора...")
        ai_generator = PerfectAIContentGenerator()
        
        # Тестируем генерацию заголовка с локальным провайдером
        print("\n📝 Тест 1: Генерация заголовка (локальный провайдер)...")
        try:
            request = AIRequest(
                prompt="Создай привлекательный заголовок для статьи на тему 'Искусственный интеллект в веб-разработке' на русском языке",
                content_type=ContentType.TITLE,
                provider=AIProvider.LOCAL,
                max_tokens=100,
                temperature=0.8,
                language='ru'
            )
            
            # Синхронная генерация
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(ai_generator.generate_content(request))
                print(f"✅ Заголовок сгенерирован: {response.content}")
                print(f"📊 Статистика: {response.tokens_used} токенов, качество: {response.quality_score}")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Ошибка генерации заголовка: {e}")
        
        # Тестируем генерацию контента с локальным провайдером
        print("\n📄 Тест 2: Генерация контента (локальный провайдер)...")
        try:
            request = AIRequest(
                prompt="Напиши подробную статью на тему 'Искусственный интеллект в веб-разработке' на русском языке. Длина статьи должна быть примерно 500 слов.",
                content_type=ContentType.POST,
                provider=AIProvider.LOCAL,
                max_tokens=500,
                temperature=0.7,
                language='ru'
            )
            
            # Синхронная генерация
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(ai_generator.generate_content(request))
                print(f"✅ Контент сгенерирован (длина: {len(response.content)} символов)")
                print(f"📖 Превью: {response.content[:200]}...")
                print(f"📊 Статистика: {response.tokens_used} токенов, качество: {response.quality_score}")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Ошибка генерации контента: {e}")
        
        # Тестируем генерацию тегов с локальным провайдером
        print("\n🏷️ Тест 3: Генерация тегов (локальный провайдер)...")
        try:
            request = AIRequest(
                prompt="Создай 5 релевантных тегов для статьи об искусственном интеллекте в веб-разработке на русском языке",
                content_type=ContentType.TAG,
                provider=AIProvider.LOCAL,
                max_tokens=100,
                temperature=0.5,
                language='ru'
            )
            
            # Синхронная генерация
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(ai_generator.generate_content(request))
                print(f"✅ Теги сгенерированы: {response.content}")
                print(f"📊 Статистика: {response.tokens_used} токенов, качество: {response.quality_score}")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Ошибка генерации тегов: {e}")
        
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
        
        print("\n🎉 Тестирование локального ИИ провайдера завершено!")
        print("=" * 50)

if __name__ == '__main__':
    test_local_ai()