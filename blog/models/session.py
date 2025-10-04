"""
Модель сессии пользователя
"""

from datetime import datetime
from blog.database import db

class UserSession(db.Model):
    """Модель сессии пользователя"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, index=True)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Связи
    user = db.relationship('User', backref='sessions', lazy='select')
    
    def update_activity(self):
        """Обновление активности"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Деактивация сессии"""
        self.is_active = False
        db.session.commit()
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'