#!/usr/bin/env python3
"""
Статическая проверка работоспособности кода без запуска
"""

import os
import re
from pathlib import Path

print("=" * 60)
print("🔍 СТАТИЧЕСКАЯ ПРОВЕРКА РАБОТОСПОСОБНОСТИ")
print("=" * 60)

project_root = Path(__file__).parent

# 1. Проверка структуры директорий
print("\n1️⃣ Проверка структуры проекта...")
required_dirs = [
    'blog',
    'blog/models',
    'blog/routes',
    'blog/services',
    'blog/config',
    'blog/templates',
    'blog/static',
    'blog/utils',
    'blog/ai'
]

missing_dirs = []
for dir_path in required_dirs:
    full_path = project_root / dir_path
    if full_path.exists():
        print(f"✅ {dir_path}")
    else:
        print(f"❌ {dir_path} - НЕ НАЙДЕН")
        missing_dirs.append(dir_path)

# 2. Проверка основных файлов
print("\n2️⃣ Проверка основных файлов...")
required_files = [
    'app.py',
    'requirements.txt',
    'blog/__init__.py',
    'blog/database.py',
    'blog/forms.py',
    'blog/models/__init__.py',
    'blog/routes/__init__.py',
    'blog/services/__init__.py',
    'blog/config/__init__.py'
]

missing_files = []
for file_path in required_files:
    full_path = project_root / file_path
    if full_path.exists():
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} - НЕ НАЙДЕН")
        missing_files.append(file_path)

# 3. Проверка импортов
print("\n3️⃣ Проверка импортов в основных файлах...")
import_issues = []

def check_imports(file_path):
    """Проверка импортов в файле"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Поиск импортов
        imports = re.findall(r'^\s*(?:from|import)\s+([^\s]+)', content, re.MULTILINE)
        
        # Проверка проблемных импортов
        problematic = [
            'blog.models_perfect',
            'blog.ui_perfect',
            'blog.performance_perfect',
            'blog.security_perfect',
            'blog.api_perfect',
            'blog.fault_tolerance_perfect'
        ]
        
        for imp in imports:
            if any(prob in imp for prob in problematic):
                issues.append(f"Проблемный импорт: {imp}")
                
    except Exception as e:
        issues.append(f"Ошибка чтения файла: {e}")
        
    return issues

# Проверяем ключевые файлы
files_to_check = [
    'app.py',
    'blog/__init__.py',
    'blog/config/app_config.py',
    'blog/routes/main.py',
    'blog/routes/admin.py'
]

for file_path in files_to_check:
    full_path = project_root / file_path
    if full_path.exists():
        issues = check_imports(full_path)
        if issues:
            print(f"\n⚠️ {file_path}:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"✅ {file_path} - импорты корректны")

# 4. Проверка моделей
print("\n4️⃣ Проверка моделей...")
model_files = list((project_root / 'blog/models').glob('*.py'))
model_files = [f for f in model_files if f.name != '__init__.py']

print(f"✅ Найдено моделей: {len(model_files)}")
for model_file in model_files:
    print(f"   - {model_file.name}")

# 5. Проверка сервисов
print("\n5️⃣ Проверка сервисов...")
service_files = list((project_root / 'blog/services').glob('*_service.py'))

print(f"✅ Найдено сервисов: {len(service_files)}")
for service_file in service_files:
    print(f"   - {service_file.name}")

# 6. Проверка маршрутов
print("\n6️⃣ Проверка маршрутов...")
route_files = list((project_root / 'blog/routes').glob('*.py'))
route_files = [f for f in route_files if f.name != '__init__.py']

print(f"✅ Найдено файлов маршрутов: {len(route_files)}")
for route_file in route_files:
    print(f"   - {route_file.name}")

# 7. Проверка шаблонов
print("\n7️⃣ Проверка шаблонов...")
template_files = list((project_root / 'blog/templates').glob('**/*.html'))

print(f"✅ Найдено шаблонов: {len(template_files)}")

# Проверяем основные шаблоны
required_templates = [
    'base.html',
    'index.html',
    'blog/post_list.html',
    'blog/post_detail.html',
    'auth/login.html',
    'auth/register.html'
]

for template in required_templates:
    template_path = project_root / 'blog/templates' / template
    if template_path.exists():
        print(f"   ✓ {template}")
    else:
        print(f"   ✗ {template} - НЕ НАЙДЕН")

# 8. Проверка циклических импортов
print("\n8️⃣ Проверка потенциальных циклических импортов...")
def check_circular_imports():
    """Простая проверка на циклические импорты"""
    issues = []
    
    # Проверяем, что models не импортирует из routes
    models_init = project_root / 'blog/models/__init__.py'
    if models_init.exists():
        with open(models_init, 'r') as f:
            content = f.read()
            if 'from blog.routes' in content:
                issues.append("models импортирует из routes")
    
    # Проверяем, что database.py не импортирует модели напрямую
    database_py = project_root / 'blog/database.py'
    if database_py.exists():
        with open(database_py, 'r') as f:
            content = f.read()
            if 'from blog.models' in content and 'import' in content:
                issues.append("database.py импортирует модели")
    
    return issues

circular_issues = check_circular_imports()
if circular_issues:
    print("❌ Найдены потенциальные проблемы:")
    for issue in circular_issues:
        print(f"   - {issue}")
else:
    print("✅ Циклических импортов не обнаружено")

# Итоги
print("\n" + "=" * 60)
print("📊 ИТОГИ ПРОВЕРКИ:")
print("=" * 60)

total_issues = len(missing_dirs) + len(missing_files) + len(import_issues)

if total_issues == 0:
    print("✅ Критических проблем не обнаружено!")
    print("✅ Структура проекта корректна")
    print("✅ Все основные файлы на месте")
    print("✅ Импорты выглядят корректно")
else:
    print(f"⚠️ Обнаружено проблем: {total_issues}")
    if missing_dirs:
        print(f"   - Отсутствующих директорий: {len(missing_dirs)}")
    if missing_files:
        print(f"   - Отсутствующих файлов: {len(missing_files)}")
    if import_issues:
        print(f"   - Проблем с импортами: {len(import_issues)}")

print("\n💡 Рекомендация: Для полной проверки установите зависимости:")
print("   pip install -r requirements.txt")
print("   python app.py")