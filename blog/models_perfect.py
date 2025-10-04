"""
Идеальные модели базы данных для блога
Включает расширенный функционал, индексы, валидацию и оптимизацию
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify
import markdown
import bleach
import re
import hashlib
import secrets
from typing import Optional, List, Dict, Any
from sqlalchemy import Index, event, func, text
from sqlalchemy.orm import validates
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import JSON
from blog import db

class User(UserMixin, db.Model):
    """Идеальная модель пользователя с расширенным функционалом"""
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
    
    # Связи
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', foreign_keys='Comment.author_id', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='bookmark_user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='notification_user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='session_user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Индексы
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
        Index('idx_user_reputation', 'reputation_score'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        """Валидация email"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()
    
    @validates('username')
    def validate_username(self, key, username):
        """Валидация имени пользователя"""
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscores only')
        return username.lower()
    
    def set_password(self, password):
        """Установка пароля с хешированием"""
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        """Генерация токена для подтверждения email"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def generate_password_reset_token(self):
        """Генерация токена для сброса пароля"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def get_full_name(self):
        """Получение полного имени"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_avatar_url(self, size=64):
        """Получение URL аватара с размером"""
        if self.avatar:
            return f"/static/uploads/avatars/{size}x{size}/{self.avatar}"
        return f"/static/images/default-avatar-{size}.png"
    
    def get_reputation_level(self):
        """Получение уровня репутации"""
        if self.reputation_score >= 1000:
            return 'expert'
        elif self.reputation_score >= 500:
            return 'advanced'
        elif self.reputation_score >= 100:
            return 'intermediate'
        else:
            return 'beginner'
    
    def update_last_seen(self):
        """Обновление времени последнего посещения"""
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def increment_login_count(self):
        """Увеличение счетчика входов"""
        self.login_count += 1
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_private=False):
        """Преобразование в словарь для API"""
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.get_full_name(),
            'avatar_url': self.get_avatar_url(),
            'reputation_score': self.reputation_score,
            'reputation_level': self.get_reputation_level(),
            'created_at': self.created_at.isoformat(),
            'posts_count': self.posts_count,
            'comments_count': self.comments_count
        }
        
        if include_private:
            data.update({
                'email': self.email,
                'bio': self.bio,
                'website': self.website,
                'location': self.location,
                'is_verified': self.is_verified,
                'last_seen': self.last_seen.isoformat()
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """Идеальная модель категории с расширенным функционалом"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')
    icon = db.Column(db.String(50))  # Font Awesome иконка
    image = db.Column(db.String(255))  # Изображение категории
    
    # SEO
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    meta_keywords = db.Column(db.Text)
    
    # Настройки
    is_active = db.Column(db.Boolean, default=True, index=True)
    sort_order = db.Column(db.Integer, default=0)
    show_in_menu = db.Column(db.Boolean, default=True)
    
    # Статистика
    posts_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    posts = db.relationship('Post', backref='category', lazy='dynamic')
    
    # Индексы
    __table_args__ = (
        Index('idx_category_active_sort', 'is_active', 'sort_order'),
        Index('idx_category_menu', 'show_in_menu', 'sort_order'),
    )
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    @validates('name')
    def validate_name(self, key, name):
        """Валидация названия категории"""
        if len(name.strip()) < 2:
            raise ValueError('Category name must be at least 2 characters long')
        return name.strip()
    
    @validates('color')
    def validate_color(self, key, color):
        """Валидация цвета"""
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError('Color must be a valid hex color')
        return color
    
    def get_posts_count(self):
        """Количество опубликованных постов в категории"""
        return self.posts.filter_by(is_published=True).count()
    
    def get_image_url(self):
        """Получение URL изображения категории"""
        if self.image:
            return f"/static/uploads/categories/{self.image}"
        return f"/static/images/category-{self.slug}.jpg"
    
    def update_posts_count(self):
        """Обновление счетчика постов"""
        self.posts_count = self.get_posts_count()
        db.session.commit()
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'image_url': self.get_image_url(),
            'posts_count': self.posts_count,
            'views_count': self.views_count,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    """Идеальная модель поста с расширенным функционалом"""
    __tablename__ = 'posts'
    
    # Основные поля
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    excerpt = db.Column(db.Text)
    
    # Изображения
    featured_image = db.Column(db.String(255))
    featured_image_alt = db.Column(db.String(255))
    gallery_images = db.Column(JSON, default=list)  # Список изображений
    
    # Статус и видимость
    is_published = db.Column(db.Boolean, default=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_pinned = db.Column(db.Boolean, default=False, index=True)
    visibility = db.Column(db.String(20), default='public', index=True)  # public, private, draft
    
    # Статистика
    views_count = db.Column(db.Integer, default=0, index=True)
    likes_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    
    # SEO
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    meta_keywords = db.Column(db.Text)
    canonical_url = db.Column(db.String(500))
    
    # Настройки
    allow_comments = db.Column(db.Boolean, default=True)
    allow_sharing = db.Column(db.Boolean, default=True)
    reading_time = db.Column(db.Integer)  # В минутах
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)
    scheduled_at = db.Column(db.DateTime)  # Для отложенной публикации
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    
    # Связи
    comments = db.relationship('Comment', backref='comment_post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='post_tags', backref='posts')
    bookmarks = db.relationship('Bookmark', backref='bookmark_post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='like_post', lazy='dynamic', cascade='all, delete-orphan')
    views = db.relationship('View', backref='view_post', lazy='dynamic', cascade='all, delete-orphan')
    
    # Индексы
    __table_args__ = (
        Index('idx_post_published_featured', 'is_published', 'is_featured'),
        Index('idx_post_published_pinned', 'is_published', 'is_pinned'),
        Index('idx_post_author_published', 'author_id', 'is_published'),
        Index('idx_post_category_published', 'category_id', 'is_published'),
        Index('idx_post_views', 'views_count'),
        Index('idx_post_published_at', 'published_at'),
        Index('idx_post_scheduled', 'scheduled_at'),
    )
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            self.excerpt = self._generate_excerpt()
        if not self.reading_time:
            self.reading_time = self._calculate_reading_time()
    
    @validates('title')
    def validate_title(self, key, title):
        """Валидация заголовка"""
        if len(title.strip()) < 5:
            raise ValueError('Title must be at least 5 characters long')
        return title.strip()
    
    @validates('content')
    def validate_content(self, key, content):
        """Валидация контента"""
        if len(content.strip()) < 50:
            raise ValueError('Content must be at least 50 characters long')
        return content.strip()
    
    @validates('visibility')
    def validate_visibility(self, key, visibility):
        """Валидация видимости"""
        if visibility not in ['public', 'private', 'draft']:
            raise ValueError('Visibility must be public, private, or draft')
        return visibility
    
    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        """Обработка изменения контента для генерации HTML"""
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i',
            'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'img', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'div', 'span', 'mark', 'del', 'ins', 'sub', 'sup'
        ]
        allowed_attrs = {
            '*': ['class', 'id'],
            'a': ['href', 'rel', 'target', 'title'],
            'img': ['src', 'alt', 'width', 'height', 'title', 'loading'],
            'table': ['border', 'cellpadding', 'cellspacing'],
        }
        
        # Генерация HTML из Markdown
        html_content = markdown.markdown(
            value, 
            output_format='html',
            extensions=['codehilite', 'fenced_code', 'tables', 'toc']
        )
        
        # Очистка HTML
        target.content_html = bleach.linkify(
            bleach.clean(
                html_content,
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
        )
        
        # Обновление времени чтения
        target.reading_time = target._calculate_reading_time()
    
    def _generate_excerpt(self, length=200):
        """Генерация краткого описания"""
        # Удаляем HTML теги
        text_content = re.sub(r'<[^>]+>', '', self.content)
        if len(text_content) <= length:
            return text_content
        return text_content[:length].rsplit(' ', 1)[0] + '...'
    
    def _calculate_reading_time(self):
        """Расчет времени чтения"""
        if not self.content:
            return 1
        words_count = len(re.sub(r'<[^>]+>', '', self.content).split())
        return max(1, words_count // 200)  # 200 слов в минуту
    
    def get_reading_time(self):
        """Получение времени чтения"""
        return self._calculate_reading_time()
    
    def get_featured_image_url(self, size='large'):
        """Получение URL изображения поста"""
        if self.featured_image:
            return f"/static/uploads/posts/{size}/{self.featured_image}"
        return f"/static/images/default-post-{size}.jpg"
    
    def get_gallery_images_urls(self, size='medium'):
        """Получение URL изображений галереи"""
        if not self.gallery_images:
            return []
        return [f"/static/uploads/posts/{size}/{img}" for img in self.gallery_images]
    
    def get_comments_count(self):
        """Количество одобренных комментариев"""
        return self.comments.filter_by(is_approved=True).count()
    
    def increment_views(self, user_id=None, ip_address=None, user_agent=None):
        """Увеличение счетчика просмотров"""
        self.views_count += 1
        
        # Записываем просмотр
        view = View(
            post_id=self.id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(view)
        db.session.commit()
    
    def increment_likes(self):
        """Увеличение счетчика лайков"""
        self.likes_count += 1
        db.session.commit()
    
    def increment_shares(self):
        """Увеличение счетчика репостов"""
        self.shares_count += 1
        db.session.commit()
    
    def update_comments_count(self):
        """Обновление счетчика комментариев"""
        self.comments_count = self.get_comments_count()
        db.session.commit()
    
    def is_scheduled(self):
        """Проверка, запланирован ли пост"""
        return self.scheduled_at and self.scheduled_at > datetime.utcnow()
    
    def can_be_published(self):
        """Проверка, можно ли опубликовать пост"""
        return not self.is_published and not self.is_scheduled()
    
    def publish(self):
        """Публикация поста"""
        if self.can_be_published():
            self.is_published = True
            self.published_at = datetime.utcnow()
            self.visibility = 'public'
            db.session.commit()
            return True
        return False
    
    def unpublish(self):
        """Снятие с публикации"""
        self.is_published = False
        self.visibility = 'draft'
        db.session.commit()
    
    def to_dict(self, include_content=False):
        """Преобразование в словарь для API"""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'featured_image_url': self.get_featured_image_url(),
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'is_pinned': self.is_pinned,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'shares_count': self.shares_count,
            'comments_count': self.comments_count,
            'reading_time': self.reading_time,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'author': self.author.to_dict() if self.author else None,
            'category': self.category.to_dict() if self.category else None,
            'tags': [tag.to_dict() for tag in self.tags]
        }
        
        if include_content:
            data['content'] = self.content
            data['content_html'] = self.content_html
        
        return data
    
    def __repr__(self):
        return f'<Post {self.title}>'

# Обработчик события изменения контента
db.event.listen(Post.content, 'set', Post.on_changed_content)

class Comment(db.Model):
    """Идеальная модель комментария с расширенным функционалом"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    
    # Статус
    is_approved = db.Column(db.Boolean, default=False, index=True)
    is_spam = db.Column(db.Boolean, default=False)
    is_highlighted = db.Column(db.Boolean, default=False)
    
    # Статистика
    likes_count = db.Column(db.Integer, default=0)
    replies_count = db.Column(db.Integer, default=0)
    
    # Модерация
    moderation_notes = db.Column(db.Text)
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    moderated_at = db.Column(db.DateTime)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), index=True)
    
    # Связи
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    likes = db.relationship('CommentLike', backref='comment', lazy='dynamic', cascade='all, delete-orphan')
    moderator = db.relationship('User', foreign_keys=[moderated_by], backref='moderated_comments')
    
    # Индексы
    __table_args__ = (
        Index('idx_comment_post_approved', 'post_id', 'is_approved'),
        Index('idx_comment_author_approved', 'author_id', 'is_approved'),
        Index('idx_comment_parent', 'parent_id'),
    )
    
    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        """Обработка изменения контента комментария"""
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong', 'p', 'br', 'blockquote']
        target.content_html = bleach.linkify(
            bleach.clean(markdown.markdown(value, output_format='html'), tags=allowed_tags, strip=True)
        )
    
    @validates('content')
    def validate_content(self, key, content):
        """Валидация контента комментария"""
        if len(content.strip()) < 3:
            raise ValueError('Comment must be at least 3 characters long')
        if len(content.strip()) > 1000:
            raise ValueError('Comment must be no more than 1000 characters long')
        return content.strip()
    
    def approve(self, moderator_id=None):
        """Одобрение комментария"""
        self.is_approved = True
        self.is_spam = False
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()
        db.session.commit()
    
    def reject(self, moderator_id=None, notes=None):
        """Отклонение комментария"""
        self.is_approved = False
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()
        if notes:
            self.moderation_notes = notes
        db.session.commit()
    
    def mark_as_spam(self, moderator_id=None):
        """Помечание как спам"""
        self.is_spam = True
        self.is_approved = False
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()
        db.session.commit()
    
    def increment_likes(self):
        """Увеличение счетчика лайков"""
        self.likes_count += 1
        db.session.commit()
    
    def update_replies_count(self):
        """Обновление счетчика ответов"""
        self.replies_count = self.replies.count()
        db.session.commit()
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'content': self.content,
            'content_html': self.content_html,
            'is_approved': self.is_approved,
            'is_highlighted': self.is_highlighted,
            'likes_count': self.likes_count,
            'replies_count': self.replies_count,
            'created_at': self.created_at.isoformat(),
            'author': self.author.to_dict() if self.author else None,
            'parent_id': self.parent_id,
            'replies': [reply.to_dict() for reply in self.replies.filter_by(is_approved=True).limit(5)]
        }
    
    def __repr__(self):
        return f'<Comment {self.id}>'

# Обработчик события изменения контента комментария
db.event.listen(Comment.content, 'set', Comment.on_changed_content)

class Tag(db.Model):
    """Идеальная модель тега с расширенным функционалом"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6c757d')
    
    # Статистика
    posts_count = db.Column(db.Integer, default=0)
    usage_count = db.Column(db.Integer, default=0)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Индексы
    __table_args__ = (
        Index('idx_tag_posts_count', 'posts_count'),
        Index('idx_tag_usage_count', 'usage_count'),
    )
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    @validates('name')
    def validate_name(self, key, name):
        """Валидация названия тега"""
        if len(name.strip()) < 2:
            raise ValueError('Tag name must be at least 2 characters long')
        return name.strip().lower()
    
    def get_posts_count(self):
        """Количество постов с этим тегом"""
        return self.posts.filter_by(is_published=True).count()
    
    def update_posts_count(self):
        """Обновление счетчика постов"""
        self.posts_count = self.get_posts_count()
        db.session.commit()
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'color': self.color,
            'posts_count': self.posts_count,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Tag {self.name}>'

# Таблица связи многие-ко-многим для постов и тегов
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    Index('idx_post_tags_post', 'post_id'),
    Index('idx_post_tags_tag', 'tag_id')
)

class View(db.Model):
    """Идеальная модель просмотра с расширенной аналитикой"""
    __tablename__ = 'views'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Техническая информация
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    session_id = db.Column(db.String(255), nullable=True, index=True)
    
    # Геолокация
    country = db.Column(db.String(2), nullable=True, index=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    
    # Устройство
    device_type = db.Column(db.String(20), nullable=True, index=True)  # desktop, mobile, tablet
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    
    # Время
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    duration = db.Column(db.Integer, default=0)  # В секундах
    
    # Связи
    post = db.relationship('Post', backref=db.backref('post_views', lazy=True, overlaps="views,view_post"))
    user = db.relationship('User', backref=db.backref('user_views', lazy=True))
    
    # Индексы
    __table_args__ = (
        Index('idx_view_post_timestamp', 'post_id', 'timestamp'),
        Index('idx_view_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_view_device_timestamp', 'device_type', 'timestamp'),
        Index('idx_view_country_timestamp', 'country', 'timestamp'),
    )
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'country': self.country,
            'city': self.city,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration
        }
    
    def __repr__(self):
        return f'<View {self.id}>'

class Bookmark(db.Model):
    """Модель закладок"""
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Индексы
    __table_args__ = (
        Index('idx_bookmark_user_post', 'user_id', 'post_id', unique=True),
    )
    
    def __repr__(self):
        return f'<Bookmark {self.id}>'

class PostLike(db.Model):
    """Модель лайков постов"""
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Индексы
    __table_args__ = (
        Index('idx_post_like_user_post', 'user_id', 'post_id', unique=True),
    )
    
    def __repr__(self):
        return f'<PostLike {self.id}>'

class CommentLike(db.Model):
    """Модель лайков комментариев"""
    __tablename__ = 'comment_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Индексы
    __table_args__ = (
        Index('idx_comment_like_user_comment', 'user_id', 'comment_id', unique=True),
    )
    
    def __repr__(self):
        return f'<CommentLike {self.id}>'

class Notification(db.Model):
    """Модель уведомлений"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False, index=True)  # info, warning, success, error
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = db.relationship('User', backref=db.backref('user_notifications', lazy=True, overlaps="notifications,notification_user"))
    
    # Индексы
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
        Index('idx_notification_type', 'type'),
    )
    
    def mark_as_read(self):
        """Помечание уведомления как прочитанного"""
        self.is_read = True
        db.session.commit()
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Notification {self.id}>'

class UserSession(db.Model):
    """Модель пользовательских сессий"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Связи
    user = db.relationship('User', backref=db.backref('user_sessions', lazy=True, overlaps="sessions,session_user"))
    
    # Индексы
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
    )
    
    def is_expired(self):
        """Проверка истечения сессии"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def extend_session(self, hours=24):
        """Продление сессии"""
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        db.session.commit()
    
    def terminate(self):
        """Завершение сессии"""
        self.is_active = False
        db.session.commit()
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'

# События для автоматического обновления счетчиков
@event.listens_for(Post, 'after_insert')
def update_post_counters(mapper, connection, target):
    """Обновление счетчиков после создания поста"""
    if target.author:
        target.author.posts_count += 1
    if target.category:
        target.category.posts_count += 1
    for tag in target.tags:
        tag.posts_count += 1

@event.listens_for(Comment, 'after_insert')
def update_comment_counters(mapper, connection, target):
    """Обновление счетчиков после создания комментария"""
    if target.author:
        target.author.comments_count += 1
    if target.post:
        target.post.comments_count += 1
    if target.parent:
        target.parent.replies_count += 1

@event.listens_for(PostLike, 'after_insert')
def update_like_counters(mapper, connection, target):
    """Обновление счетчиков после лайка"""
    if target.post:
        target.post.likes_count += 1

@event.listens_for(PostLike, 'after_delete')
def update_like_counters_delete(mapper, connection, target):
    """Обновление счетчиков после удаления лайка"""
    if target.post:
        target.post.likes_count -= 1