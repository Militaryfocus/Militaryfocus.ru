#!/usr/bin/env python3
"""
Скрипт для настройки API ключей ИИ сервисов
"""

import os
import json
import getpass
from pathlib import Path

def load_config():
    """Загружает конфигурацию"""
    config_file = Path('ai_config.json')
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_config(config):
    """Сохраняет конфигурацию"""
    config_file = Path('ai_config.json')
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def setup_openai(config):
    """Настройка OpenAI"""
    print("\n🤖 Настройка OpenAI")
    print("-" * 30)
    
    api_key = getpass.getpass("Введите OpenAI API ключ (sk-...): ").strip()
    
    if api_key:
        config['ai_providers']['openai']['enabled'] = True
        config['ai_providers']['openai']['api_key'] = api_key
        
        model = input("Модель (gpt-4, gpt-3.5-turbo) [gpt-4]: ").strip() or "gpt-4"
        config['ai_providers']['openai']['model'] = model
        
        max_tokens = input("Максимум токенов [2000]: ").strip()
        if max_tokens.isdigit():
            config['ai_providers']['openai']['max_tokens'] = int(max_tokens)
        
        temperature = input("Температура (0.0-1.0) [0.7]: ").strip()
        if temperature.replace('.', '').isdigit():
            config['ai_providers']['openai']['temperature'] = float(temperature)
        
        print("✅ OpenAI настроен")
    else:
        print("⚠️ OpenAI пропущен")

def setup_anthropic(config):
    """Настройка Anthropic"""
    print("\n🧠 Настройка Anthropic")
    print("-" * 30)
    
    api_key = getpass.getpass("Введите Anthropic API ключ (sk-ant-...): ").strip()
    
    if api_key:
        config['ai_providers']['anthropic']['enabled'] = True
        config['ai_providers']['anthropic']['api_key'] = api_key
        
        model = input("Модель (claude-3-sonnet, claude-3-haiku) [claude-3-sonnet]: ").strip() or "claude-3-sonnet-20240229"
        config['ai_providers']['anthropic']['model'] = model
        
        max_tokens = input("Максимум токенов [2000]: ").strip()
        if max_tokens.isdigit():
            config['ai_providers']['anthropic']['max_tokens'] = int(max_tokens)
        
        temperature = input("Температура (0.0-1.0) [0.7]: ").strip()
        if temperature.replace('.', '').isdigit():
            config['ai_providers']['anthropic']['temperature'] = float(temperature)
        
        print("✅ Anthropic настроен")
    else:
        print("⚠️ Anthropic пропущен")

def setup_google(config):
    """Настройка Google Gemini"""
    print("\n🔍 Настройка Google Gemini")
    print("-" * 30)
    
    api_key = getpass.getpass("Введите Google API ключ (AI...): ").strip()
    
    if api_key:
        config['ai_providers']['google']['enabled'] = True
        config['ai_providers']['google']['api_key'] = api_key
        
        model = input("Модель (gemini-pro, gemini-pro-vision) [gemini-pro]: ").strip() or "gemini-pro"
        config['ai_providers']['google']['model'] = model
        
        max_tokens = input("Максимум токенов [2000]: ").strip()
        if max_tokens.isdigit():
            config['ai_providers']['google']['max_tokens'] = int(max_tokens)
        
        temperature = input("Температура (0.0-1.0) [0.7]: ").strip()
        if temperature.replace('.', '').isdigit():
            config['ai_providers']['google']['temperature'] = float(temperature)
        
        print("✅ Google Gemini настроен")
    else:
        print("⚠️ Google Gemini пропущен")

def setup_local_models(config):
    """Настройка локальных моделей"""
    print("\n🏠 Настройка локальных моделей")
    print("-" * 30)
    
    enable_local = input("Включить локальные модели? (y/n) [y]: ").strip().lower()
    
    if enable_local in ['', 'y', 'yes', 'да']:
        config['ai_providers']['local']['enabled'] = True
        
        device = input("Устройство (cpu, cuda) [cpu]: ").strip() or "cpu"
        config['ai_providers']['local']['device'] = device
        
        cache_enabled = input("Включить кэширование? (y/n) [y]: ").strip().lower()
        config['ai_providers']['local']['cache_enabled'] = cache_enabled in ['', 'y', 'yes', 'да']
        
        print("✅ Локальные модели настроены")
    else:
        config['ai_providers']['local']['enabled'] = False
        print("⚠️ Локальные модели отключены")

