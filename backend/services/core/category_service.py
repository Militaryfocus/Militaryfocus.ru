"""
Сервис для работы с категориями
"""
from typing import List, Optional, Dict
from sqlalchemy import func
from models import Category, Post
from config.database import db
from services.core.base import BaseService
import logging

logger = logging.getLogger(__name__)

class CategoryService(BaseService):
    """Сервис управления категориями"""
    model = Category
    
    def get_active_categories(self) -> List[Category]:
        """
        Получить активные категории
        
        Returns:
            Список активных категорий
        """
        return self.find_all_by(is_active=True, order_by='name')
    
    def get_categories_with_post_count(self) -> List[Dict]:
        """
        Получить категории с количеством постов
        
        Returns:
            Список категорий с подсчетом постов
        """
        try:
            categories = db.session.query(
                Category,
                func.count(Post.id).label('post_count')
            ).outerjoin(
                Post, 
                (Post.category_id == Category.id) & (Post.is_published == True)
            ).group_by(Category.id).all()
            
            return [
                {
                    'category': cat,
                    'post_count': count
                }
                for cat, count in categories
            ]
        except Exception as e:
            logger.error(f"Error getting categories with post count: {e}")
            return []
    
    def get_category_tree(self) -> List[Dict]:
        """
        Получить дерево категорий (с подкатегориями)
        
        Returns:
            Иерархическая структура категорий
        """
        try:
            # Получаем все категории
            all_categories = Category.query.all()
            
            # Строим дерево
            category_dict = {cat.id: {
                'category': cat,
                'children': []
            } for cat in all_categories}
            
            # Формируем иерархию
            roots = []
            for cat in all_categories:
                if cat.parent_id:
                    parent = category_dict.get(cat.parent_id)
                    if parent:
                        parent['children'].append(category_dict[cat.id])
                else:
                    roots.append(category_dict[cat.id])
            
            return roots
            
        except Exception as e:
            logger.error(f"Error building category tree: {e}")
            return []
    
    def create_category(self, name: str, description: str = None, 
                       color: str = '#007bff', parent_id: int = None) -> Optional[Category]:
        """
        Создать новую категорию
        
        Args:
            name: Название категории
            description: Описание
            color: Цвет категории
            parent_id: ID родительской категории
            
        Returns:
            Созданная категория или None
        """
        try:
            # Проверяем уникальность имени
            if self.exists(name=name):
                logger.warning(f"Category with name '{name}' already exists")
                return None
            
            # Создаем категорию
            category = self.create(
                name=name,
                description=description,
                color=color,
                parent_id=parent_id
            )
            
            return category
            
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return None
    
    def update_post_count(self, category_id: int):
        """
        Обновить счетчик постов в категории
        
        Args:
            category_id: ID категории
        """
        try:
            category = self.get_by_id(category_id)
            if category:
                count = Post.query.filter_by(
                    category_id=category_id,
                    is_published=True
                ).count()
                category.posts_count = count
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating post count: {e}")
    
    def get_popular_categories(self, limit: int = 10) -> List[Category]:
        """
        Получить популярные категории
        
        Args:
            limit: Количество категорий
            
        Returns:
            Список популярных категорий
        """
        return Category.query.filter_by(is_active=True)\
            .order_by(Category.posts_count.desc())\
            .limit(limit)\
            .all()
    
    def merge_categories(self, source_id: int, target_id: int) -> bool:
        """
        Объединить две категории
        
        Args:
            source_id: ID исходной категории
            target_id: ID целевой категории
            
        Returns:
            True если успешно
        """
        try:
            source = self.get_by_id(source_id)
            target = self.get_by_id(target_id)
            
            if not source or not target:
                return False
            
            # Перемещаем все посты
            Post.query.filter_by(category_id=source_id).update(
                {'category_id': target_id}
            )
            
            # Перемещаем подкатегории
            Category.query.filter_by(parent_id=source_id).update(
                {'parent_id': target_id}
            )
            
            # Обновляем счетчик
            self.update_post_count(target_id)
            
            # Удаляем исходную категорию
            self.delete(source_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error merging categories: {e}")
            db.session.rollback()
            return False

# Создаем глобальный экземпляр сервиса
category_service = CategoryService()