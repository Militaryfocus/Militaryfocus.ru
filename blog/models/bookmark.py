"""
Модель закладки
"""

from datetime import datetime
from blog.database import db

class Bookmark(db.Model):
    """Модель закладки пользователя"""
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    notes = db.Column(db.Text)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    
    # Связи
    user = db.relationship('User', backref='bookmarks', lazy='select')
    post = db.relationship('Post', backref='bookmarks', lazy='select')
    
    # Уникальность
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_bookmark'),
    )
    
    def __repr__(self):
        return f'<Bookmark {self.id}>'