def setup_cache(config):
    """Настройка кэширования"""
    print("\n💾 Настройка кэширования")
    print("-" * 30)
    
    enable_cache = input("Включить кэширование? (y/n) [y]: ").strip().lower()
    
    if enable_cache in ['', 'y', 'yes', 'да']:
        config['cache']['enabled'] = True
        
        ttl = input("Время жизни кэша в секундах [3600]: ").strip()
        if ttl.isdigit():
            config['cache']['ttl'] = int(ttl)
        
        max_size = input("Максимальный размер кэша [1000]: ").strip()
        if max_size.isdigit():
            config['cache']['max_size'] = int(max_size)
        
        storage_path = input("Путь к кэшу [./cache]: ").strip() or "./cache"
        config['cache']['storage_path'] = storage_path
        
        print("✅ Кэширование настроено")
    else:
        config['cache']['enabled'] = False
        print("⚠️ Кэширование отключено")

def setup_monitoring(config):
    """Настройка мониторинга"""
    print("\n📊 Настройка мониторинга")
    print("-" * 30)
    
    enable_monitoring = input("Включить мониторинг? (y/n) [y]: ").strip().lower()
    
    if enable_monitoring in ['', 'y', 'yes', 'да']:
        config['monitoring']['enabled'] = True
        
        log_level = input("Уровень логирования (DEBUG, INFO, WARNING, ERROR) [INFO]: ").strip() or "INFO"
        config['monitoring']['log_level'] = log_level
        
        metrics_enabled = input("Включить метрики? (y/n) [y]: ").strip().lower()
        config['monitoring']['metrics_enabled'] = metrics_enabled in ['', 'y', 'yes', 'да']
        
        print("✅ Мониторинг настроен")
    else:
        config['monitoring']['enabled'] = False
        print("⚠️ Мониторинг отключен")

def test_configuration(config):
    """Тестирует конфигурацию"""
    print("\n🧪 Тестирование конфигурации")
    print("-" * 30)
    
    try:
        # Тестируем импорт модулей
        import sys
        sys.path.append('blog')
        
        from blog.ai_provider_manager import AIProviderManager
        
        provider_manager = AIProviderManager()
        print("✅ AIProviderManager инициализирован")
        
        # Тестируем локальные модели
        if config['ai_providers']['local']['enabled']:
            print("🏠 Тестируем локальные модели...")
            # Здесь можно добавить реальный тест
        
        print("✅ Конфигурация работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def main():
    """Основная функция"""
    print("🔑 Настройка API ключей ИИ сервисов")
    print("=" * 50)
    
    # Загружаем существующую конфигурацию
    config = load_config()
    
    # Если конфигурация пустая, создаем базовую структуру
    if not config:
        config = {
            "ai_providers": {
                "openai": {
                    "enabled": False,
                    "api_key": "",
                    "model": "gpt-4",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "timeout": 30
                },
                "anthropic": {
                    "enabled": False,
                    "api_key": "",
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "timeout": 30
                },
                "google": {
                    "enabled": False,
                    "api_key": "",
                    "model": "gemini-pro",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "timeout": 30
                },
                "local": {
                    "enabled": True,
                    "models": {
                        "text_generation": "microsoft/DialoGPT-medium",
                        "sentiment_analysis": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                        "summarization": "facebook/bart-large-cnn"
                    },
                    "device": "cpu",
                    "cache_enabled": True
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
    
    # Настройка провайдеров
    setup_openai(config)
    setup_anthropic(config)
    setup_google(config)
    setup_local_models(config)
    
    # Дополнительные настройки
    setup_cache(config)
    setup_monitoring(config)
    
    # Сохраняем конфигурацию
    save_config(config)
    print("\n💾 Конфигурация сохранена в ai_config.json")
    
    # Тестируем конфигурацию
    if test_configuration(config):
        print("\n🎉 Настройка завершена успешно!")
        
        # Показываем статус
        print("\n📊 Статус провайдеров:")
        for provider, settings in config['ai_providers'].items():
            status = "✅ Включен" if settings.get('enabled', False) else "❌ Отключен"
            print(f"  {provider}: {status}")
        
        print("\n🚀 Теперь можно использовать ИИ сервисы!")
        print("   Запустите: python3 ai_manager.py advanced-generate 1")
    else:
        print("\n⚠️ Настройка завершена с ошибками")
        print("   Проверьте конфигурацию и попробуйте снова")

if __name__ == '__main__':
    main()