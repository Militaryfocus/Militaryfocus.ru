"""
Модель категории
"""

from datetime import datetime
from slugify import slugify
from sqlalchemy.orm import validates
from sqlalchemy import Index
from blog import db

class Category(db.Model):
    """Модель категории с расширенным функционалом"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')
    icon = db.Column(db.String(50))
    image = db.Column(db.String(255))
    
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
    
    def generate_slug(self):
        """Генерация slug из названия"""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Category.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def update_slug(self):
        """Обновление slug"""
        self.slug = self.generate_slug()
    
    def increment_posts_count(self):
        """Увеличение счетчика постов"""
        self.posts_count += 1
        db.session.commit()
    
    def decrement_posts_count(self):
        """Уменьшение счетчика постов"""
        if self.posts_count > 0:
            self.posts_count -= 1
            db.session.commit()
    
    def increment_views(self):
        """Увеличение счетчика просмотров"""
        self.views_count += 1
        db.session.commit()
    
    def get_published_posts(self):
        """Получение опубликованных постов"""
        return self.posts.filter_by(is_published=True).order_by(db.desc('created_at'))
    
    def get_posts_count(self):
        """Получение количества опубликованных постов"""
        return self.posts.filter_by(is_published=True).count()
    
    def __repr__(self):
        return f'<Category {self.name}>'