#!/usr/bin/env python3
"""
Быстрая настройка API ключей через переменные окружения
"""

import os
import json
from pathlib import Path

def create_env_template():
    """Создает шаблон .env файла"""
    env_content = """# API ключи для ИИ сервисов
# Получите ключи на соответствующих сайтах:
# OpenAI: https://platform.openai.com/api-keys
# Anthropic: https://console.anthropic.com/
# Google: https://makersuite.google.com/app/apikey

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google Gemini
GOOGLE_API_KEY=AI-your-google-key-here

# Настройки
AI_MODEL_OPENAI=gpt-4
AI_MODEL_ANTHROPIC=claude-3-sonnet-20240229
AI_MODEL_GOOGLE=gemini-pro

# Локальные модели (всегда включены)
LOCAL_MODELS_ENABLED=true
AI_DEVICE=cpu
AI_CACHE_ENABLED=true
"""
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("📝 Создан шаблон .env.template")
    print("   Скопируйте его в .env и заполните ваши ключи")

def load_env_config():
    """Загружает конфигурацию из переменных окружения"""
    config = {
        "ai_providers": {
            "openai": {
                "enabled": bool(os.getenv('OPENAI_API_KEY')),
                "api_key": os.getenv('OPENAI_API_KEY', ''),
                "model": os.getenv('AI_MODEL_OPENAI', 'gpt-4'),
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30
            },
            "anthropic": {
                "enabled": bool(os.getenv('ANTHROPIC_API_KEY')),
                "api_key": os.getenv('ANTHROPIC_API_KEY', ''),
                "model": os.getenv('AI_MODEL_ANTHROPIC', 'claude-3-sonnet-20240229'),
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30
            },
            "google": {
                "enabled": bool(os.getenv('GOOGLE_API_KEY')),
                "api_key": os.getenv('GOOGLE_API_KEY', ''),
                "model": os.getenv('AI_MODEL_GOOGLE', 'gemini-pro'),
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30
            },
            "local": {
                "enabled": os.getenv('LOCAL_MODELS_ENABLED', 'true').lower() == 'true',
                "models": {
                    "text_generation": "microsoft/DialoGPT-medium",
                    "sentiment_analysis": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                    "summarization": "facebook/bart-large-cnn"
                },
                "device": os.getenv('AI_DEVICE', 'cpu'),
                "cache_enabled": os.getenv('AI_CACHE_ENABLED', 'true').lower() == 'true'
            }
        },
        "cache": {
            "enabled": True,
            "ttl": 3600,
            "max_size": 1000,
            "storage_path": "./cache"
        },
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": 60,
            "requests_per_hour": 1000
        },
        "monitoring": {
            "enabled": True,
            "log_level": "INFO",
            "metrics_enabled": True,
            "alert_threshold": 0.8
        },
        "security": {
            "encrypt_keys": True,
            "key_rotation_days": 90,
            "audit_logging": True
        }
    }
    
    return config

def main():
    """Основная функция"""
    print("🔑 Быстрая настройка API ключей")
    print("=" * 40)
    
    # Проверяем наличие .env файла
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️ Файл .env не найден")
        create_env_template()
        print("\n📋 Инструкции:")
        print("1. Скопируйте .env.template в .env")
        print("2. Заполните ваши API ключи")
        print("3. Запустите этот скрипт снова")
        return
    
    # Загружаем конфигурацию из переменных окружения
    config = load_env_config()
    
    # Сохраняем в ai_config.json
    with open('ai_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Конфигурация создана из переменных окружения")
    
    # Показываем статус
    print("\n📊 Статус провайдеров:")
    for provider, settings in config['ai_providers'].items():
        if provider == 'local':
            status = "✅ Включен" if settings.get('enabled', False) else "❌ Отключен"
            print(f"  {provider}: {status}")
        else:
            status = "✅ Настроен" if settings.get('enabled', False) else "❌ Не настроен"
            print(f"  {provider}: {status}")
    
    # Тестируем конфигурацию
    print("\n🧪 Тестирование...")
    try:
        import sys
        sys.path.append('blog')
        
        from blog.ai_provider_manager import AIProviderManager
        provider_manager = AIProviderManager()
        print("✅ AIProviderManager работает")
        
        print("\n🎉 Настройка завершена!")
        print("🚀 Теперь можно использовать ИИ сервисы")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        print("   Проверьте установку зависимостей")

if __name__ == '__main__':
    main()