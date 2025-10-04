"""
Модель поста
"""

from datetime import datetime
from sqlalchemy import JSON
from slugify import slugify
from blog import db

class Post(db.Model):
    """Модель поста с расширенным функционалом"""
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
    gallery_images = db.Column(JSON, default=list)
    
    # Статус и видимость
    is_published = db.Column(db.Boolean, default=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_pinned = db.Column(db.Boolean, default=False, index=True)
    visibility = db.Column(db.String(20), default='public', index=True)
    
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
    reading_time = db.Column(db.Integer)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)
    scheduled_at = db.Column(db.DateTime)
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    
    # Связи
    category = db.relationship('Category', backref='posts', lazy='select')
    tags = db.relationship('Tag', secondary='post_tags', backref='posts', lazy='dynamic')
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    views = db.relationship('View', backref='view_post', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='bookmark_post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='liked_post', lazy='dynamic', cascade='all, delete-orphan')
    
    # Индексы
    __table_args__ = (
        db.Index('idx_post_title', 'title'),
        db.Index('idx_post_slug', 'slug'),
        db.Index('idx_post_published', 'is_published'),
        db.Index('idx_post_featured', 'is_featured'),
        db.Index('idx_post_author', 'author_id'),
        db.Index('idx_post_category', 'category_id'),
        db.Index('idx_post_created', 'created_at'),
        db.Index('idx_post_published_at', 'published_at'),
        db.Index('idx_post_views', 'views_count'),
    )
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if self.title and not self.slug:
            self.slug = self.generate_slug()
    
    def generate_slug(self):
        """Генерация slug из заголовка"""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        
        while Post.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def update_slug(self):
        """Обновление slug"""
        self.slug = self.generate_slug()
    
    def publish(self):
        """Публикация поста"""
        self.is_published = True
        self.published_at = datetime.utcnow()
        db.session.commit()
    
    def unpublish(self):
        """Снятие с публикации"""
        self.is_published = False
        db.session.commit()
    
    def increment_views(self):
        """Увеличение счетчика просмотров"""
        self.views_count += 1
        db.session.commit()
    
    def increment_likes(self):
        """Увеличение счетчика лайков"""
        self.likes_count += 1
        db.session.commit()
    
    def decrement_likes(self):
        """Уменьшение счетчика лайков"""
        if self.likes_count > 0:
            self.likes_count -= 1
            db.session.commit()
    
    def increment_comments(self):
        """Увеличение счетчика комментариев"""
        self.comments_count += 1
        db.session.commit()
    
    def decrement_comments(self):
        """Уменьшение счетчика комментариев"""
        if self.comments_count > 0:
            self.comments_count -= 1
            db.session.commit()
    
    def calculate_reading_time(self):
        """Расчет времени чтения"""
        words_per_minute = 200
        word_count = len(self.content.split())
        self.reading_time = max(1, word_count // words_per_minute)
        db.session.commit()
    
    def get_excerpt(self, length=200):
        """Получение краткого описания"""
        if self.excerpt:
            return self.excerpt
        return self.content[:length] + '...' if len(self.content) > length else self.content
    
    def is_author(self, user):
        """Проверка авторства"""
        return user and user.id == self.author_id
    
    def can_edit(self, user):
        """Проверка права редактирования"""
        return user and (user.is_admin or self.is_author(user))
    
    def can_delete(self, user):
        """Проверка права удаления"""
        return user and (user.is_admin or self.is_author(user))
    
    def __repr__(self):
        return f'<Post {self.title}>'