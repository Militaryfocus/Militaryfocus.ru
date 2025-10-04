"""
Идеальная система производительности для блога
Включает кэширование, оптимизацию запросов, мониторинг и масштабирование
"""

import os
import time
import json
import logging
import threading
import asyncio
import aiohttp
import redis
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
from functools import wraps, lru_cache
import sqlite3
import hashlib
import pickle
from contextlib import contextmanager
import queue
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.pool import QueuePool
from flask import request, g, current_app
from werkzeug.cache import SimpleCache
try:
    from werkzeug.cache import MemcachedCache, RedisCache
except ImportError:
    # Fallback для новых версий Werkzeug
    MemcachedCache = None
    RedisCache = None
import memcached
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from blog.models import Post, User, Category, Comment, Tag
from blog import db
from blog import db as database

class CacheType(Enum):
    """Типы кэша"""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    FILE = "file"

class PerformanceMetric(Enum):
    """Метрики производительности"""
    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DATABASE_QUERIES = "database_queries"
    CACHE_HITS = "cache_hits"
    CACHE_MISSES = "cache_misses"

@dataclass
class PerformanceProfile:
    """Профиль производительности"""
    endpoint: str
    method: str
    response_time: float
    memory_usage: int
    cpu_usage: float
    database_queries: int
    cache_hits: int
    cache_misses: int
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None

class AdvancedCache:
    """Продвинутая система кэширования"""
    
    def __init__(self, cache_type: CacheType = CacheType.MEMORY):
        self.cache_type = cache_type
        self.cache = self._initialize_cache()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'size': 0
        }
        self.lock = threading.Lock()
        self.ttl_default = 3600  # 1 час
    
    def _initialize_cache(self):
        """Инициализация кэша"""
        if self.cache_type == CacheType.MEMORY:
            return SimpleCache()
        elif self.cache_type == CacheType.REDIS:
            return RedisCache(host='localhost', port=6379, db=0)
        elif self.cache_type == CacheType.MEMCACHED:
            return MemcachedCache(['127.0.0.1:11211'])
        elif self.cache_type == CacheType.FILE:
            return SimpleCache()  # Fallback to memory
    
    def get(self, key: str) -> Optional[Any]:
        """Получение из кэша"""
        with self.lock:
            try:
                value = self.cache.get(key)
                if value is not None:
                    self.stats['hits'] += 1
                    return value
                else:
                    self.stats['misses'] += 1
                    return None
            except Exception as e:
                logging.error(f"Cache get error: {e}")
                self.stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранение в кэш"""
        with self.lock:
            try:
                ttl = ttl or self.ttl_default
                success = self.cache.set(key, value, timeout=ttl)
                if success:
                    self.stats['sets'] += 1
                    self.stats['size'] += 1
                return success
            except Exception as e:
                logging.error(f"Cache set error: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Удаление из кэша"""
        with self.lock:
            try:
                success = self.cache.delete(key)
                if success:
                    self.stats['deletes'] += 1
                    self.stats['size'] -= 1
                return success
            except Exception as e:
                logging.error(f"Cache delete error: {e}")
                return False
    
    def clear(self):
        """Очистка кэша"""
        with self.lock:
            try:
                self.cache.clear()
                self.stats['size'] = 0
            except Exception as e:
                logging.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'cache_type': self.cache_type.value,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': hit_rate,
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'size': self.stats['size']
            }
    
    def generate_key(self, prefix: str, *args) -> str:
        """Генерация ключа кэша"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()

class QueryOptimizer:
    """Оптимизатор запросов к базе данных"""
    
    def __init__(self):
        self.query_cache = {}
        self.slow_queries = deque(maxlen=1000)
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf')
        })
        self.lock = threading.Lock()
    
    def optimize_query(self, query_func: Callable, *args, **kwargs) -> Any:
        """Оптимизация запроса"""
        query_key = self._generate_query_key(query_func.__name__, args, kwargs)
        
        # Проверка кэша запросов
        if query_key in self.query_cache:
            return self.query_cache[query_key]
        
        start_time = time.time()
        
        try:
            result = query_func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Запись статистики
            self._record_query_stats(query_func.__name__, execution_time)
            
            # Кэширование результата
            self.query_cache[query_key] = result
            
            # Запись медленных запросов
            if execution_time > 1.0:  # Запросы дольше 1 секунды
                self.slow_queries.append({
                    'query': query_func.__name__,
                    'execution_time': execution_time,
                    'timestamp': datetime.utcnow(),
                    'args': args,
                    'kwargs': kwargs
                })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_query_stats(query_func.__name__, execution_time)
            raise e
    
    def _generate_query_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Генерация ключа запроса"""
        key_data = f"{func_name}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _record_query_stats(self, query_name: str, execution_time: float):
        """Запись статистики запроса"""
        with self.lock:
            stats = self.query_stats[query_name]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['min_time'] = min(stats['min_time'], execution_time)
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение медленных запросов"""
        return list(self.slow_queries)[-limit:]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Получение статистики запросов"""
        with self.lock:
            return {
                query_name: {
                    'count': stats['count'],
                    'avg_time': stats['avg_time'],
                    'max_time': stats['max_time'],
                    'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                    'total_time': stats['total_time']
                }
                for query_name, stats in self.query_stats.items()
            }
    
    def clear_cache(self):
        """Очистка кэша запросов"""
        with self.lock:
            self.query_cache.clear()

