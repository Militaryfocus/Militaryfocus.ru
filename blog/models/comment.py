"""
Модель комментария
"""

from datetime import datetime
from blog import db

class Comment(db.Model):
    """Модель комментария"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, index=True)
    is_spam = db.Column(db.Boolean, default=False)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), index=True)
    
    # Связи
    post = db.relationship('Post', backref='comments', lazy='select')
    author = db.relationship('User', backref='comments', lazy='select')
    parent = db.relationship('Comment', remote_side=[id], backref='replies')
    likes = db.relationship('CommentLike', backref='liked_comment', lazy='dynamic', cascade='all, delete-orphan')
    
    def approve(self):
        """Одобрение комментария"""
        self.is_approved = True
        db.session.commit()
    
    def disapprove(self):
        """Отклонение комментария"""
        self.is_approved = False
        db.session.commit()
    
    def mark_as_spam(self):
        """Пометка как спам"""
        self.is_spam = True
        self.is_approved = False
        db.session.commit()
    
    def __repr__(self):
        return f'<Comment {self.id}>'