#!/usr/bin/env python3
"""
Простой тест системы без Flask-Admin
"""

import unittest
import os
import tempfile
from flask import Flask
from blog import create_app, db
from blog.models_perfect import User, Post, Category, Comment

class SimpleSystemTest(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения"""
        os.environ['SECRET_KEY'] = 'test-secret-key'
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
        
        # Создание временной базы данных
        self.db_fd, self.app.config['DATABASE'] = tempfile.mkstemp()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            self.create_test_data()

    def tearDown(self):
        """Очистка после тестов"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(self.app.config['DATABASE'])

    def create_test_data(self):
        """Создание тестовых данных"""
        # Создание тестового пользователя
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash='test_hash'
        )
        db.session.add(self.test_user)
        
        # Создание тестовой категории
        self.test_category = Category(
            name='Тестовая категория',
            description='Описание тестовой категории'
        )
        db.session.add(self.test_category)
        
        # Создание тестового поста
        self.test_post = Post(
            title='Тестовый пост',
            content='Это очень длинное содержимое тестового поста, которое содержит более чем 50 символов для прохождения валидации.',
            excerpt='Краткое описание тестового поста',
            author=self.test_user,
            category=self.test_category,
            is_published=True
        )
        db.session.add(self.test_post)
        
        db.session.commit()

    def test_database_creation(self):
        """Тест создания базы данных"""
        with self.app.app_context():
            # Проверяем, что таблицы созданы
            inspector = db.inspect(db.engine)
            self.assertTrue(inspector.get_table_names())
            
            # Проверяем, что данные сохранены
            user = User.query.first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'testuser')
            
            category = Category.query.first()
            self.assertIsNotNone(category)
            self.assertEqual(category.name, 'Тестовая категория')
            
            post = Post.query.first()
            self.assertIsNotNone(post)
            self.assertEqual(post.title, 'Тестовый пост')

    def test_user_creation(self):
        """Тест создания пользователя"""
        with self.app.app_context():
            new_user = User(
                username='newuser',
                email='new@example.com',
                password_hash='new_hash'
            )
            db.session.add(new_user)
            db.session.commit()
            
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'new@example.com')

    def test_post_creation(self):
        """Тест создания поста"""
        with self.app.app_context():
            new_post = Post(
                title='Новый пост',
                content='Это очень длинное содержимое нового поста, которое содержит более чем 50 символов для прохождения валидации.',
                excerpt='Краткое описание нового поста',
                author=self.test_user,
                category=self.test_category,
                is_published=True
            )
            db.session.add(new_post)
            db.session.commit()
            
            post = Post.query.filter_by(title='Новый пост').first()
            self.assertIsNotNone(post)
            self.assertEqual(post.author.username, 'testuser')

    def test_category_creation(self):
        """Тест создания категории"""
        with self.app.app_context():
            new_category = Category(
                name='Новая категория',
                description='Описание новой категории'
            )
            db.session.add(new_category)
            db.session.commit()
            
            category = Category.query.filter_by(name='Новая категория').first()
            self.assertIsNotNone(category)
            self.assertEqual(category.description, 'Описание новой категории')

    def test_homepage(self):
        """Тест главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Тестовый пост', response.data.decode('utf-8'))

    def test_login_page(self):
        """Тест страницы входа"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        """Тест страницы регистрации"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()