class DatabaseOptimizer:
    """Оптимизатор базы данных"""
    
    def __init__(self):
        self.connection_pool = None
        self.query_optimizer = QueryOptimizer()
        self._optimize_database()
    
    def _optimize_database(self):
        """Оптимизация базы данных"""
        try:
            # Оптимизация пула соединений
            if database.engine.url.drivername == 'sqlite':
                # Оптимизация SQLite
                with database.engine.connect() as conn:
                    conn.execute(text("PRAGMA journal_mode=WAL"))
                    conn.execute(text("PRAGMA synchronous=NORMAL"))
                    conn.execute(text("PRAGMA cache_size=10000"))
                    conn.execute(text("PRAGMA temp_store=MEMORY"))
                    conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
            
            # Создание индексов для оптимизации
            self._create_performance_indexes()
            
        except Exception as e:
            logging.error(f"Database optimization error: {e}")
    
    def _create_performance_indexes(self):
        """Создание индексов для производительности"""
        try:
            with database.engine.connect() as conn:
                # Индексы для постов
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_posts_published_created ON posts (is_published, created_at DESC)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_posts_author_published ON posts (author_id, is_published)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_posts_category_published ON posts (category_id, is_published)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_posts_views ON posts (views_count DESC)"))
                
                # Индексы для комментариев
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_comments_post_approved ON comments (post_id, is_approved)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_comments_author_approved ON comments (author_id, is_approved)"))
                
                # Индексы для пользователей
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_admin ON users (is_admin)"))
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Index creation error: {e}")
    
    def get_optimized_posts(self, limit: int = 10, offset: int = 0, category_id: Optional[int] = None) -> List[Post]:
        """Оптимизированное получение постов"""
        def _query():
            query = database.session.query(Post).options(
                joinedload(Post.author),
                joinedload(Post.category),
                selectinload(Post.tags)
            ).filter(Post.is_published == True)
            
            if category_id:
                query = query.filter(Post.category_id == category_id)
            
            return query.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
        
        return self.query_optimizer.optimize_query(_query)
    
    def get_optimized_post(self, post_id: int) -> Optional[Post]:
        """Оптимизированное получение поста"""
        def _query():
            return database.session.query(Post).options(
                joinedload(Post.author),
                joinedload(Post.category),
                selectinload(Post.tags),
                selectinload(Post.comments).joinedload(Comment.author)
            ).filter(Post.id == post_id).first()
        
        return self.query_optimizer.optimize_query(_query)
    
    def get_optimized_user_posts(self, user_id: int, limit: int = 10) -> List[Post]:
        """Оптимизированное получение постов пользователя"""
        def _query():
            return database.session.query(Post).options(
                joinedload(Post.category),
                selectinload(Post.tags)
            ).filter(
                and_(Post.author_id == user_id, Post.is_published == True)
            ).order_by(Post.created_at.desc()).limit(limit).all()
        
        return self.query_optimizer.optimize_query(_query)
    
    def get_optimized_categories(self) -> List[Category]:
        """Оптимизированное получение категорий"""
        def _query():
            return database.session.query(Category).options(
                selectinload(Category.posts)
            ).filter(Category.is_active == True).order_by(Category.sort_order).all()
        
        return self.query_optimizer.optimize_query(_query)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных"""
        try:
            with database.engine.connect() as conn:
                if database.engine.url.drivername == 'sqlite':
                    # Статистика SQLite
                    db_size = os.path.getsize(database.engine.url.database)
                    
                    # Количество записей в таблицах
                    tables_stats = {}
                    for table in ['posts', 'users', 'categories', 'comments', 'tags']:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                        tables_stats[table] = result[0] if result else 0
                    
                    return {
                        'database_size': f"{db_size / 1024 / 1024:.2f} MB",
                        'tables_stats': tables_stats,
                        'connection_pool_size': database.engine.pool.size(),
                        'connection_pool_checked_in': database.engine.pool.checkedin(),
                        'connection_pool_checked_out': database.engine.pool.checkedout()
                    }
                else:
                    return {
                        'connection_pool_size': database.engine.pool.size(),
                        'connection_pool_checked_in': database.engine.pool.checkedin(),
                        'connection_pool_checked_out': database.engine.pool.checkedout()
                    }
                    
        except Exception as e:
            logging.error(f"Database stats error: {e}")
            return {}

class MemoryOptimizer:
    """Оптимизатор памяти"""
    
    def __init__(self):
        self.memory_threshold = 0.8  # 80% использования памяти
        self.gc_threshold = 1000  # Количество объектов для сборки мусора
        self.object_count = 0
        self.memory_stats = deque(maxlen=100)
        self.lock = threading.Lock()
    
    def monitor_memory(self):
        """Мониторинг использования памяти"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        with self.lock:
            self.memory_stats.append({
                'timestamp': datetime.utcnow(),
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': memory_percent
            })
            
            # Проверка порога памяти
            if memory_percent > self.memory_threshold * 100:
                self._optimize_memory()
    
    def _optimize_memory(self):
        """Оптимизация памяти"""
        try:
            # Принудительная сборка мусора
            collected = gc.collect()
            
            # Очистка кэшей
            from blog.performance_perfect import performance_manager
            performance_manager.cache.clear()
            performance_manager.database_optimizer.query_optimizer.clear_cache()
            
            logging.info(f"Memory optimization: collected {collected} objects")
            
        except Exception as e:
            logging.error(f"Memory optimization error: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        with self.lock:
            recent_stats = list(self.memory_stats)[-10:] if self.memory_stats else []
            avg_memory = np.mean([stat['percent'] for stat in recent_stats]) if recent_stats else 0
            
            return {
                'current_memory_mb': memory_info.rss / 1024 / 1024,
                'current_memory_percent': memory_percent,
                'avg_memory_percent': avg_memory,
                'memory_threshold': self.memory_threshold * 100,
                'gc_stats': {
                    'count': len(gc.garbage),
                    'collected': gc.collect()
                }
            }

class PerformanceProfiler:
    """Профилировщик производительности"""
    
    def __init__(self):
        self.profiles = deque(maxlen=10000)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf'),
            'memory_usage': 0,
            'cpu_usage': 0.0
        })
        self.lock = threading.Lock()
    
    def profile_endpoint(self, endpoint: str, method: str, response_time: float, 
                        memory_usage: int, cpu_usage: float, user_id: Optional[int] = None):
        """Профилирование endpoint"""
        profile = PerformanceProfile(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address=request.remote_addr if request else None
        )
        
        with self.lock:
            self.profiles.append(profile)
            
            # Обновление статистики endpoint
            stats = self.endpoint_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += response_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], response_time)
            stats['min_time'] = min(stats['min_time'], response_time)
            stats['memory_usage'] = max(stats['memory_usage'], memory_usage)
            stats['cpu_usage'] = max(stats['cpu_usage'], cpu_usage)
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Получение статистики endpoint"""
        with self.lock:
            return {
                endpoint: {
                    'count': stats['count'],
                    'avg_time': stats['avg_time'],
                    'max_time': stats['max_time'],
                    'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                    'memory_usage': stats['memory_usage'],
                    'cpu_usage': stats['cpu_usage']
                }
                for endpoint, stats in self.endpoint_stats.items()
            }
    
    def get_slow_endpoints(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Получение медленных endpoint"""
        with self.lock:
            slow_endpoints = []
            for endpoint, stats in self.endpoint_stats.items():
                if stats['avg_time'] > threshold:
                    slow_endpoints.append({
                        'endpoint': endpoint,
                        'avg_time': stats['avg_time'],
                        'max_time': stats['max_time'],
                        'count': stats['count']
                    })
            
            return sorted(slow_endpoints, key=lambda x: x['avg_time'], reverse=True)

