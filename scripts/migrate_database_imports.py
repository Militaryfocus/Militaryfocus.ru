#!/usr/bin/env python3
"""
Скрипт для автоматической миграции импортов базы данных
Заменяет 'from blog import db' на 'from blog.database import db'
"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# Директории для обработки
DIRECTORIES_TO_PROCESS = [
    'blog/models',
    'blog/routes',
    'blog/services',
    'blog'
]

# Файлы для исключения
EXCLUDE_FILES = [
    '__init__.py',
    'database.py'
]

# Паттерны для замены
PATTERNS = [
    # Основной паттерн
    (r'from blog import db\b', 'from blog.database import db'),
    # Паттерн с алиасом
    (r'from blog import db as database\b', 'from blog.database import db as database'),
    # Множественный импорт с db
    (r'from blog import ([^,\n]*),\s*db\b', r'from blog import \1\nfrom blog.database import db'),
    (r'from blog import db,\s*([^,\n]*)', r'from blog.database import db\nfrom blog import \1'),
]

def backup_file(filepath):
    """Создать резервную копию файла"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"  ✅ Создана резервная копия: {backup_path}")

def process_file(filepath):
    """Обработать один файл"""
    try:
        # Читаем содержимое файла
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, нужна ли замена
        original_content = content
        modified = False
        
        for pattern, replacement in PATTERNS:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
        
        if modified:
            # Создаем резервную копию
            backup_file(filepath)
            
            # Записываем изменения
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Обновлен файл: {filepath}")
            
            # Показываем изменения
            lines_before = original_content.split('\n')
            lines_after = content.split('\n')
            
            for i, (before, after) in enumerate(zip(lines_before, lines_after)):
                if before != after:
                    print(f"    Строка {i+1}:")
                    print(f"      - {before}")
                    print(f"      + {after}")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка обработки {filepath}: {e}")
        return False

def find_python_files(directory):
    """Найти все Python файлы в директории"""
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        # Исключаем __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and file not in EXCLUDE_FILES:
                python_files.append(os.path.join(root, file))
    
    return python_files

def analyze_imports(directory):
    """Анализировать текущие импорты"""
    print(f"\n🔍 Анализ импортов в {directory}...")
    
    files_with_old_import = []
    python_files = find_python_files(directory)
    
    for filepath in python_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем наличие старых импортов
            for pattern, _ in PATTERNS:
                if re.search(pattern, content):
                    files_with_old_import.append(filepath)
                    break
                    
        except Exception as e:
            print(f"  ❌ Ошибка анализа {filepath}: {e}")
    
    return files_with_old_import

def main():
    """Основная функция"""
    print("🚀 Скрипт миграции импортов базы данных")
    print("=" * 50)
    
    # Проверяем, что мы в корне проекта
    if not os.path.exists('blog') or not os.path.exists('app.py'):
        print("❌ Скрипт должен запускаться из корня проекта!")
        return
    
    # Анализируем текущее состояние
    all_files_to_update = []
    
    for directory in DIRECTORIES_TO_PROCESS:
        if os.path.exists(directory):
            files = analyze_imports(directory)
            all_files_to_update.extend(files)
    
    if not all_files_to_update:
        print("\n✅ Все файлы уже используют новый импорт!")
        return
    
    print(f"\n📋 Найдено {len(all_files_to_update)} файлов для обновления:")
    for file in all_files_to_update:
        print(f"  - {file}")
    
    # Запрашиваем подтверждение
    response = input("\n❓ Продолжить миграцию? (y/N): ")
    if response.lower() != 'y':
        print("❌ Миграция отменена")
        return
    
    # Выполняем миграцию
    print("\n🔧 Выполнение миграции...")
    updated_count = 0
    
    for filepath in all_files_to_update:
        print(f"\n📄 Обработка {filepath}...")
        if process_file(filepath):
            updated_count += 1
    
    # Итоги
    print("\n" + "=" * 50)
    print(f"✅ Миграция завершена!")
    print(f"📊 Обновлено файлов: {updated_count}/{len(all_files_to_update)}")
    
    if updated_count < len(all_files_to_update):
        print(f"⚠️  Некоторые файлы не были обновлены. Проверьте логи выше.")
    
    print("\n💡 Рекомендации:")
    print("1. Проверьте изменения: git diff")
    print("2. Запустите приложение для проверки: python app.py")
    print("3. Если все работает, закоммитьте изменения")
    print("4. Если есть проблемы, восстановите из резервных копий (.backup_*)")

if __name__ == "__main__":
    main()