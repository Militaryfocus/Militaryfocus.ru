#!/usr/bin/env python3
"""
Проверка синтаксиса всех Python файлов
"""

import ast
import os
from pathlib import Path

print("=" * 60)
print("🐍 ПРОВЕРКА СИНТАКСИСА PYTHON ФАЙЛОВ")
print("=" * 60)

errors = []
checked = 0

# Проходим по всем Python файлам
for root, dirs, files in os.walk('blog'):
    # Пропускаем __pycache__
    if '__pycache__' in root:
        continue
        
    for file in files:
        if file.endswith('.py'):
            file_path = Path(root) / file
            checked += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Компилируем AST для проверки синтаксиса
                ast.parse(content)
                print(f"✅ {file_path}")
                
            except SyntaxError as e:
                error_msg = f"❌ {file_path}: Синтаксическая ошибка на строке {e.lineno}: {e.msg}"
                print(error_msg)
                errors.append(error_msg)
                
            except Exception as e:
                error_msg = f"❌ {file_path}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)

# Проверяем основные файлы в корне
root_files = ['app.py', 'install.py', 'ai_manager.py']
for file in root_files:
    if Path(file).exists():
        checked += 1
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ {file}")
        except SyntaxError as e:
            error_msg = f"❌ {file}: Синтаксическая ошибка на строке {e.lineno}: {e.msg}"
            print(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"❌ {file}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)

print("\n" + "=" * 60)
print(f"Проверено файлов: {checked}")
print(f"Найдено ошибок: {len(errors)}")

if errors:
    print("\n⚠️ ОБНАРУЖЕНЫ ОШИБКИ:")
    for error in errors:
        print(f"  {error}")
else:
    print("\n✅ ВСЕ ФАЙЛЫ ИМЕЮТ КОРРЕКТНЫЙ СИНТАКСИС!")

print("=" * 60)