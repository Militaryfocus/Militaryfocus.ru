"""
Сервис для работы с комментариями
"""
from typing import List, Optional
from datetime import datetime
from models import Comment, Post, User
from config.database import db
from services.core.base import BaseService
import logging

logger = logging.getLogger(__name__)

class CommentService(BaseService):
    """Сервис управления комментариями"""
    model = Comment
    
    def get_post_comments(self, post_id: int, include_replies: bool = True) -> List[Comment]:
        """
        Получить комментарии к посту
        
        Args:
            post_id: ID поста
            include_replies: Включать ответы на комментарии
            
        Returns:
            Список комментариев
        """
        try:
            if include_replies:
                # Получаем все комментарии с иерархией
                comments = Comment.query.filter_by(
                    post_id=post_id,
                    is_approved=True
                ).order_by(Comment.created_at).all()
            else:
                # Только комментарии верхнего уровня
                comments = Comment.query.filter_by(
                    post_id=post_id,
                    parent_id=None,
                    is_approved=True
                ).order_by(Comment.created_at).all()
            
            return comments
        except Exception as e:
            logger.error(f"Error getting post comments: {e}")
            return []
    
    def get_user_comments(self, user_id: int, page: int = 1, per_page: int = 20):
        """
        Получить комментарии пользователя
        
        Args:
            user_id: ID пользователя
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список комментариев
        """
        return self.get_paginated(
            page=page,
            per_page=per_page,
            filters={'author_id': user_id},
            order_by='created_at',
            desc_order=True
        )
    
    def create_comment(self, post_id: int, author_id: int, content: str,
                      parent_id: Optional[int] = None,
                      auto_approve: bool = False) -> Optional[Comment]:
        """
        Создать новый комментарий
        
        Args:
            post_id: ID поста
            author_id: ID автора
            content: Содержание комментария
            parent_id: ID родительского комментария (для ответов)
            auto_approve: Автоматически одобрить комментарий
            
        Returns:
            Созданный комментарий или None
        """
        try:
            # Проверяем существование поста
            post = Post.query.get(post_id)
            if not post or not post.allow_comments:
                logger.warning(f"Cannot create comment for post {post_id}")
                return None
            
            # Проверяем родительский комментарий
            if parent_id:
                parent = Comment.query.get(parent_id)
                if not parent or parent.post_id != post_id:
                    logger.warning(f"Invalid parent comment {parent_id}")
                    return None
            
            # Создаем комментарий
            comment = self.create(
                post_id=post_id,
                author_id=author_id,
                content=content,
                parent_id=parent_id,
                is_approved=auto_approve,
                commit=False
            )
            
            if comment:
                # Увеличиваем счетчик комментариев
                post.increment_comments()
                db.session.commit()
                
                # Отправляем уведомления
                self._send_comment_notifications(comment)
            
            return comment
            
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            db.session.rollback()
            return None
    
    def approve_comment(self, comment_id: int) -> bool:
        """
        Одобрить комментарий
        
        Args:
            comment_id: ID комментария
            
        Returns:
            True если успешно
        """
        return self.update(comment_id, is_approved=True) is not None
    
    def reject_comment(self, comment_id: int) -> bool:
        """
        Отклонить комментарий
        
        Args:
            comment_id: ID комментария
            
        Returns:
            True если успешно
        """
        comment = self.get_by_id(comment_id)
        if comment and not comment.is_approved:
            # Уменьшаем счетчик если комментарий был учтен
            post = Post.query.get(comment.post_id)
            if post:
                post.decrement_comments()
            
            return self.delete(comment_id)
        return False
    
    def get_pending_comments(self, page: int = 1, per_page: int = 20):
        """
        Получить комментарии на модерации
        
        Args:
            page: Номер страницы
            per_page: Количество на странице
            
        Returns:
            Пагинированный список комментариев
        """
        return self.get_paginated(
            page=page,
            per_page=per_page,
            filters={'is_approved': False},
            order_by='created_at',
            desc_order=True
        )
    
    def get_recent_comments(self, limit: int = 10) -> List[Comment]:
        """
        Получить последние комментарии
        
        Args:
            limit: Количество комментариев
            
        Returns:
            Список комментариев
        """
        try:
            return Comment.query.filter_by(is_approved=True)\
                .order_by(Comment.created_at.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting recent comments: {e}")
            return []
    
    def delete_comment(self, comment_id: int, cascade: bool = True) -> bool:
        """
        Удалить комментарий
        
        Args:
            comment_id: ID комментария
            cascade: Удалить также все ответы
            
        Returns:
            True если успешно
        """
        try:
            comment = self.get_by_id(comment_id)
            if not comment:
                return False
            
            # Получаем пост для обновления счетчика
            post = Post.query.get(comment.post_id)
            
            if cascade:
                # Удаляем все дочерние комментарии
                self._delete_replies(comment_id)
            
            # Удаляем сам комментарий
            success = self.delete(comment_id)
            
            if success and post:
                # Обновляем счетчик
                post.decrement_comments()
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting comment: {e}")
            return False
    
    def _delete_replies(self, parent_id: int):
        """
        Рекурсивно удалить все ответы на комментарий
        
        Args:
            parent_id: ID родительского комментария
        """
        replies = Comment.query.filter_by(parent_id=parent_id).all()
        for reply in replies:
            self._delete_replies(reply.id)
            db.session.delete(reply)
    
    def _send_comment_notifications(self, comment: Comment):
        """
        Отправить уведомления о новом комментарии
        
        Args:
            comment: Комментарий
        """
        try:
            from models import Notification
            
            # Уведомление автору поста
            post = Post.query.get(comment.post_id)
            if post and post.author_id != comment.author_id:
                notification = Notification(
                    user_id=post.author_id,
                    type='new_comment',
                    title='Новый комментарий',
                    message=f'Новый комментарий к вашему посту "{post.title}"',
                    link=f'/blog/post/{post.slug}#comment-{comment.id}'
                )
                db.session.add(notification)
            
            # Уведомление автору родительского комментария
            if comment.parent_id:
                parent = Comment.query.get(comment.parent_id)
                if parent and parent.author_id != comment.author_id:
                    notification = Notification(
                        user_id=parent.author_id,
                        type='comment_reply',
                        title='Ответ на комментарий',
                        message='На ваш комментарий ответили',
                        link=f'/blog/post/{post.slug}#comment-{comment.id}'
                    )
                    db.session.add(notification)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error sending comment notifications: {e}")
    
    def get_comment_tree(self, post_id: int) -> List[dict]:
        """
        Получить дерево комментариев для поста
        
        Args:
            post_id: ID поста
            
        Returns:
            Иерархическая структура комментариев
        """
        try:
            # Получаем все комментарии
            comments = self.get_post_comments(post_id)
            
            # Строим дерево
            comment_dict = {}
            roots = []
            
            # Создаем словарь комментариев
            for comment in comments:
                comment_dict[comment.id] = {
                    'comment': comment,
                    'replies': []
                }
            
            # Строим иерархию
            for comment in comments:
                if comment.parent_id:
                    parent = comment_dict.get(comment.parent_id)
                    if parent:
                        parent['replies'].append(comment_dict[comment.id])
                else:
                    roots.append(comment_dict[comment.id])
            
            return roots
            
        except Exception as e:
            logger.error(f"Error building comment tree: {e}")
            return []

# Создаем глобальный экземпляр сервиса
comment_service = CommentService()