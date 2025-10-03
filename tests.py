"""
Система тестирования для блога
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import create_app, db
from blog.models import User, Post, Category, Comment, Tag
from blog.security import validate_password_strength, sanitize_input, check_content_safety
from blog.autonomous_ai import AutonomousContentManager

class TestConfig:
    """Конфигурация для тестирования"""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'null'
    RATELIMIT_ENABLED = False

class BaseTestCase(unittest.TestCase):
    """Базовый класс для тестов"""
    
    def setUp(self):
        """Настройка для каждого теста"""
        self.app = create_app('testing')
        self.app.config.from_object(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Создаем тестовую базу данных
        db.create_all()
        
        # Создаем тестового пользователя
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            is_admin=True
        )
        self.test_user.set_password('testpassword123')
        db.session.add(self.test_user)
        db.session.commit()
        
        # Создаем тестовую категорию
        self.test_category = Category(
            name='Тестовая категория',
            description='Категория для тестирования',
            color='#007bff'
        )
        db.session.add(self.test_category)
        db.session.commit()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

class TestUserModel(BaseTestCase):
    """Тесты модели пользователя"""
    
    def test_user_creation(self):
        """Тест создания пользователя"""
        user = User(
            username='newuser',
            email='new@example.com'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_user_password_hashing(self):
        """Тест хеширования пароля"""
        user = User(username='test', email='test@test.com')
        user.set_password('password123')
        
        # Пароль должен быть захеширован
        self.assertNotEqual(user.password_hash, 'password123')
        self.assertTrue(user.password_hash)
    
    def test_user_full_name(self):
        """Тест получения полного имени"""
        user = User(
            username='testuser',
            first_name='Иван',
            last_name='Петров'
        )
        
        self.assertEqual(user.get_full_name(), 'Иван Петров')
        
        # Без имени и фамилии
        user.first_name = None
        user.last_name = None
        self.assertEqual(user.get_full_name(), 'testuser')

class TestPostModel(BaseTestCase):
    """Тесты модели поста"""
    
    def test_post_creation(self):
        """Тест создания поста"""
        post = Post(
            title='Тестовый пост',
            content='Содержание тестового поста',
            author_id=self.test_user.id,
            category_id=self.test_category.id,
            is_published=True
        )
        
        db.session.add(post)
        db.session.commit()
        
        self.assertEqual(post.title, 'Тестовый пост')
        self.assertEqual(post.author_id, self.test_user.id)
        self.assertEqual(post.category_id, self.test_category.id)
        self.assertTrue(post.is_published)
    
    def test_post_slug_generation(self):
        """Тест генерации slug"""
        post = Post(
            title='Тестовый пост с пробелами',
            content='Содержание',
            author_id=self.test_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        self.assertEqual(post.slug, 'testovyy-post-s-probelami')
    
    def test_post_reading_time(self):
        """Тест расчета времени чтения"""
        post = Post(
            title='Тест',
            content=' '.join(['слово'] * 400),  # 400 слов
            author_id=self.test_user.id
        )
        
        # 400 слов / 200 слов в минуту = 2 минуты
        self.assertEqual(post.get_reading_time(), 2)

class TestCategoryModel(BaseTestCase):
    """Тесты модели категории"""
    
    def test_category_creation(self):
        """Тест создания категории"""
        category = Category(
            name='Новая категория',
            description='Описание новой категории',
            color='#28a745'
        )
        
        db.session.add(category)
        db.session.commit()
        
        self.assertEqual(category.name, 'Новая категория')
        self.assertEqual(category.color, '#28a745')
    
    def test_category_slug_generation(self):
        """Тест генерации slug для категории"""
        category = Category(name='Категория с пробелами')
        
        self.assertEqual(category.slug, 'kategoriya-s-probelami')
    
    def test_category_posts_count(self):
        """Тест подсчета постов в категории"""
        # Создаем пост в категории
        post = Post(
            title='Тест',
            content='Содержание',
            author_id=self.test_user.id,
            category_id=self.test_category.id,
            is_published=True
        )
        db.session.add(post)
        db.session.commit()
        
        self.assertEqual(self.test_category.get_posts_count(), 1)

class TestSecurity(BaseTestCase):
    """Тесты безопасности"""
    
    def test_password_validation(self):
        """Тест валидации пароля"""
        # Слабый пароль
        weak_errors = validate_password_strength('123')
        self.assertTrue(len(weak_errors) > 0)
        
        # Сильный пароль
        strong_errors = validate_password_strength('Password123!')
        self.assertEqual(len(strong_errors), 0)
    
    def test_input_sanitization(self):
        """Тест санитизации ввода"""
        malicious_input = '<script>alert("xss")</script>Hello'
        sanitized = sanitize_input(malicious_input)
        
        self.assertNotIn('<script>', sanitized)
        self.assertIn('Hello', sanitized)
    
    def test_content_safety(self):
        """Тест проверки безопасности контента"""
        # Безопасный контент
        safe_content = 'Это обычный текст без подозрительных слов'
        is_safe, warnings = check_content_safety(safe_content)
        
        self.assertTrue(is_safe)
        self.assertEqual(len(warnings), 0)
        
        # Подозрительный контент
        suspicious_content = 'Этот контент содержит слово spam'
        is_safe, warnings = check_content_safety(suspicious_content)
        
        self.assertFalse(is_safe)
        self.assertTrue(len(warnings) > 0)

class TestAutonomousAI(BaseTestCase):
    """Тесты автономной ИИ системы"""
    
    def test_autonomous_manager_initialization(self):
        """Тест инициализации автономного менеджера"""
        manager = AutonomousContentManager()
        
        self.assertIsNotNone(manager.ai_generator)
        self.assertIsNotNone(manager.category_manager)
        self.assertIsNotNone(manager.tag_manager)
        self.assertIsNotNone(manager.trend_analyzer)
    
    def test_trend_analysis(self):
        """Тест анализа трендов"""
        manager = AutonomousContentManager()
        trends = manager.trend_analyzer.analyze_current_trends()
        
        self.assertIsInstance(trends, list)
        self.assertTrue(len(trends) > 0)
        
        # Проверяем структуру тренда
        if trends:
            trend = trends[0]
            self.assertIn('topic', trend)
            self.assertIn('category', trend)
            self.assertIn('source', trend)

class TestAPI(BaseTestCase):
    """Тесты API"""
    
    def setUp(self):
        super().setUp()
        self.client = self.app.test_client()
    
    def test_home_page(self):
        """Тест главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """Тест страницы входа"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_protection(self):
        """Тест защиты админ-панели"""
        response = self.client.get('/admin/dashboard')
        # Должен перенаправить на страницу входа
        self.assertEqual(response.status_code, 302)

def run_tests():
    """Запуск всех тестов"""
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestUserModel))
    suite.addTests(loader.loadTestsFromTestCase(TestPostModel))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModel))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestAutonomousAI))
    suite.addTests(loader.loadTestsFromTestCase(TestAPI))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)