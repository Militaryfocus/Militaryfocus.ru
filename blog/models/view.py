"""
Модель просмотра
"""

from datetime import datetime
from blog import db

class View(db.Model):
    """Модель просмотра поста"""
    __tablename__ = 'views'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.String(500))
    
    # Временные метки
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Внешние ключи
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # Связи
    post = db.relationship('Post', backref='views', lazy='select')
    user = db.relationship('User', backref='views', lazy='select')
    
    def __repr__(self):
        return f'<View {self.id}>'