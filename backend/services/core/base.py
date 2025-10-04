"""
Базовый сервис для работы с моделями
Реализует паттерн Repository для унификации доступа к данным
"""
from typing import Optional, List, Dict, Any, Type
from flask_sqlalchemy import Pagination
from sqlalchemy import desc, asc
from config.database import db
import logging

logger = logging.getLogger(__name__)

class BaseService:
    """
    Базовый класс для всех сервисов
    Предоставляет общие методы для работы с моделями
    """
    model: Type[db.Model] = None
    
    def __init__(self):
        if not self.model:
            raise ValueError("Model must be specified in service class")
    
    def get_by_id(self, id: int) -> Optional[db.Model]:
        """
        Получить объект по ID
        
        Args:
            id: ID объекта
            
        Returns:
            Объект модели или None
        """
        try:
            return self.model.query.get(id)
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None
    
    def get_all(self, order_by: str = None, desc_order: bool = True) -> List[db.Model]:
        """
        Получить все объекты
        
        Args:
            order_by: Поле для сортировки
            desc_order: Сортировка по убыванию
            
        Returns:
            Список объектов
        """
        try:
            query = self.model.query
            
            if order_by:
                column = getattr(self.model, order_by, None)
                if column:
                    query = query.order_by(desc(column) if desc_order else asc(column))
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []
    
    def get_paginated(self, page: int = 1, per_page: int = 20, 
                     filters: Dict[str, Any] = None,
                     order_by: str = None, desc_order: bool = True) -> Pagination:
        """
        Получить объекты с пагинацией
        
        Args:
            page: Номер страницы
            per_page: Количество объектов на странице
            filters: Словарь фильтров
            order_by: Поле для сортировки
            desc_order: Сортировка по убыванию
            
        Returns:
            Объект пагинации
        """
        try:
            query = self.model.query
            
            # Применяем фильтры
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        query = query.filter(getattr(self.model, key) == value)
            
            # Применяем сортировку
            if order_by and hasattr(self.model, order_by):
                column = getattr(self.model, order_by)
                query = query.order_by(desc(column) if desc_order else asc(column))
            
            return query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            logger.error(f"Error getting paginated {self.model.__name__}: {e}")
            return self.model.query.paginate(page=1, per_page=1, error_out=False)
    
    def create(self, commit: bool = True, **kwargs) -> Optional[db.Model]:
        """
        Создать новый объект
        
        Args:
            commit: Сохранить изменения в БД
            **kwargs: Параметры для создания объекта
            
        Returns:
            Созданный объект или None
        """
        try:
            obj = self.model(**kwargs)
            db.session.add(obj)
            
            if commit:
                db.session.commit()
            
            return obj
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            db.session.rollback()
            return None
    
    def update(self, id: int, commit: bool = True, **kwargs) -> Optional[db.Model]:
        """
        Обновить объект
        
        Args:
            id: ID объекта
            commit: Сохранить изменения в БД
            **kwargs: Параметры для обновления
            
        Returns:
            Обновленный объект или None
        """
        try:
            obj = self.get_by_id(id)
            if obj:
                for key, value in kwargs.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                
                if commit:
                    db.session.commit()
                
                return obj
            return None
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            db.session.rollback()
            return None
    
    def delete(self, id: int, commit: bool = True) -> bool:
        """
        Удалить объект
        
        Args:
            id: ID объекта
            commit: Сохранить изменения в БД
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            obj = self.get_by_id(id)
            if obj:
                db.session.delete(obj)
                
                if commit:
                    db.session.commit()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            db.session.rollback()
            return False
    
    def bulk_create(self, objects_data: List[Dict[str, Any]], commit: bool = True) -> List[db.Model]:
        """
        Массовое создание объектов
        
        Args:
            objects_data: Список словарей с данными объектов
            commit: Сохранить изменения в БД
            
        Returns:
            Список созданных объектов
        """
        created_objects = []
        
        try:
            for data in objects_data:
                obj = self.model(**data)
                db.session.add(obj)
                created_objects.append(obj)
            
            if commit:
                db.session.commit()
            
            return created_objects
        except Exception as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            db.session.rollback()
            return []
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Подсчет количества объектов
        
        Args:
            filters: Словарь фильтров
            
        Returns:
            Количество объектов
        """
        try:
            query = self.model.query
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        query = query.filter(getattr(self.model, key) == value)
            
            return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    def exists(self, **kwargs) -> bool:
        """
        Проверка существования объекта
        
        Args:
            **kwargs: Параметры для поиска
            
        Returns:
            True если существует, False если нет
        """
        try:
            return self.model.query.filter_by(**kwargs).first() is not None
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__}: {e}")
            return False
    
    def find_by(self, **kwargs) -> Optional[db.Model]:
        """
        Найти объект по параметрам
        
        Args:
            **kwargs: Параметры для поиска
            
        Returns:
            Найденный объект или None
        """
        try:
            return self.model.query.filter_by(**kwargs).first()
        except Exception as e:
            logger.error(f"Error finding {self.model.__name__}: {e}")
            return None
    
    def find_all_by(self, order_by: str = None, desc_order: bool = True, **kwargs) -> List[db.Model]:
        """
        Найти все объекты по параметрам
        
        Args:
            order_by: Поле для сортировки
            desc_order: Сортировка по убыванию
            **kwargs: Параметры для поиска
            
        Returns:
            Список найденных объектов
        """
        try:
            query = self.model.query.filter_by(**kwargs)
            
            if order_by and hasattr(self.model, order_by):
                column = getattr(self.model, order_by)
                query = query.order_by(desc(column) if desc_order else asc(column))
            
            return query.all()
        except Exception as e:
            logger.error(f"Error finding all {self.model.__name__}: {e}")
            return []
    
    def save(self) -> bool:
        """
        Сохранить изменения в БД
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving changes: {e}")
            db.session.rollback()
            return False
    
    def refresh(self, obj: db.Model) -> db.Model:
        """
        Обновить объект из БД
        
        Args:
            obj: Объект для обновления
            
        Returns:
            Обновленный объект
        """
        db.session.refresh(obj)
        return obj