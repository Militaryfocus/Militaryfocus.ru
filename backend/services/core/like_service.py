"""
Сервис для работы с лайками
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func
from models import Like, Post, Comment, User
from config.database import db
from services.core.base import BaseService
import logging

logger = logging.getLogger(__name__)

class LikeService(BaseService):
    """Сервис управления лайками"""
    model = Like
    
    def add_like(self, user_id: int, item_type: str, item_id: int) -> Optional[Like]:
        """
        Добавить лайк
        
        Args:
            user_id: ID пользователя
            item_type: Тип объекта ('post' или 'comment')
            item_id: ID объекта
            
        Returns:
            Созданный лайк или None
        """
        try:
            # Проверяем валидность типа
            if item_type not in ['post', 'comment']:
                logger.error(f"Invalid item type: {item_type}")
                return None
            
            # Проверяем существование объекта
            if item_type == 'post':
                item = Post.query.get(item_id)
                if not item or not item.is_published:
                    return None
            else:
                item = Comment.query.get(item_id)
                if not item or not item.is_approved:
                    return None
            
            # Проверяем, не поставлен ли уже лайк
            existing = self.find_by(
                user_id=user_id,
                item_type=item_type,
                item_id=item_id
            )
            
            if existing:
                logger.info(f"Like already exists for user {user_id}")
                return existing
            
            # Создаем лайк
            like = self.create(
                user_id=user_id,
                item_type=item_type,
                item_id=item_id
            )
            
            # Увеличиваем счетчик
            self._increment_like_count(item_type, item_id)
            
            # Создаем уведомление автору
            self._notify_author(like, item)
            
            return like
            
        except Exception as e:
            logger.error(f"Error adding like: {e}")
            return None
    
    def remove_like(self, user_id: int, item_type: str, item_id: int) -> bool:
        """
        Удалить лайк
        
        Args:
            user_id: ID пользователя
            item_type: Тип объекта
            item_id: ID объекта
            
        Returns:
            True если удалено успешно
        """
        try:
            like = self.find_by(
                user_id=user_id,
                item_type=item_type,
                item_id=item_id
            )
            
            if like:
                db.session.delete(like)
                db.session.commit()
                
                # Уменьшаем счетчик
                self._decrement_like_count(item_type, item_id)
                
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error removing like: {e}")
            db.session.rollback()
            return False
    
    def toggle_like(self, user_id: int, item_type: str, item_id: int) -> Dict[str, bool]:
        """
        Переключить состояние лайка
        
        Args:
            user_id: ID пользователя
            item_type: Тип объекта
            item_id: ID объекта
            
        Returns:
            Словарь с результатом {'liked': bool, 'success': bool}
        """
        try:
            like = self.find_by(
                user_id=user_id,
                item_type=item_type,
                item_id=item_id
            )
            
            if like:
                # Удаляем
                success = self.remove_like(user_id, item_type, item_id)
                return {'liked': False, 'success': success}
            else:
                # Добавляем
                new_like = self.add_like(user_id, item_type, item_id)
                return {'liked': bool(new_like), 'success': bool(new_like)}
                
        except Exception as e:
            logger.error(f"Error toggling like: {e}")
            return {'liked': False, 'success': False}
    
    def is_liked(self, user_id: int, item_type: str, item_id: int) -> bool:
        """
        Проверить, поставлен ли лайк
        
        Args:
            user_id: ID пользователя
            item_type: Тип объекта
            item_id: ID объекта
            
        Returns:
            True если лайк есть
        """
        return self.exists(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id
        )
    
    def get_like_count(self, item_type: str, item_id: int) -> int:
        """
        Получить количество лайков
        
        Args:
            item_type: Тип объекта
            item_id: ID объекта
            
        Returns:
            Количество лайков
        """
        return self.count(filters={
            'item_type': item_type,
            'item_id': item_id
        })
    
    def get_user_likes(self, user_id: int, item_type: str = None, 
                      page: int = 1, per_page: int = 20):
        """
        Получить лайки пользователя
        
        Args:
            user_id: ID пользователя
            item_type: Тип объектов (опционально)
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список лайков
        """
        filters = {'user_id': user_id}
        if item_type:
            filters['item_type'] = item_type
        
        return self.get_paginated(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by='created_at',
            desc_order=True
        )
    
    def get_liked_posts(self, user_id: int, page: int = 1, per_page: int = 20):
        """
        Получить понравившиеся посты пользователя
        
        Args:
            user_id: ID пользователя
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список постов
        """
        try:
            posts = Post.query.join(
                Like,
                (Like.item_id == Post.id) & 
                (Like.item_type == 'post') &
                (Like.user_id == user_id)
            ).filter(
                Post.is_published == True
            ).order_by(
                Like.created_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting liked posts: {e}")
            return Post.query.paginate(page=1, per_page=1, error_out=False)
    
    def get_popular_posts_by_likes(self, days: int = 7, limit: int = 10) -> List[Post]:
        """
        Получить популярные посты по лайкам
        
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
                func.count(Like.id).label('like_count')
            ).join(
                Like,
                (Like.item_id == Post.id) & (Like.item_type == 'post')
            ).filter(
                Post.is_published == True,
                Like.created_at >= since_date
            ).group_by(
                Post.id
            ).order_by(
                func.count(Like.id).desc()
            ).limit(limit).all()
            
            return [post for post, count in popular_posts]
            
        except Exception as e:
            logger.error(f"Error getting popular posts by likes: {e}")
            return []
    
    def get_like_statistics(self, item_type: str = None, days: int = 30) -> Dict:
        """
        Получить статистику лайков
        
        Args:
            item_type: Тип объектов
            days: Период в днях
            
        Returns:
            Словарь со статистикой
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            query = Like.query.filter(Like.created_at >= since_date)
            if item_type:
                query = query.filter(Like.item_type == item_type)
            
            # Общее количество
            total_likes = query.count()
            
            # Лайки по дням
            daily_likes = db.session.query(
                func.date(Like.created_at).label('date'),
                func.count(Like.id).label('count')
            ).filter(
                Like.created_at >= since_date
            )
            
            if item_type:
                daily_likes = daily_likes.filter(Like.item_type == item_type)
            
            daily_likes = daily_likes.group_by(
                func.date(Like.created_at)
            ).all()
            
            # Топ пользователей по лайкам
            top_users = db.session.query(
                User,
                func.count(Like.id).label('like_count')
            ).join(
                Like, Like.user_id == User.id
            ).filter(
                Like.created_at >= since_date
            )
            
            if item_type:
                top_users = top_users.filter(Like.item_type == item_type)
            
            top_users = top_users.group_by(
                User.id
            ).order_by(
                func.count(Like.id).desc()
            ).limit(10).all()
            
            return {
                'total_likes': total_likes,
                'average_daily': total_likes / days if days > 0 else 0,
                'likes_by_day': {
                    str(date): count for date, count in daily_likes
                },
                'top_users': [
                    {
                        'username': user.username,
                        'count': count
                    }
                    for user, count in top_users
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting like statistics: {e}")
            return {
                'total_likes': 0,
                'average_daily': 0,
                'likes_by_day': {},
                'top_users': []
            }
    
    def _increment_like_count(self, item_type: str, item_id: int):
        """
        Увеличить счетчик лайков
        
        Args:
            item_type: Тип объекта
            item_id: ID объекта
        """
        try:
            if item_type == 'post':
                post = Post.query.get(item_id)
                if post:
                    post.like_count = (post.like_count or 0) + 1
                    db.session.commit()
            elif item_type == 'comment':
                comment = Comment.query.get(item_id)
                if comment:
                    comment.like_count = (comment.like_count or 0) + 1
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"Error incrementing like count: {e}")
            db.session.rollback()
    
    def _decrement_like_count(self, item_type: str, item_id: int):
        """
        Уменьшить счетчик лайков
        
        Args:
            item_type: Тип объекта
            item_id: ID объекта
        """
        try:
            if item_type == 'post':
                post = Post.query.get(item_id)
                if post and post.like_count > 0:
                    post.like_count -= 1
                    db.session.commit()
            elif item_type == 'comment':
                comment = Comment.query.get(item_id)
                if comment and comment.like_count > 0:
                    comment.like_count -= 1
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"Error decrementing like count: {e}")
            db.session.rollback()
    
    def _notify_author(self, like: Like, item):
        """
        Отправить уведомление автору
        
        Args:
            like: Лайк
            item: Объект (пост или комментарий)
        """
        try:
            # Получаем автора
            if like.item_type == 'post':
                author_id = item.user_id
                title = "Ваш пост понравился"
                message = f"Пользователь поставил лайк вашему посту '{item.title}'"
                link = f"/blog/post/{item.slug}"
            else:
                author_id = item.user_id
                title = "Ваш комментарий понравился"
                message = "Пользователь поставил лайк вашему комментарию"
                link = f"/blog/post/{item.post.slug}#comment-{item.id}"
            
            # Не отправляем уведомление самому себе
            if author_id == like.user_id:
                return
            
            # Создаем уведомление через сервис уведомлений
            from services.core.notification_service import notification_service
            notification_service.create_notification(
                user_id=author_id,
                type='post_liked' if like.item_type == 'post' else 'comment_liked',
                title=title,
                message=message,
                link=link
            )
            
        except Exception as e:
            logger.error(f"Error notifying author: {e}")

# Создаем глобальный экземпляр сервиса
like_service = LikeService()