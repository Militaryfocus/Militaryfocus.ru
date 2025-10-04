#!/usr/bin/env python3
"""
Простой тест для проверки базовой функциональности
"""

import unittest
import os
import tempfile
from flask import Flask
from blog import create_app, db
from blog.models_perfect import User, Post, Category, Comment

class SimpleBlogTest(unittest.TestCase):
    """Простой тест блога"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        # Создаем временную базу данных
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Настраиваем тестовое окружение
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['DATABASE_URL'] = f'sqlite:///{self.db_path}'
        os.environ['FLASK_DEBUG'] = 'False'
        os.environ['CSRF_ENABLED'] = 'False'
        
        # Создаем приложение
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self.create_test_data()
    
    def tearDown(self):
        """Очистка после тестов"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def create_test_data(self):
        """Создание тестовых данных"""
        # Создаем тестового пользователя
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.test_user.set_password('testpass')
        db.session.add(self.test_user)
        
        # Создаем тестовую категорию
        self.test_category = Category(
            name='Тестовая категория',
            description='Описание тестовой категории'
        )
        db.session.add(self.test_category)
        
        # Создаем тестовый пост
        self.test_post = Post(
            title='Тестовый пост',
            content='Содержимое тестового поста',
            excerpt='Краткое описание тестового поста',
            author_id=self.test_user.id,
            category_id=self.test_category.id,
            is_published=True
        )
        db.session.add(self.test_post)
        
        db.session.commit()
    
    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.test_user.username, 'testuser')
        self.assertEqual(self.test_user.email, 'test@example.com')
        self.assertTrue(self.test_user.check_password('testpass'))
        self.assertFalse(self.test_user.check_password('wrongpass'))
    
    def test_post_creation(self):
        """Тест создания поста"""
        self.assertEqual(self.test_post.title, 'Тестовый пост')
        self.assertEqual(self.test_post.author.username, 'testuser')
        self.assertEqual(self.test_post.category.name, 'Тестовая категория')
        self.assertTrue(self.test_post.is_published)
    
    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.test_category.name, 'Тестовая категория')
        self.assertEqual(self.test_category.description, 'Описание тестовой категории')
    
    def test_homepage(self):
        """Тест главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Тестовый пост', response.data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()