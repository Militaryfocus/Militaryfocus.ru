#!/usr/bin/env python3
"""
Скрипт для запуска тестов
"""

import subprocess
import sys
import os

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов...")
    
    # Проверяем что мы в правильной директории
    if not os.path.exists('tests.py'):
        print("❌ Файл tests.py не найден. Запустите скрипт из корневой директории проекта.")
        return False
    
    try:
        # Запускаем pytest
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests.py', 
            '-v', 
            '--tb=short',
            '--cov=blog',
            '--cov-report=html',
            '--cov-report=term-missing'
        ], capture_output=True, text=True)
        
        print("📊 Результаты тестов:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Предупреждения:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Все тесты прошли успешно!")
            print("📈 Отчет о покрытии кода сохранен в htmlcov/index.html")
            return True
        else:
            print("❌ Некоторые тесты не прошли")
            return False
            
    except FileNotFoundError:
        print("❌ pytest не установлен. Установите его командой:")
        print("pip install pytest pytest-cov")
        return False
    except Exception as e:
        print(f"❌ Ошибка запуска тестов: {e}")
        return False

def run_linting():
    """Запуск проверки кода"""
    print("\n🔍 Проверка кода...")
    
    try:
        # Запускаем flake8
        result = subprocess.run([
            sys.executable, '-m', 'flake8', 
            'blog/', 
            'app.py', 
            'ai_manager.py',
            '--max-line-length=120',
            '--ignore=E203,W503'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Код соответствует стандартам!")
            return True
        else:
            print("⚠️ Найдены проблемы в коде:")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("❌ flake8 не установлен. Установите его командой:")
        print("pip install flake8")
        return False

def run_type_checking():
    """Запуск проверки типов"""
    print("\n🔍 Проверка типов...")
    
    try:
        # Запускаем mypy
        result = subprocess.run([
            sys.executable, '-m', 'mypy', 
            'blog/', 
            '--ignore-missing-imports',
            '--no-strict-optional'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Проверка типов прошла успешно!")
            return True
        else:
            print("⚠️ Найдены проблемы с типами:")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("❌ mypy не установлен. Установите его командой:")
        print("pip install mypy")
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск полной проверки проекта")
    print("=" * 50)
    
    success = True
    
    # Запускаем тесты
    if not run_tests():
        success = False
    
    # Запускаем проверку кода
    if not run_linting():
        success = False
    
    # Запускаем проверку типов
    if not run_type_checking():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Все проверки прошли успешно!")
        print("Проект готов к продакшену!")
    else:
        print("⚠️ Некоторые проверки не прошли")
        print("Исправьте найденные проблемы перед деплоем")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)