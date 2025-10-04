"""
Модель пользователя
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON
from blog.database import db

class User(UserMixin, db.Model):
    """Модель пользователя с расширенным функционалом"""
    __tablename__ = 'users'
    
    # Основные поля
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Профиль
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(255))
    website = db.Column(db.String(255))
    location = db.Column(db.String(100))
    birth_date = db.Column(db.Date)
    
    # Настройки
    is_admin = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=True)
    privacy_settings = db.Column(JSON, default=lambda: {
        'show_email': False,
        'show_location': False,
        'show_birth_date': False,
        'allow_messages': True
    })
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_login = db.Column(db.DateTime)
    
    # Безопасность
    email_verification_token = db.Column(db.String(255))
    password_reset_token = db.Column(db.String(255))
    password_reset_expires = db.Column(db.DateTime)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(255))
    
    # Статистика
    login_count = db.Column(db.Integer, default=0)
    posts_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    reputation_score = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Связи
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='notification_user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='session_user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Индексы
    __table_args__ = (
        db.Index('idx_user_username', 'username'),
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_active', 'is_active'),
        db.Index('idx_user_admin', 'is_admin'),
        db.Index('idx_user_created', 'created_at'),
    )
    
    def set_password(self, password):
        """Установка пароля"""
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Получение полного имени"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_authenticated(self):
        """Проверка аутентификации"""
        return True
    
    def is_anonymous(self):
        """Проверка анонимности"""
        return False
    
    def get_id(self):
        """Получение ID пользователя"""
        return str(self.id)
    
    def update_last_seen(self):
        """Обновление времени последнего посещения"""
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def increment_login_count(self):
        """Увеличение счетчика входов"""
        self.login_count += 1
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def can_edit_post(self, post):
        """Проверка права редактирования поста"""
        return self.is_admin or self.id == post.author_id
    
    def can_delete_post(self, post):
        """Проверка права удаления поста"""
        return self.is_admin or self.id == post.author_id
    
    def can_moderate_comments(self):
        """Проверка права модерации комментариев"""
        return self.is_admin
    
    def __repr__(self):
        return f'<User {self.username}>'