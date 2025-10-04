"""
Модель уведомления
"""

from datetime import datetime
from blog import db

class Notification(db.Model):
    """Модель уведомления"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False, index=True)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Связи
    user = db.relationship('User', backref='notifications', lazy='select')
    
    def mark_as_read(self):
        """Пометка как прочитанное"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Notification {self.id}>'