class PerformanceMonitor:
    """Мониторинг производительности"""
    
    def __init__(self):
        self.metrics = {
            'response_time': Histogram('response_time_seconds', 'Response time', ['endpoint', 'method']),
            'memory_usage': Gauge('memory_usage_bytes', 'Memory usage', ['endpoint']),
            'cpu_usage': Gauge('cpu_usage_percent', 'CPU usage', ['endpoint']),
            'database_queries': Counter('database_queries_total', 'Database queries', ['query_type']),
            'cache_hits': Counter('cache_hits_total', 'Cache hits', ['cache_type']),
            'cache_misses': Counter('cache_misses_total', 'Cache misses', ['cache_type'])
        }
        
        # Запуск Prometheus сервера
        try:
            start_http_server(9091)
        except Exception as e:
            logging.warning(f"Failed to start Prometheus server: {e}")
    
    def record_metric(self, metric: PerformanceMetric, value: float, labels: Dict[str, str] = None):
        """Запись метрики"""
        labels = labels or {}
        
        if metric == PerformanceMetric.RESPONSE_TIME:
            self.metrics['response_time'].labels(**labels).observe(value)
        elif metric == PerformanceMetric.MEMORY_USAGE:
            self.metrics['memory_usage'].labels(**labels).set(value)
        elif metric == PerformanceMetric.CPU_USAGE:
            self.metrics['cpu_usage'].labels(**labels).set(value)
        elif metric == PerformanceMetric.DATABASE_QUERIES:
            self.metrics['database_queries'].labels(**labels).inc()
        elif metric == PerformanceMetric.CACHE_HITS:
            self.metrics['cache_hits'].labels(**labels).inc()
        elif metric == PerformanceMetric.CACHE_MISSES:
            self.metrics['cache_misses'].labels(**labels).inc()

