"""
Сервис для работы с тегами
"""
from typing import List, Optional, Dict
from sqlalchemy import func
from blog.models import Tag, Post
from blog.database import db
from blog.services.base import BaseService
import logging

logger = logging.getLogger(__name__)

class TagService(BaseService):
    """Сервис управления тегами"""
    model = Tag
    
    def get_popular_tags(self, limit: int = 20) -> List[Dict]:
        """
        Получить популярные теги с количеством использований
        
        Args:
            limit: Количество тегов
            
        Returns:
            Список тегов с количеством постов
        """
        try:
            # Подсчитываем количество постов для каждого тега
            tags = db.session.query(
                Tag,
                func.count(Post.id).label('post_count')
            ).join(
                Tag.posts
            ).filter(
                Post.is_published == True
            ).group_by(
                Tag.id
            ).order_by(
                func.count(Post.id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'tag': tag,
                    'post_count': count
                }
                for tag, count in tags
            ]
        except Exception as e:
            logger.error(f"Error getting popular tags: {e}")
            return []
    
    def get_or_create(self, name: str) -> Optional[Tag]:
        """
        Получить тег или создать новый
        
        Args:
            name: Название тега
            
        Returns:
            Тег или None
        """
        try:
            # Нормализуем имя тега
            name = name.strip().lower()
            
            # Ищем существующий
            tag = self.find_by(name=name)
            if tag:
                return tag
            
            # Создаем новый
            return self.create(name=name)
            
        except Exception as e:
            logger.error(f"Error get_or_create tag: {e}")
            return None
    
    def get_related_tags(self, tag_id: int, limit: int = 10) -> List[Tag]:
        """
        Получить связанные теги (часто используются вместе)
        
        Args:
            tag_id: ID тега
            limit: Количество тегов
            
        Returns:
            Список связанных тегов
        """
        try:
            # Находим посты с данным тегом
            posts_with_tag = Post.query.join(Post.tags).filter(
                Tag.id == tag_id,
                Post.is_published == True
            ).all()
            
            if not posts_with_tag:
                return []
            
            # Собираем все теги из этих постов
            related_tags_count = {}
            for post in posts_with_tag:
                for tag in post.tags:
                    if tag.id != tag_id:  # Исключаем исходный тег
                        related_tags_count[tag] = related_tags_count.get(tag, 0) + 1
            
            # Сортируем по частоте использования
            sorted_tags = sorted(
                related_tags_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit]
            
            return [tag for tag, count in sorted_tags]
            
        except Exception as e:
            logger.error(f"Error getting related tags: {e}")
            return []
    
    def merge_tags(self, source_id: int, target_id: int) -> bool:
        """
        Объединить два тега
        
        Args:
            source_id: ID исходного тега
            target_id: ID целевого тега
            
        Returns:
            True если успешно
        """
        try:
            source = self.get_by_id(source_id)
            target = self.get_by_id(target_id)
            
            if not source or not target or source_id == target_id:
                return False
            
            # Переносим все посты на целевой тег
            for post in source.posts:
                if target not in post.tags:
                    post.tags.append(target)
            
            # Удаляем исходный тег
            self.delete(source_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error merging tags: {e}")
            db.session.rollback()
            return False
    
    def clean_unused_tags(self) -> int:
        """
        Удалить неиспользуемые теги
        
        Returns:
            Количество удаленных тегов
        """
        try:
            # Находим теги без постов
            unused_tags = Tag.query.filter(
                ~Tag.posts.any()
            ).all()
            
            count = len(unused_tags)
            
            # Удаляем
            for tag in unused_tags:
                db.session.delete(tag)
            
            db.session.commit()
            logger.info(f"Cleaned {count} unused tags")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning unused tags: {e}")
            db.session.rollback()
            return 0
    
    def suggest_tags(self, content: str, limit: int = 5) -> List[Tag]:
        """
        Предложить теги на основе контента
        
        Args:
            content: Текст для анализа
            limit: Количество предложений
            
        Returns:
            Список предложенных тегов
        """
        try:
            # Простой алгоритм: ищем существующие теги в тексте
            content_lower = content.lower()
            all_tags = Tag.query.all()
            
            # Подсчитываем вхождения
            tag_scores = []
            for tag in all_tags:
                if tag.name in content_lower:
                    # Считаем количество вхождений
                    count = content_lower.count(tag.name)
                    # Учитываем длину тега (более длинные теги важнее)
                    score = count * len(tag.name)
                    tag_scores.append((tag, score))
            
            # Сортируем по релевантности
            tag_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Возвращаем топ N
            return [tag for tag, score in tag_scores[:limit]]
            
        except Exception as e:
            logger.error(f"Error suggesting tags: {e}")
            return []
    
    def get_tag_cloud(self) -> List[Dict]:
        """
        Получить данные для облака тегов
        
        Returns:
            Список тегов с весами для отображения
        """
        try:
            # Получаем все теги с количеством постов
            tags_data = self.get_popular_tags(limit=50)
            
            if not tags_data:
                return []
            
            # Находим минимум и максимум
            counts = [data['post_count'] for data in tags_data]
            min_count = min(counts)
            max_count = max(counts)
            
            # Нормализуем размеры (от 1 до 5)
            tag_cloud = []
            for data in tags_data:
                count = data['post_count']
                # Нормализация
                if max_count == min_count:
                    size = 3
                else:
                    size = 1 + int(4 * (count - min_count) / (max_count - min_count))
                
                tag_cloud.append({
                    'tag': data['tag'],
                    'size': size,
                    'count': count
                })
            
            # Сортируем по алфавиту для красивого отображения
            tag_cloud.sort(key=lambda x: x['tag'].name)
            
            return tag_cloud
            
        except Exception as e:
            logger.error(f"Error generating tag cloud: {e}")
            return []

# Создаем глобальный экземпляр сервиса
tag_service = TagService()