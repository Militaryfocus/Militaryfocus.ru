"""
Сервис для работы с сессиями пользователей
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, text
from models import Session, User
from config.database import db
from services.core.base import BaseService
import secrets
import logging

logger = logging.getLogger(__name__)

class SessionService(BaseService):
    """Сервис управления сессиями"""
    model = Session
    
    def create_session(self, user_id: int, ip_address: str = None, 
                      user_agent: str = None, remember: bool = False) -> Optional[Session]:
        """
        Создать новую сессию для пользователя
        
        Args:
            user_id: ID пользователя
            ip_address: IP адрес
            user_agent: User Agent браузера
            remember: Долгосрочная сессия
            
        Returns:
            Созданная сессия или None
        """
        try:
            # Генерируем уникальный токен
            token = self._generate_session_token()
            
            # Устанавливаем время жизни
            if remember:
                expires_at = datetime.utcnow() + timedelta(days=30)
            else:
                expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Создаем сессию
            session = self.create(
                user_id=user_id,
                token=token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                last_activity=datetime.utcnow()
            )
            
            # Ограничиваем количество активных сессий
            self._limit_user_sessions(user_id)
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def validate_session(self, token: str) -> Optional[Session]:
        """
        Проверить валидность сессии
        
        Args:
            token: Токен сессии
            
        Returns:
            Сессия если валидна, иначе None
        """
        try:
            session = self.find_by(token=token)
            
            if not session:
                return None
            
            # Проверяем срок действия
            if session.expires_at < datetime.utcnow():
                self.delete(session.id)
                return None
            
            # Обновляем последнюю активность
            session.last_activity = datetime.utcnow()
            db.session.commit()
            
            return session
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def extend_session(self, session_id: int, hours: int = 24) -> bool:
        """
        Продлить сессию
        
        Args:
            session_id: ID сессии
            hours: На сколько часов продлить
            
        Returns:
            True если успешно
        """
        try:
            session = self.get_by_id(session_id)
            
            if session:
                session.expires_at = datetime.utcnow() + timedelta(hours=hours)
                session.last_activity = datetime.utcnow()
                db.session.commit()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False
    
    def end_session(self, token: str) -> bool:
        """
        Завершить сессию (logout)
        
        Args:
            token: Токен сессии
            
        Returns:
            True если успешно
        """
        try:
            session = self.find_by(token=token)
            
            if session:
                return self.delete(session.id)
                
            return False
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    def end_all_user_sessions(self, user_id: int, except_token: str = None) -> int:
        """
        Завершить все сессии пользователя
        
        Args:
            user_id: ID пользователя
            except_token: Токен, который не нужно удалять
            
        Returns:
            Количество завершенных сессий
        """
        try:
            query = Session.query.filter_by(user_id=user_id)
            
            if except_token:
                query = query.filter(Session.token != except_token)
            
            sessions = query.all()
            count = len(sessions)
            
            for session in sessions:
                db.session.delete(session)
            
            db.session.commit()
            
            return count
            
        except Exception as e:
            logger.error(f"Error ending all user sessions: {e}")
            db.session.rollback()
            return 0
    
    def get_active_sessions(self, user_id: int) -> List[Session]:
        """
        Получить активные сессии пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список активных сессий
        """
        try:
            return Session.query.filter(
                Session.user_id == user_id,
                Session.expires_at > datetime.utcnow()
            ).order_by(
                Session.last_activity.desc()
            ).all()
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def clean_expired_sessions(self) -> int:
        """
        Удалить истекшие сессии
        
        Returns:
            Количество удаленных сессий
        """
        try:
            expired = Session.query.filter(
                Session.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired)
            
            for session in expired:
                db.session.delete(session)
            
            db.session.commit()
            logger.info(f"Cleaned {count} expired sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning expired sessions: {e}")
            db.session.rollback()
            return 0
    
    def get_session_statistics(self, user_id: int = None) -> Dict:
        """
        Получить статистику сессий
        
        Args:
            user_id: ID пользователя (опционально)
            
        Returns:
            Словарь со статистикой
        """
        try:
            query = Session.query
            
            if user_id:
                query = query.filter(Session.user_id == user_id)
            
            # Активные сессии
            active_sessions = query.filter(
                Session.expires_at > datetime.utcnow()
            ).count()
            
            # Уникальные пользователи
            if user_id:
                unique_users = 1 if active_sessions > 0 else 0
            else:
                unique_users = db.session.query(
                    func.count(func.distinct(Session.user_id))
                ).filter(
                    Session.expires_at > datetime.utcnow()
                ).scalar() or 0
            
            # Средняя продолжительность сессии
            avg_duration = db.session.query(
                func.avg(
                    func.timestampdiff(
                        text('MINUTE'),
                        Session.created_at,
                        Session.last_activity
                    )
                )
            ).filter(
                Session.expires_at < datetime.utcnow()
            )
            
            if user_id:
                avg_duration = avg_duration.filter(Session.user_id == user_id)
            
            avg_duration = avg_duration.scalar() or 0
            
            # Устройства
            devices = db.session.query(
                Session.user_agent,
                func.count(Session.id).label('count')
            ).filter(
                Session.expires_at > datetime.utcnow()
            )
            
            if user_id:
                devices = devices.filter(Session.user_id == user_id)
            
            devices = devices.group_by(
                Session.user_agent
            ).all()
            
            return {
                'active_sessions': active_sessions,
                'unique_users': unique_users,
                'average_duration_minutes': avg_duration,
                'devices': [
                    {
                        'user_agent': self._parse_user_agent(ua),
                        'count': count
                    }
                    for ua, count in devices
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {
                'active_sessions': 0,
                'unique_users': 0,
                'average_duration_minutes': 0,
                'devices': []
            }
    
    def detect_suspicious_activity(self, user_id: int) -> List[Dict]:
        """
        Обнаружить подозрительную активность
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список подозрительных событий
        """
        try:
            suspicious = []
            
            # Проверяем множественные входы с разных IP
            recent_sessions = Session.query.filter(
                Session.user_id == user_id,
                Session.created_at > datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            unique_ips = set(s.ip_address for s in recent_sessions if s.ip_address)
            
            if len(unique_ips) > 3:
                suspicious.append({
                    'type': 'multiple_ips',
                    'description': f'Входы с {len(unique_ips)} разных IP за последний час',
                    'severity': 'medium'
                })
            
            # Проверяем быстрые переключения между устройствами
            devices = set(s.user_agent for s in recent_sessions if s.user_agent)
            
            if len(devices) > 2:
                suspicious.append({
                    'type': 'multiple_devices',
                    'description': f'Использование {len(devices)} разных устройств',
                    'severity': 'low'
                })
            
            return suspicious
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}")
            return []
    
    def _generate_session_token(self) -> str:
        """
        Сгенерировать уникальный токен сессии
        
        Returns:
            Токен сессии
        """
        while True:
            token = secrets.token_urlsafe(32)
            
            # Проверяем уникальность
            if not self.exists(token=token):
                return token
    
    def _limit_user_sessions(self, user_id: int, max_sessions: int = 5):
        """
        Ограничить количество активных сессий пользователя
        
        Args:
            user_id: ID пользователя
            max_sessions: Максимальное количество сессий
        """
        try:
            # Получаем все активные сессии
            sessions = self.get_active_sessions(user_id)
            
            # Если превышен лимит, удаляем старые
            if len(sessions) > max_sessions:
                # Сортируем по последней активности и удаляем старые
                sessions_to_remove = sessions[max_sessions:]
                
                for session in sessions_to_remove:
                    db.session.delete(session)
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error limiting user sessions: {e}")
    
    def _parse_user_agent(self, user_agent: str) -> str:
        """
        Простой парсер User Agent
        
        Args:
            user_agent: Строка User Agent
            
        Returns:
            Читаемое описание устройства
        """
        if not user_agent:
            return "Unknown"
        
        # Простое определение типа устройства
        if "Mobile" in user_agent:
            return "Mobile"
        elif "Tablet" in user_agent:
            return "Tablet"
        elif "Windows" in user_agent:
            return "Windows"
        elif "Mac" in user_agent:
            return "Mac"
        elif "Linux" in user_agent:
            return "Linux"
        else:
            return "Other"

# Создаем глобальный экземпляр сервиса
session_service = SessionService()