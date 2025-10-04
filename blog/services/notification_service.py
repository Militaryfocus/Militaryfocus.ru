"""
Сервис для работы с уведомлениями
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from blog.models import Notification, User
from blog.database import db
from blog.services.base import BaseService
import logging

logger = logging.getLogger(__name__)

class NotificationService(BaseService):
    """Сервис управления уведомлениями"""
    model = Notification
    
    def create_notification(self, user_id: int, type: str, title: str, 
                          message: str, link: str = None) -> Optional[Notification]:
        """
        Создать уведомление для пользователя
        
        Args:
            user_id: ID пользователя
            type: Тип уведомления
            title: Заголовок
            message: Сообщение
            link: Ссылка (опционально)
            
        Returns:
            Созданное уведомление или None
        """
        try:
            notification = self.create(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                link=link,
                is_read=False
            )
            
            # Отправляем email если включено
            user = User.query.get(user_id)
            if user and user.email_notifications:
                self._send_email_notification(user, notification)
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False,
                             page: int = 1, per_page: int = 20):
        """
        Получить уведомления пользователя
        
        Args:
            user_id: ID пользователя
            unread_only: Только непрочитанные
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список уведомлений
        """
        filters = {'user_id': user_id}
        if unread_only:
            filters['is_read'] = False
        
        return self.get_paginated(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by='created_at',
            desc_order=True
        )
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Отметить уведомление как прочитанное
        
        Args:
            notification_id: ID уведомления
            user_id: ID пользователя (для проверки)
            
        Returns:
            True если успешно
        """
        try:
            notification = self.get_by_id(notification_id)
            
            if notification and notification.user_id == user_id:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.session.commit()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Отметить все уведомления как прочитанные
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество обновленных уведомлений
        """
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            db.session.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            db.session.rollback()
            return 0
    
    def get_unread_count(self, user_id: int) -> int:
        """
        Получить количество непрочитанных уведомлений
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество непрочитанных
        """
        return self.count(filters={'user_id': user_id, 'is_read': False})
    
    def delete_old_notifications(self, days: int = 30) -> int:
        """
        Удалить старые прочитанные уведомления
        
        Args:
            days: Старше скольких дней удалять
            
        Returns:
            Количество удаленных
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Удаляем только прочитанные
            old_notifications = Notification.query.filter(
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            ).all()
            
            count = len(old_notifications)
            
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            logger.info(f"Deleted {count} old notifications")
            
            return count
            
        except Exception as e:
            logger.error(f"Error deleting old notifications: {e}")
            db.session.rollback()
            return 0
    
    def notify_followers(self, user_id: int, type: str, title: str, 
                        message: str, link: str = None):
        """
        Уведомить подписчиков пользователя
        
        Args:
            user_id: ID пользователя
            type: Тип уведомления
            title: Заголовок
            message: Сообщение
            link: Ссылка
        """
        # TODO: Реализовать когда будет система подписок
        pass
    
    def notify_admins(self, type: str, title: str, message: str, link: str = None):
        """
        Уведомить всех администраторов
        
        Args:
            type: Тип уведомления
            title: Заголовок
            message: Сообщение
            link: Ссылка
        """
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            
            for admin in admins:
                self.create_notification(
                    user_id=admin.id,
                    type=type,
                    title=title,
                    message=message,
                    link=link
                )
                
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")
    
    def create_bulk_notifications(self, user_ids: List[int], type: str, 
                                 title: str, message: str, link: str = None) -> int:
        """
        Создать массовые уведомления
        
        Args:
            user_ids: Список ID пользователей
            type: Тип уведомления
            title: Заголовок
            message: Сообщение
            link: Ссылка
            
        Returns:
            Количество созданных уведомлений
        """
        try:
            notifications = []
            
            for user_id in user_ids:
                notification = Notification(
                    user_id=user_id,
                    type=type,
                    title=title,
                    message=message,
                    link=link,
                    is_read=False
                )
                notifications.append(notification)
            
            db.session.add_all(notifications)
            db.session.commit()
            
            return len(notifications)
            
        except Exception as e:
            logger.error(f"Error creating bulk notifications: {e}")
            db.session.rollback()
            return 0
    
    def _send_email_notification(self, user: User, notification: Notification):
        """
        Отправить email уведомление
        
        Args:
            user: Пользователь
            notification: Уведомление
        """
        # TODO: Реализовать отправку email
        # Здесь должна быть интеграция с email сервисом
        pass
    
    # Типы уведомлений
    TYPES = {
        'new_comment': 'Новый комментарий',
        'comment_reply': 'Ответ на комментарий',
        'post_published': 'Пост опубликован',
        'post_liked': 'Ваш пост понравился',
        'new_follower': 'Новый подписчик',
        'mention': 'Вас упомянули',
        'system': 'Системное уведомление',
        'admin': 'Административное уведомление'
    }

# Создаем глобальный экземпляр сервиса
notification_service = NotificationService()