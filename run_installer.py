#!/usr/bin/env python3
"""
Быстрый запуск автоустановщика ИИ-блога
"""

import os
import sys
import webbrowser
import time
import subprocess
from threading import Timer

def open_browser():
    """Открывает браузер через 2 секунды"""
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

def main():
    print("🚀 Автоустановщик ИИ-блога")
    print("=" * 50)
    
    # Проверяем наличие необходимых файлов
    required_files = ['installer.html', 'installer_server.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return
    
    print("✅ Все файлы установщика найдены")
    
    # Устанавливаем Flask-CORS если нужно
    try:
        import flask_cors
    except ImportError:
        print("📦 Устанавливаем Flask-CORS...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask-cors'], check=True)
        print("✅ Flask-CORS установлен")
    
    print("\n🌐 Запускаем веб-интерфейс установщика...")
    print("📱 Браузер откроется автоматически через 2 секунды")
    print("🔗 Или перейдите по адресу: http://localhost:8080")
    print("\n" + "=" * 50)
    
    # Запускаем браузер в отдельном потоке
    Timer(0, open_browser).start()
    
    # Запускаем сервер установщика
    try:
        subprocess.run([sys.executable, 'installer_server.py'], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Установщик остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска установщика: {e}")

if __name__ == '__main__':
    main()