class PerfectPerformanceManager:
    """Идеальный менеджер производительности"""
    
    def __init__(self):
        self.cache = AdvancedCache(CacheType.MEMORY)
        self.database_optimizer = DatabaseOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.profiler = PerformanceProfiler()
        self.monitor = PerformanceMonitor()
        
        self.optimization_thread = None
        self.is_optimizing = False
        self.optimization_interval = 60  # секунд
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def start_optimization(self):
        """Запуск оптимизации"""
        if self.is_optimizing:
            return
        
        self.is_optimizing = True
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()
        
        self.logger.info("Performance optimization started")
    
    def stop_optimization(self):
        """Остановка оптимизации"""
        self.is_optimizing = False
        if self.optimization_thread:
            self.optimization_thread.join()
        
        self.logger.info("Performance optimization stopped")
    
    def _optimization_loop(self):
        """Основной цикл оптимизации"""
        while self.is_optimizing:
            try:
                # Мониторинг памяти
                self.memory_optimizer.monitor_memory()
                
                # Очистка кэша при необходимости
                cache_stats = self.cache.get_stats()
                if cache_stats['size'] > 10000:  # Больше 10000 записей
                    self.cache.clear()
                
                # Оптимизация базы данных
                self._optimize_database_periodically()
                
                time.sleep(self.optimization_interval)
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                time.sleep(self.optimization_interval)
    
    def _optimize_database_periodically(self):
        """Периодическая оптимизация базы данных"""
        try:
            if database.engine.url.drivername == 'sqlite':
                with database.engine.connect() as conn:
                    conn.execute(text("PRAGMA optimize"))
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Database optimization error: {e}")
    
    def profile_endpoint(self, endpoint: str, method: str):
        """Декоратор для профилирования endpoint"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                start_cpu = psutil.cpu_percent()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss
                    end_cpu = psutil.cpu_percent()
                    
                    response_time = end_time - start_time
                    memory_usage = end_memory - start_memory
                    cpu_usage = end_cpu - start_cpu
                    
                    # Профилирование
                    self.profiler.profile_endpoint(
                        endpoint, method, response_time, memory_usage, cpu_usage
                    )
                    
                    # Запись метрик
                    self.monitor.record_metric(
                        PerformanceMetric.RESPONSE_TIME, 
                        response_time, 
                        {'endpoint': endpoint, 'method': method}
                    )
                    self.monitor.record_metric(
                        PerformanceMetric.MEMORY_USAGE, 
                        memory_usage, 
                        {'endpoint': endpoint}
                    )
                    self.monitor.record_metric(
                        PerformanceMetric.CPU_USAGE, 
                        cpu_usage, 
                        {'endpoint': endpoint}
                    )
            
            return wrapper
        return decorator
    
    def cached_query(self, cache_key: str, ttl: int = 3600):
        """Декоратор для кэширования запросов"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Генерация ключа кэша
                key = self.cache.generate_key(cache_key, *args, **kwargs)
                
                # Проверка кэша
                cached_result = self.cache.get(key)
                if cached_result is not None:
                    self.monitor.record_metric(
                        PerformanceMetric.CACHE_HITS, 
                        1, 
                        {'cache_type': 'query'}
                    )
                    return cached_result
                
                # Выполнение запроса
                result = func(*args, **kwargs)
                
                # Сохранение в кэш
                self.cache.set(key, result, ttl)
                self.monitor.record_metric(
                    PerformanceMetric.CACHE_MISSES, 
                    1, 
                    {'cache_type': 'query'}
                )
                
                return result
            
            return wrapper
        return decorator
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        return {
            'cache_stats': self.cache.get_stats(),
            'database_stats': self.database_optimizer.get_database_stats(),
            'memory_stats': self.memory_optimizer.get_memory_stats(),
            'endpoint_stats': self.profiler.get_endpoint_stats(),
            'slow_queries': self.database_optimizer.query_optimizer.get_slow_queries(),
            'slow_endpoints': self.profiler.get_slow_endpoints(),
            'query_stats': self.database_optimizer.query_optimizer.get_query_stats()
        }
    
    def optimize_system(self):
        """Оптимизация системы"""
        try:
            # Очистка кэшей
            self.cache.clear()
            self.database_optimizer.query_optimizer.clear_cache()
            
            # Принудительная сборка мусора
            collected = gc.collect()
            
            # Оптимизация базы данных
            self._optimize_database_periodically()
            
            self.logger.info(f"System optimization completed: collected {collected} objects")
            
        except Exception as e:
            self.logger.error(f"System optimization error: {e}")
    
    def get_recommendations(self) -> List[str]:
        """Получение рекомендаций по оптимизации"""
        recommendations = []
        
        # Анализ статистики
        stats = self.get_performance_stats()
        
        # Рекомендации по кэшу
        cache_stats = stats['cache_stats']
        if cache_stats['hit_rate'] < 0.7:
            recommendations.append("Низкий hit rate кэша. Рассмотрите увеличение TTL или оптимизацию ключей кэша.")
        
        # Рекомендации по базе данных
        slow_queries = stats['slow_queries']
        if len(slow_queries) > 5:
            recommendations.append("Обнаружено много медленных запросов. Рассмотрите добавление индексов или оптимизацию запросов.")
        
        # Рекомендации по памяти
        memory_stats = stats['memory_stats']
        if memory_stats['current_memory_percent'] > 80:
            recommendations.append("Высокое использование памяти. Рассмотрите увеличение RAM или оптимизацию кода.")
        
        # Рекомендации по endpoint
        slow_endpoints = stats['slow_endpoints']
        if slow_endpoints:
            recommendations.append(f"Медленные endpoint: {', '.join([ep['endpoint'] for ep in slow_endpoints[:3]])}")
        
        return recommendations

# Глобальный экземпляр идеального менеджера производительности
performance_manager = PerfectPerformanceManager()