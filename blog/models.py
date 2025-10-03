"""
Модели базы данных для блога
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify
import markdown
import bleach
from blog import db

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Установка пароля с хешированием"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Получение полного имени"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_avatar_url(self):
        """Получение URL аватара"""
        if self.avatar:
            return f"/static/uploads/{self.avatar}"
        return "/static/images/default-avatar.png"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """Модель категории"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # HEX цвет
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    posts = db.relationship('Post', backref='category', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    def get_posts_count(self):
        """Количество постов в категории"""
        # Используем кэшированный счетчик для производительности
        from flask import current_app
        cache_key = f'category_posts_count_{self.id}'
        
        try:
            count = current_app.cache.get(cache_key) if hasattr(current_app, 'cache') else None
            if count is None:
                count = self.posts.filter_by(is_published=True).count()
                if hasattr(current_app, 'cache'):
                    current_app.cache.set(cache_key, count, timeout=300)
            return count
        except:
            return self.posts.filter_by(is_published=True).count()
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    """Модель поста"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)  # HTML версия контента
    excerpt = db.Column(db.Text)  # Краткое описание
    featured_image = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    # Связи
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='post_tags', backref='posts')
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            # Создаем краткое описание из первых 200 символов
            self.excerpt = self.content[:200] + '...' if len(self.content) > 200 else self.content
    
    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        """Обработка изменения контента для генерации HTML"""
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i',
            'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'img', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ]
        allowed_attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt', 'width', 'height'],
        }
        target.content_html = bleach.linkify(
            bleach.clean(
                markdown.markdown(value, output_format='html'),
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
        )
    
    def get_featured_image_url(self):
        """Получение URL изображения поста"""
        if self.featured_image:
            return f"/static/uploads/{self.featured_image}"
        return "/static/images/default-post.jpg"
    
    def get_comments_count(self):
        """Количество комментариев"""
        # Используем кэшированный счетчик для производительности
        from flask import current_app
        cache_key = f'post_comments_count_{self.id}'
        
        try:
            count = current_app.cache.get(cache_key) if hasattr(current_app, 'cache') else None
            if count is None:
                count = self.comments.filter_by(is_approved=True).count()
                if hasattr(current_app, 'cache'):
                    current_app.cache.set(cache_key, count, timeout=300)
            return count
        except:
            return self.comments.filter_by(is_approved=True).count()
    
    def get_reading_time(self):
        """Примерное время чтения (слов в минуту)"""
        words_count = len(self.content.split())
        return max(1, words_count // 200)  # 200 слов в минуту
    
    def increment_views(self):
        """Увеличение счетчика просмотров"""
        self.views_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<Post {self.title}>'

# Обработчик события изменения контента
db.event.listen(Post.content, 'set', Post.on_changed_content)

class Comment(db.Model):
    """Модель комментария"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # Для ответов на комментарии
    
    # Связи
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        """Обработка изменения контента комментария"""
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong', 'p', 'br']
        target.content_html = bleach.linkify(
            bleach.clean(markdown.markdown(value, output_format='html'), tags=allowed_tags, strip=True)
        )
    
    def __repr__(self):
        return f'<Comment {self.id}>'

# Обработчик события изменения контента комментария
db.event.listen(Comment.content, 'set', Comment.on_changed_content)

class Tag(db.Model):
    """Модель тега"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

# Таблица связи многие-ко-многим для постов и тегов
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)