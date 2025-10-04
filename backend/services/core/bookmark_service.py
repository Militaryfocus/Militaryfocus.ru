"""
Сервис для работы с закладками
"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import func
from models import Bookmark, Post, User
from config.database import db
from services.core.base import BaseService
import logging

logger = logging.getLogger(__name__)

class BookmarkService(BaseService):
    """Сервис управления закладками"""
    model = Bookmark
    
    def add_bookmark(self, user_id: int, post_id: int) -> Optional[Bookmark]:
        """
        Добавить пост в закладки
        
        Args:
            user_id: ID пользователя
            post_id: ID поста
            
        Returns:
            Созданная закладка или None
        """
        try:
            # Проверяем, существует ли уже закладка
            existing = self.find_by(user_id=user_id, post_id=post_id)
            if existing:
                logger.info(f"Bookmark already exists for user {user_id} and post {post_id}")
                return existing
            
            # Проверяем существование поста
            post = Post.query.get(post_id)
            if not post or not post.is_published:
                logger.warning(f"Post {post_id} not found or not published")
                return None
            
            # Создаем закладку
            bookmark = self.create(
                user_id=user_id,
                post_id=post_id
            )
            
            return bookmark
            
        except Exception as e:
            logger.error(f"Error adding bookmark: {e}")
            return None
    
    def remove_bookmark(self, user_id: int, post_id: int) -> bool:
        """
        Удалить пост из закладок
        
        Args:
            user_id: ID пользователя
            post_id: ID поста
            
        Returns:
            True если удалено успешно
        """
        try:
            bookmark = self.find_by(user_id=user_id, post_id=post_id)
            
            if bookmark:
                db.session.delete(bookmark)
                db.session.commit()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error removing bookmark: {e}")
            db.session.rollback()
            return False
    
    def toggle_bookmark(self, user_id: int, post_id: int) -> Dict[str, bool]:
        """
        Переключить состояние закладки
        
        Args:
            user_id: ID пользователя
            post_id: ID поста
            
        Returns:
            Словарь с результатом {'bookmarked': bool, 'success': bool}
        """
        try:
            bookmark = self.find_by(user_id=user_id, post_id=post_id)
            
            if bookmark:
                # Удаляем
                self.remove_bookmark(user_id, post_id)
                return {'bookmarked': False, 'success': True}
            else:
                # Добавляем
                new_bookmark = self.add_bookmark(user_id, post_id)
                return {'bookmarked': bool(new_bookmark), 'success': bool(new_bookmark)}
                
        except Exception as e:
            logger.error(f"Error toggling bookmark: {e}")
            return {'bookmarked': False, 'success': False}
    
    def get_user_bookmarks(self, user_id: int, page: int = 1, per_page: int = 20):
        """
        Получить закладки пользователя
        
        Args:
            user_id: ID пользователя
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список закладок
        """
        return self.get_paginated(
            page=page,
            per_page=per_page,
            filters={'user_id': user_id},
            order_by='created_at',
            desc_order=True
        )
    
    def is_bookmarked(self, user_id: int, post_id: int) -> bool:
        """
        Проверить, добавлен ли пост в закладки
        
        Args:
            user_id: ID пользователя
            post_id: ID поста
            
        Returns:
            True если в закладках
        """
        return self.exists(user_id=user_id, post_id=post_id)
    
    def get_bookmarked_posts(self, user_id: int, page: int = 1, per_page: int = 20):
        """
        Получить посты из закладок пользователя
        
        Args:
            user_id: ID пользователя
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список постов
        """
        try:
            # Получаем посты через join
            posts = Post.query.join(
                Bookmark, 
                (Bookmark.post_id == Post.id) & (Bookmark.user_id == user_id)
            ).filter(
                Post.is_published == True
            ).order_by(
                Bookmark.created_at.desc()
            ).paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting bookmarked posts: {e}")
            return Post.query.paginate(page=1, per_page=1, error_out=False)
    
    def get_bookmark_count(self, post_id: int) -> int:
        """
        Получить количество закладок для поста
        
        Args:
            post_id: ID поста
            
        Returns:
            Количество закладок
        """
        return self.count(filters={'post_id': post_id})
    
    def get_popular_bookmarked_posts(self, limit: int = 10) -> List[Post]:
        """
        Получить самые популярные посты по закладкам
        
        Args:
            limit: Количество постов
            
        Returns:
            Список популярных постов
        """
        try:
            # Группируем по post_id и считаем количество
            popular_posts = db.session.query(
                Post,
                func.count(Bookmark.id).label('bookmark_count')
            ).join(
                Bookmark, Bookmark.post_id == Post.id
            ).filter(
                Post.is_published == True
            ).group_by(
                Post.id
            ).order_by(
                func.count(Bookmark.id).desc()
            ).limit(limit).all()
            
            return [post for post, count in popular_posts]
            
        except Exception as e:
            logger.error(f"Error getting popular bookmarked posts: {e}")
            return []
    
    def export_user_bookmarks(self, user_id: int) -> List[Dict]:
        """
        Экспортировать закладки пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список закладок для экспорта
        """
        try:
            bookmarks = Bookmark.query.filter_by(user_id=user_id).all()
            
            export_data = []
            for bookmark in bookmarks:
                if bookmark.post and bookmark.post.is_published:
                    export_data.append({
                        'title': bookmark.post.title,
                        'url': f"/blog/post/{bookmark.post.slug}",
                        'added_at': bookmark.created_at.isoformat(),
                        'excerpt': bookmark.post.excerpt or '',
                        'tags': [tag.name for tag in bookmark.post.tags]
                    })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting bookmarks: {e}")
            return []
    
    def clean_orphaned_bookmarks(self) -> int:
        """
        Удалить закладки для удаленных постов
        
        Returns:
            Количество удаленных закладок
        """
        try:
            # Находим закладки без постов
            orphaned = Bookmark.query.filter(
                ~Bookmark.post.has()
            ).all()
            
            count = len(orphaned)
            
            for bookmark in orphaned:
                db.session.delete(bookmark)
            
            db.session.commit()
            logger.info(f"Cleaned {count} orphaned bookmarks")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning orphaned bookmarks: {e}")
            db.session.rollback()
            return 0

# Создаем глобальный экземпляр сервиса
bookmark_service = BookmarkService()