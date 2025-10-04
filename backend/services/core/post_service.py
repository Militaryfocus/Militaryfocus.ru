"""
Сервис для работы с постами
"""

from typing import Optional, List
from datetime import datetime
from models import Post, User, Category, Tag
from config.database import db

class PostService:
    """Сервис для работы с постами"""
    
    @staticmethod
    def create_post(title: str, content: str, author_id: int, 
                   category_id: Optional[int] = None, 
                   tags: Optional[List[str]] = None,
                   is_published: bool = False) -> Post:
        """Создание нового поста"""
        post = Post(
            title=title,
            content=content,
            author_id=author_id,
            category_id=category_id,
            is_published=is_published,
            created_at=datetime.utcnow()
        )
        
        # Добавление тегов
        if tags:
            tag_objects = []
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                tag_objects.append(tag)
            post.tags = tag_objects
        
        db.session.add(post)
        db.session.commit()
        
        # Обновление счетчиков
        if category_id:
            category = Category.query.get(category_id)
            if category:
                category.increment_posts_count()
        
        author = User.query.get(author_id)
        if author:
            author.posts_count += 1
            db.session.commit()
        
        return post
    
    @staticmethod
    def get_post_by_slug(slug: str) -> Optional[Post]:
        """Получение поста по slug"""
        return Post.query.filter_by(slug=slug, is_published=True).first()
    
    @staticmethod
    def get_posts_by_author(author_id: int, page: int = 1, 
                           per_page: int = 10) -> List[Post]:
        """Получение постов автора с пагинацией"""
        return Post.query.filter_by(
            author_id=author_id, 
            is_published=True
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_published_posts(page: int = 1, per_page: int = 10) -> List[Post]:
        """Получение опубликованных постов с пагинацией"""
        return Post.query.filter_by(is_published=True)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_featured_posts(limit: int = 5) -> List[Post]:
        """Получение рекомендуемых постов"""
        return Post.query.filter_by(is_published=True, is_featured=True)\
            .order_by(Post.created_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_popular_posts(limit: int = 5) -> List[Post]:
        """Получение популярных постов"""
        return Post.query.filter_by(is_published=True)\
            .order_by(Post.views_count.desc())\
            .limit(limit).all()
    
    @staticmethod
    def update_post(post: Post, **kwargs) -> Post:
        """Обновление поста"""
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        return post
    
    @staticmethod
    def delete_post(post: Post) -> bool:
        """Удаление поста"""
        try:
            # Обновление счетчиков
            if post.category:
                post.category.decrement_posts_count()
            
            if post.author:
                post.author.posts_count -= 1
            
            db.session.delete(post)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def publish_post(post: Post) -> Post:
        """Публикация поста"""
        post.publish()
        return post
    
    @staticmethod
    def unpublish_post(post: Post) -> Post:
        """Снятие с публикации"""
        post.unpublish()
        return post
    
    @staticmethod
    def increment_views(post: Post) -> Post:
        """Увеличение счетчика просмотров"""
        post.increment_views()
        return post
    
    @staticmethod
    def search_posts(query: str, page: int = 1, per_page: int = 10) -> List[Post]:
        """Поиск постов"""
        return Post.query.filter(
            Post.is_published == True,
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query)
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )