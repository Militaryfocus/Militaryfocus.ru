"""
Модели лайков
"""

from datetime import datetime
from blog.database import db

class PostLike(db.Model):
    """Модель лайка поста"""
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    
    # Связи
    user = db.relationship('User', backref='post_likes', lazy='select')
    post = db.relationship('Post', backref='likes', lazy='select')
    
    # Уникальность
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )
    
    def __repr__(self):
        return f'<PostLike {self.id}>'

class CommentLike(db.Model):
    """Модель лайка комментария"""
    __tablename__ = 'comment_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False, index=True)
    
    # Связи
    user = db.relationship('User', backref='comment_likes', lazy='select')
    comment = db.relationship('Comment', backref='likes', lazy='select')
    
    # Уникальность
    __table_args__ = (
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),
    )
    
    def __repr__(self):
        return f'<CommentLike {self.id}>'