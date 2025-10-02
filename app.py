#!/usr/bin/env python3
"""
Ядро блога на Python Flask
Современное веб-приложение с полным функционалом блога
"""

import os
from dotenv import load_dotenv
from blog import create_app, db
from blog.models import User, Post, Category, Comment

# Загружаем переменные окружения
load_dotenv()

# Создаем приложение
app = create_app()

# Контекст для работы с базой данных в shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Post': Post,
        'Category': Category,
        'Comment': Comment
    }

if __name__ == '__main__':
    with app.app_context():
        # Создаем таблицы базы данных
        db.create_all()
        
        # Создаем администратора по умолчанию, если его нет
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@blog.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Создан администратор: admin / admin123")
    
    # Запускаем приложение
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    )