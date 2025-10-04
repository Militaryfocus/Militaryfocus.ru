"""
Сервис для работы с пользователями
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from models import User, Post, Comment
from config.database import db
from services.core.base import BaseService
import secrets
import logging

logger = logging.getLogger(__name__)

class UserService(BaseService):
    """Сервис управления пользователями"""
    model = User
    
    def create_user(self, username: str, email: str, password: str,
                   is_admin: bool = False, **kwargs) -> Optional[User]:
        """
        Создать нового пользователя
        
        Args:
            username: Имя пользователя
            email: Email
            password: Пароль
            is_admin: Является ли администратором
            **kwargs: Дополнительные параметры
            
        Returns:
            Созданный пользователь или None
        """
        try:
            # Проверяем уникальность
            if self.exists(username=username):
                logger.warning(f"User with username {username} already exists")
                return None
            
            if self.exists(email=email):
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Создаем пользователя
            user = User(
                username=username,
                email=email,
                is_admin=is_admin,
                **kwargs
            )
            user.set_password(password)
            
            # Генерируем токен для подтверждения email
            user.email_verification_token = secrets.token_urlsafe(32)
            
            db.session.add(user)
            db.session.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.session.rollback()
            return None
    
    def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Аутентификация пользователя
        
        Args:
            username_or_email: Имя пользователя или email
            password: Пароль
            
        Returns:
            Пользователь если аутентификация успешна
        """
        try:
            # Ищем по username или email
            user = User.query.filter(
                db.or_(
                    User.username == username_or_email,
                    User.email == username_or_email
                )
            ).first()
            
            if user and user.check_password(password) and user.is_active:
                # Обновляем статистику входа
                user.increment_login_count()
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Изменить пароль пользователя
        
        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль
            
        Returns:
            True если успешно
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False
            
            # Проверяем старый пароль
            if not user.check_password(old_password):
                logger.warning(f"Invalid old password for user {user_id}")
                return False
            
            # Устанавливаем новый пароль
            user.set_password(new_password)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            db.session.rollback()
            return False
    
    def request_password_reset(self, email: str) -> Optional[str]:
        """
        Запрос сброса пароля
        
        Args:
            email: Email пользователя
            
        Returns:
            Токен для сброса пароля или None
        """
        try:
            user = self.find_by(email=email)
            if not user:
                return None
            
            # Генерируем токен
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
            
            db.session.commit()
            
            return token
            
        except Exception as e:
            logger.error(f"Error requesting password reset: {e}")
            db.session.rollback()
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Сбросить пароль по токену
        
        Args:
            token: Токен сброса
            new_password: Новый пароль
            
        Returns:
            True если успешно
        """
        try:
            user = User.query.filter_by(password_reset_token=token).first()
            
            if not user:
                return False
            
            # Проверяем срок действия токена
            if user.password_reset_expires < datetime.utcnow():
                logger.warning(f"Password reset token expired for user {user.id}")
                return False
            
            # Устанавливаем новый пароль
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            db.session.rollback()
            return False
    
    def verify_email(self, token: str) -> bool:
        """
        Подтвердить email по токену
        
        Args:
            token: Токен подтверждения
            
        Returns:
            True если успешно
        """
        try:
            user = User.query.filter_by(email_verification_token=token).first()
            
            if not user:
                return False
            
            user.is_verified = True
            user.email_verification_token = None
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            db.session.rollback()
            return False
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Получить статистику пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь со статистикой
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return {}
            
            # Подсчет постов
            posts_count = Post.query.filter_by(author_id=user_id).count()
            published_posts = Post.query.filter_by(
                author_id=user_id,
                is_published=True
            ).count()
            
            # Подсчет комментариев
            comments_count = Comment.query.filter_by(author_id=user_id).count()
            
            # Общее количество просмотров постов
            total_views = db.session.query(
                db.func.sum(Post.views_count)
            ).filter(Post.author_id == user_id).scalar() or 0
            
            # Общее количество лайков
            total_likes = db.session.query(
                db.func.sum(Post.likes_count)
            ).filter(Post.author_id == user_id).scalar() or 0
            
            return {
                'posts_count': posts_count,
                'published_posts': published_posts,
                'draft_posts': posts_count - published_posts,
                'comments_count': comments_count,
                'total_views': total_views,
                'total_likes': total_likes,
                'reputation_score': user.reputation_score,
                'member_since': user.created_at,
                'last_active': user.last_seen
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    def search_users(self, query: str, page: int = 1, per_page: int = 20):
        """
        Поиск пользователей
        
        Args:
            query: Поисковый запрос
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список пользователей
        """
        try:
            return User.query.filter(
                db.or_(
                    User.username.contains(query),
                    User.email.contains(query),
                    User.first_name.contains(query),
                    User.last_name.contains(query)
                )
            ).paginate(page=page, per_page=per_page, error_out=False)
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return User.query.paginate(page=1, per_page=1, error_out=False)
    
    def get_active_users(self, days: int = 30, limit: int = 10) -> List[User]:
        """
        Получить активных пользователей
        
        Args:
            days: Количество дней для определения активности
            limit: Максимальное количество пользователей
            
        Returns:
            Список активных пользователей
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            return User.query.filter(
                User.last_seen >= since,
                User.is_active == True
            ).order_by(User.last_seen.desc())\
             .limit(limit)\
             .all()
             
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def update_user_profile(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Обновить профиль пользователя
        
        Args:
            user_id: ID пользователя
            **kwargs: Поля для обновления
            
        Returns:
            Обновленный пользователь
        """
        # Поля, которые можно обновлять
        allowed_fields = [
            'first_name', 'last_name', 'bio', 'website',
            'location', 'birth_date', 'avatar',
            'email_notifications', 'privacy_settings'
        ]
        
        # Фильтруем только разрешенные поля
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        return self.update(user_id, **update_data)
    
    def toggle_admin_status(self, user_id: int) -> bool:
        """
        Переключить статус администратора
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если успешно
        """
        user = self.get_by_id(user_id)
        if user:
            user.is_admin = not user.is_admin
            db.session.commit()
            return True
        return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Деактивировать пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если успешно
        """
        return self.update(user_id, is_active=False) is not None
    
    def activate_user(self, user_id: int) -> bool:
        """
        Активировать пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если успешно
        """
        return self.update(user_id, is_active=True) is not None

# Создаем глобальный экземпляр сервиса
user_service = UserService()