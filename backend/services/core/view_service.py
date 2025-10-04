"""
Сервис для работы с просмотрами
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func
from models import View, Post, User
from config.database import db
from services.core.base import BaseService
import logging

logger = logging.getLogger(__name__)

class ViewService(BaseService):
    """Сервис управления просмотрами"""
    model = View
    
    def record_view(self, post_id: int, user_id: Optional[int] = None, 
                   ip_address: str = None, user_agent: str = None) -> Optional[View]:
        """
        Записать просмотр поста
        
        Args:
            post_id: ID поста
            user_id: ID пользователя (если авторизован)
            ip_address: IP адрес
            user_agent: User Agent браузера
            
        Returns:
            Созданный просмотр или None
        """
        try:
            # Проверяем, не был ли этот пост просмотрен недавно
            if self._is_recently_viewed(post_id, user_id, ip_address):
                return None
            
            # Создаем запись о просмотре
            view = self.create(
                post_id=post_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Увеличиваем счетчик в посте
            post = Post.query.get(post_id)
            if post:
                post.increment_views()
            
            return view
            
        except Exception as e:
            logger.error(f"Error recording view: {e}")
            return None
    
    def _is_recently_viewed(self, post_id: int, user_id: Optional[int], 
                           ip_address: str, minutes: int = 30) -> bool:
        """
        Проверить, был ли пост просмотрен недавно
        
        Args:
            post_id: ID поста
            user_id: ID пользователя
            ip_address: IP адрес
            minutes: Период в минутах
            
        Returns:
            True если был просмотрен недавно
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            query = View.query.filter(
                View.post_id == post_id,
                View.created_at > cutoff_time
            )
            
            # Проверяем по пользователю или IP
            if user_id:
                query = query.filter(View.user_id == user_id)
            else:
                query = query.filter(View.ip_address == ip_address)
            
            return query.first() is not None
            
        except Exception as e:
            logger.error(f"Error checking recent views: {e}")
            return False
    
    def get_post_views(self, post_id: int, unique_only: bool = False) -> int:
        """
        Получить количество просмотров поста
        
        Args:
            post_id: ID поста
            unique_only: Только уникальные просмотры
            
        Returns:
            Количество просмотров
        """
        try:
            if unique_only:
                # Считаем уникальные по IP + user_id
                unique_views = db.session.query(
                    func.count(func.distinct(
                        func.coalesce(View.user_id, View.ip_address)
                    ))
                ).filter(View.post_id == post_id).scalar()
                
                return unique_views or 0
            else:
                return self.count(filters={'post_id': post_id})
                
        except Exception as e:
            logger.error(f"Error getting post views: {e}")
            return 0
    
    def get_popular_posts_by_views(self, days: int = 7, limit: int = 10) -> List[Post]:
        """
        Получить популярные посты по просмотрам за период
        
        Args:
            days: Период в днях
            limit: Количество постов
            
        Returns:
            Список популярных постов
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            popular_posts = db.session.query(
                Post,
                func.count(View.id).label('view_count')
            ).join(
                View, View.post_id == Post.id
            ).filter(
                Post.is_published == True,
                View.created_at >= since_date
            ).group_by(
                Post.id
            ).order_by(
                func.count(View.id).desc()
            ).limit(limit).all()
            
            return [post for post, count in popular_posts]
            
        except Exception as e:
            logger.error(f"Error getting popular posts by views: {e}")
            return []
    
    def get_user_history(self, user_id: int, page: int = 1, per_page: int = 20):
        """
        Получить историю просмотров пользователя
        
        Args:
            user_id: ID пользователя
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированная история просмотров
        """
        return self.get_paginated(
            page=page,
            per_page=per_page,
            filters={'user_id': user_id},
            order_by='created_at',
            desc_order=True
        )
    
    def get_view_statistics(self, post_id: int = None, days: int = 30) -> Dict:
        """
        Получить статистику просмотров
        
        Args:
            post_id: ID поста (если None - общая статистика)
            days: Период в днях
            
        Returns:
            Словарь со статистикой
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            query = View.query.filter(View.created_at >= since_date)
            if post_id:
                query = query.filter(View.post_id == post_id)
            
            # Общее количество просмотров
            total_views = query.count()
            
            # Уникальные просмотры
            unique_views = query.distinct(
                func.coalesce(View.user_id, View.ip_address)
            ).count()
            
            # Просмотры по дням
            daily_views = db.session.query(
                func.date(View.created_at).label('date'),
                func.count(View.id).label('count')
            ).filter(
                View.created_at >= since_date
            )
            
            if post_id:
                daily_views = daily_views.filter(View.post_id == post_id)
            
            daily_views = daily_views.group_by(
                func.date(View.created_at)
            ).all()
            
            # Преобразуем в словарь
            views_by_day = {
                str(date): count for date, count in daily_views
            }
            
            return {
                'total_views': total_views,
                'unique_views': unique_views,
                'average_daily': total_views / days if days > 0 else 0,
                'views_by_day': views_by_day
            }
            
        except Exception as e:
            logger.error(f"Error getting view statistics: {e}")
            return {
                'total_views': 0,
                'unique_views': 0,
                'average_daily': 0,
                'views_by_day': {}
            }
    
    def get_referrer_statistics(self, post_id: int = None, limit: int = 10) -> List[Dict]:
        """
        Получить статистику по источникам трафика
        
        Args:
            post_id: ID поста
            limit: Количество источников
            
        Returns:
            Список источников с количеством переходов
        """
        try:
            query = db.session.query(
                View.referrer,
                func.count(View.id).label('count')
            ).filter(
                View.referrer.isnot(None)
            )
            
            if post_id:
                query = query.filter(View.post_id == post_id)
            
            referrers = query.group_by(
                View.referrer
            ).order_by(
                func.count(View.id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'referrer': referrer,
                    'count': count
                }
                for referrer, count in referrers
            ]
            
        except Exception as e:
            logger.error(f"Error getting referrer statistics: {e}")
            return []
    
    def clean_old_views(self, days: int = 90) -> int:
        """
        Удалить старые записи о просмотрах
        
        Args:
            days: Старше скольких дней удалять
            
        Returns:
            Количество удаленных записей
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Удаляем старые просмотры
            old_views = View.query.filter(
                View.created_at < cutoff_date
            ).all()
            
            count = len(old_views)
            
            # Пакетное удаление
            for i in range(0, count, 1000):
                batch = old_views[i:i+1000]
                for view in batch:
                    db.session.delete(view)
                db.session.commit()
            
            logger.info(f"Cleaned {count} old views")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning old views: {e}")
            db.session.rollback()
            return 0
    
    def get_reading_time_stats(self, post_id: int) -> Dict:
        """
        Получить статистику времени чтения
        
        Args:
            post_id: ID поста
            
        Returns:
            Статистика времени чтения
        """
        # TODO: Реализовать когда будет tracking времени на странице
        return {
            'average_time': 0,
            'completion_rate': 0
        }

# Создаем глобальный экземпляр сервиса
view_service = ViewService()