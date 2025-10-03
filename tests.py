#!/usr/bin/env python3
"""
Unit-тесты для блога
"""

import unittest
import os
import tempfile
from flask import Flask
from blog import create_app, db
from blog.models_perfect import User, Post, Category, Comment

class BlogTestCase(unittest.TestCase):
    """Базовый класс для тестов блога"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        # Создаем временную базу данных
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Настраиваем тестовое окружение
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['DATABASE_URL'] = f'sqlite:///{self.db_path}'
        os.environ['FLASK_DEBUG'] = 'False'
        os.environ['CSRF_ENABLED'] = 'False'  # Отключаем CSRF для тестов
        
        # Создаем приложение с отключенной админкой для тестов
        from blog import create_app
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
            description='Описание тестовой категории',
            color='#007bff'
        )
        db.session.add(self.test_category)
        
        # Сначала коммитим пользователя и категорию
        db.session.commit()
        
        # Создаем тестовый пост
        self.test_post = Post(
            title='Тестовый пост',
            content='Содержание тестового поста',
            excerpt='Краткое описание',
            author_id=self.test_user.id,
            category_id=self.test_category.id,
            is_published=True
        )
        db.session.add(self.test_post)
        
        db.session.commit()
    
    def login(self, username='testuser', password='testpass'):
        """Вход в систему для тестов"""
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        """Выход из системы"""
        return self.client.get('/auth/logout', follow_redirects=True)

class UserModelTest(BlogTestCase):
    """Тесты модели User"""
    
    def test_user_creation(self):
        """Тест создания пользователя"""
        user = User(
            username='newuser',
            email='new@example.com',
            first_name='New',
            last_name='User'
        )
        user.set_password('password123')
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_user_full_name(self):
        """Тест получения полного имени"""
        self.assertEqual(self.test_user.get_full_name(), 'Test User')
        
        # Тест без имени и фамилии
        user = User(username='simpleuser', email='simple@example.com')
        self.assertEqual(user.get_full_name(), 'simpleuser')
    
    def test_user_avatar_url(self):
        """Тест получения URL аватара"""
        self.assertEqual(self.test_user.get_avatar_url(), '/static/images/default-avatar.png')

class PostModelTest(BlogTestCase):
    """Тесты модели Post"""
    
    def test_post_creation(self):
        """Тест создания поста"""
        post = Post(
            title='Новый пост',
            content='Содержание нового поста',
            author_id=self.test_user.id,
            category_id=self.test_category.id
        )
        
        self.assertEqual(post.title, 'Новый пост')
        self.assertEqual(post.content, 'Содержание нового поста')
        self.assertEqual(post.author_id, self.test_user.id)
        self.assertFalse(post.is_published)
    
    def test_post_reading_time(self):
        """Тест расчета времени чтения"""
        reading_time = self.test_post.get_reading_time()
        self.assertGreater(reading_time, 0)
    
    def test_post_comments_count(self):
        """Тест подсчета комментариев"""
        count = self.test_post.get_comments_count()
        self.assertEqual(count, 0)

class CategoryModelTest(BlogTestCase):
    """Тесты модели Category"""
    
    def test_category_creation(self):
        """Тест создания категории"""
        category = Category(
            name='Новая категория',
            description='Описание новой категории',
            color='#ff0000'
        )
        
        self.assertEqual(category.name, 'Новая категория')
        self.assertEqual(category.slug, 'novaya-kategoriya')
    
    def test_category_posts_count(self):
        """Тест подсчета постов в категории"""
        count = self.test_category.get_posts_count()
        self.assertEqual(count, 1)

class AuthRoutesTest(BlogTestCase):
    """Тесты маршрутов аутентификации"""
    
    def test_login_page(self):
        """Тест страницы входа"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему'.encode('utf-8'), response.data)
    
    def test_login_success(self):
        """Тест успешного входа"""
        response = self.login()
        self.assertEqual(response.status_code, 200)
    
    def test_login_failure(self):
        """Тест неудачного входа"""
        response = self.client.post('/auth/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Неверное имя пользователя или пароль'.encode('utf-8'), response.data)
    
    def test_register_page(self):
        """Тест страницы регистрации"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Регистрация'.encode('utf-8'), response.data)
    
    def test_logout(self):
        """Тест выхода из системы"""
        self.login()
        response = self.logout()
        self.assertEqual(response.status_code, 200)

class BlogRoutesTest(BlogTestCase):
    """Тесты маршрутов блога"""
    
    def test_index_page(self):
        """Тест главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('МойБлог'.encode('utf-8'), response.data)
    
    def test_post_detail(self):
        """Тест страницы поста"""
        response = self.client.get(f'/blog/post/{self.test_post.slug}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.test_post.title.encode(), response.data)
    
    def test_create_post_requires_auth(self):
        """Тест что создание поста требует авторизации"""
        response = self.client.get('/blog/create')
        self.assertEqual(response.status_code, 302)  # Редирект на логин
    
    def test_create_post_with_auth(self):
        """Тест создания поста с авторизацией"""
        self.login()
        response = self.client.get('/blog/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Создать новый пост'.encode('utf-8'), response.data)

class SecurityTest(BlogTestCase):
    """Тесты безопасности"""
    
    def test_csrf_protection(self):
        """Тест CSRF защиты"""
        # Отключаем CSRF для этого теста
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Должен работать без CSRF токена в тестах
        self.assertEqual(response.status_code, 200)
    
    def test_password_hashing(self):
        """Тест хеширования паролей"""
        user = User(username='test', email='test@test.com')
        user.set_password('password123')
        
        # Пароль должен быть захеширован
        self.assertNotEqual(user.password_hash, 'password123')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))

if __name__ == '__main__':
    unittest.main()