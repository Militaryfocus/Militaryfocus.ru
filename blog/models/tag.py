"""
Модель тега
"""

from datetime import datetime
from slugify import slugify
from blog import db

class Tag(db.Model):
    """Модель тега"""
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
    
    # Связи
    posts = db.relationship('Post', secondary='post_tags', backref='tags', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    def generate_slug(self):
        """Генерация slug из названия"""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Tag.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def increment_usage(self):
        """Увеличение счетчика использования"""
        self.usage_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<Tag {self.name}>'