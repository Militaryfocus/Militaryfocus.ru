"""
Система отказоустойчивости для блога
Обеспечивает надежность, резервирование и восстановление
"""

import os
import json
import time
import logging
import threading
import sqlite3
import shutil
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Callable, Any
import traceback
from contextlib import contextmanager

from blog import db
from blog.models import Post, User, Category, Comment

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blog_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Автоматический выключатель для предотвращения каскадных отказов"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                if self.state == 'OPEN':
                    if self._should_attempt_reset():
                        self.state = 'HALF_OPEN'
                    else:
                        raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
                
                try:
                    result = func(*args, **kwargs)
                    self._on_success()
                    return result
                except Exception as e:
                    self._on_failure()
                    raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class RetryMechanism:
    """Механизм повторных попыток с экспоненциальной задержкой"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < self.max_retries:
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {self.max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper

class HealthChecker:
    """Мониторинг здоровья системы"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = {}
        self.check_interval = 60  # секунд
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """Регистрация проверки здоровья"""
        self.checks[name] = check_func
        self.last_check_time[name] = 0
    
    def run_checks(self) -> Dict[str, Dict]:
        """Запуск всех проверок"""
        results = {}
        current_time = time.time()
        
        for name, check_func in self.checks.items():
            if current_time - self.last_check_time[name] >= self.check_interval:
                try:
                    start_time = time.time()
                    result = check_func()
                    end_time = time.time()
                    
                    results[name] = {
                        'status': 'healthy' if result else 'unhealthy',
                        'response_time': end_time - start_time,
                        'timestamp': datetime.now().isoformat(),
                        'details': result if isinstance(result, dict) else {}
                    }
                    
                    self.last_check_time[name] = current_time
                    
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.error(f"Health check {name} failed: {e}")
        
        return results
    
    def get_system_status(self) -> Dict:
        """Получение общего статуса системы"""
        checks = self.run_checks()
        
        healthy_count = sum(1 for check in checks.values() if check.get('status') == 'healthy')
        total_count = len(checks)
        
        overall_status = 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'healthy_services': healthy_count,
            'total_services': total_count,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }

class BackupManager:
    """Управление резервными копиями"""
    
    def __init__(self, backup_dir: str = 'backups'):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    @RetryMechanism(max_retries=2)
    def create_database_backup(self) -> str:
        """Создание резервной копии базы данных"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"database_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Для SQLite
            if 'sqlite' in db.engine.url.drivername:
                db_path = db.engine.url.database
                shutil.copy2(db_path, backup_path)
            else:
                # Для других БД можно использовать pg_dump, mysqldump и т.д.
                raise NotImplementedError("Backup for non-SQLite databases not implemented")
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise
    
    def create_content_backup(self) -> str:
        """Создание резервной копии контента"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"content_backup_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Экспорт всех данных в JSON
            backup_data = {
                'timestamp': timestamp,
                'posts': [],
                'users': [],
                'categories': [],
                'comments': []
            }
            
            # Экспорт постов
            posts = Post.query.all()
            for post in posts:
                backup_data['posts'].append({
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'content': post.content,
                    'excerpt': post.excerpt,
                    'is_published': post.is_published,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'author_id': post.author_id,
                    'category_id': post.category_id,
                    'tags': [tag.name for tag in post.tags]
                })
            
            # Экспорт пользователей (без паролей)
            users = User.query.all()
            for user in users:
                backup_data['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'bio': user.bio,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })
            
            # Экспорт категорий
            categories = Category.query.all()
            for category in categories:
                backup_data['categories'].append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'color': category.color
                })
            
            # Экспорт комментариев
            comments = Comment.query.all()
            for comment in comments:
                backup_data['comments'].append({
                    'id': comment.id,
                    'content': comment.content,
                    'is_approved': comment.is_approved,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                    'author_id': comment.author_id,
                    'post_id': comment.post_id,
                    'parent_id': comment.parent_id
                })
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Content backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create content backup: {e}")
            raise
    
    def cleanup_old_backups(self, keep_days: int = 7) -> None:
        """Очистка старых резервных копий"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {filename}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

class FaultTolerantSystem:
    """Основная система отказоустойчивости"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.backup_manager = BackupManager()
        self.circuit_breakers = {}
        self.monitoring_active = False
        self.monitoring_thread = None
        
        self._setup_health_checks()
        self._setup_circuit_breakers()
    
    def _setup_health_checks(self):
        """Настройка проверок здоровья"""
        
        def check_database():
            """Проверка доступности базы данных"""
            try:
                db.session.execute('SELECT 1')
                return {'connection': 'ok', 'query_time': 'fast'}
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return False
        
        def check_disk_space():
            """Проверка свободного места на диске"""
            try:
                statvfs = os.statvfs('.')
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
                free_gb = free_bytes / (1024**3)
                
                return {
                    'free_space_gb': round(free_gb, 2),
                    'status': 'ok' if free_gb > 1 else 'warning'
                }
            except Exception as e:
                logger.error(f"Disk space check failed: {e}")
                return False
        
        def check_ai_system():
            """Проверка ИИ системы"""
            try:
                from blog.ai_content import AIContentGenerator
                generator = AIContentGenerator()
                # Быстрая проверка генерации
                test_data = generator.generate_title('тест')
                return {'ai_generator': 'ok', 'test_title': len(test_data) > 0}
            except Exception as e:
                logger.error(f"AI system check failed: {e}")
                return False
        
        self.health_checker.register_check('database', check_database)
        self.health_checker.register_check('disk_space', check_disk_space)
        self.health_checker.register_check('ai_system', check_ai_system)
    
    def _setup_circuit_breakers(self):
        """Настройка автоматических выключателей"""
        self.circuit_breakers['ai_generation'] = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
        self.circuit_breakers['database'] = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.circuit_breakers['file_operations'] = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Получение автоматического выключателя"""
        return self.circuit_breakers.get(name, CircuitBreaker())
    
    def start_monitoring(self):
        """Запуск мониторинга системы"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                # Проверка здоровья системы
                status = self.health_checker.get_system_status()
                
                if status['overall_status'] == 'unhealthy':
                    logger.critical("System is unhealthy! Taking corrective actions...")
                    self._handle_system_failure(status)
                elif status['overall_status'] == 'degraded':
                    logger.warning("System is degraded. Monitoring closely...")
                
                # Создание резервных копий (каждые 6 часов)
                if datetime.now().hour % 6 == 0 and datetime.now().minute < 5:
                    self._create_scheduled_backup()
                
                # Очистка старых резервных копий (раз в день)
                if datetime.now().hour == 2 and datetime.now().minute < 5:
                    self.backup_manager.cleanup_old_backups()
                
                time.sleep(300)  # Проверка каждые 5 минут
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)  # Короткая пауза при ошибке
    
    def _handle_system_failure(self, status: Dict):
        """Обработка отказа системы"""
        try:
            # Создание экстренной резервной копии
            self.backup_manager.create_database_backup()
            
            # Попытка восстановления сервисов
            for check_name, check_result in status['checks'].items():
                if check_result.get('status') == 'error':
                    logger.info(f"Attempting to recover service: {check_name}")
                    self._attempt_service_recovery(check_name)
            
        except Exception as e:
            logger.critical(f"Failed to handle system failure: {e}")
    
    def _attempt_service_recovery(self, service_name: str):
        """Попытка восстановления сервиса"""
        if service_name == 'database':
            try:
                # Переподключение к базе данных
                db.session.close()
                db.engine.dispose()
                logger.info("Database connection reset")
            except Exception as e:
                logger.error(f"Failed to reset database connection: {e}")
        
        elif service_name == 'ai_system':
            try:
                # Сброс ИИ системы
                from blog.ai_content import AIContentGenerator
                # Можно добавить логику сброса кеша ИИ
                logger.info("AI system reset attempted")
            except Exception as e:
                logger.error(f"Failed to reset AI system: {e}")
    
    def _create_scheduled_backup(self):
        """Создание плановой резервной копии"""
        try:
            self.backup_manager.create_database_backup()
            self.backup_manager.create_content_backup()
            logger.info("Scheduled backup completed")
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def get_system_metrics(self) -> Dict:
        """Получение метрик системы"""
        return {
            'health_status': self.health_checker.get_system_status(),
            'circuit_breakers': {
                name: {
                    'state': cb.state,
                    'failure_count': cb.failure_count,
                    'last_failure': cb.last_failure_time
                }
                for name, cb in self.circuit_breakers.items()
            },
            'monitoring_active': self.monitoring_active,
            'backup_info': self._get_backup_info()
        }
    
    def _get_backup_info(self) -> Dict:
        """Информация о резервных копиях"""
        try:
            backups = []
            for filename in os.listdir(self.backup_manager.backup_dir):
                file_path = os.path.join(self.backup_manager.backup_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    backups.append({
                        'filename': filename,
                        'size_mb': round(stat.st_size / (1024**2), 2),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            return {
                'total_backups': len(backups),
                'latest_backups': sorted(backups, key=lambda x: x['created'], reverse=True)[:5]
            }
        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return {'error': str(e)}

# Глобальный экземпляр системы отказоустойчивости
fault_tolerant_system = FaultTolerantSystem()

# Декораторы для использования в приложении
database_circuit_breaker = fault_tolerant_system.get_circuit_breaker('database')
ai_circuit_breaker = fault_tolerant_system.get_circuit_breaker('ai_generation')
file_circuit_breaker = fault_tolerant_system.get_circuit_breaker('file_operations')

# Контекстный менеджер для безопасных операций с БД
@contextmanager
def safe_db_operation():
    """Безопасные операции с базой данных"""
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        db.session.close()

def init_fault_tolerance():
    """Инициализация системы отказоустойчивости"""
    fault_tolerant_system.start_monitoring()
    logger.info("Fault tolerance system initialized")

def shutdown_fault_tolerance():
    """Завершение работы системы отказоустойчивости"""
    fault_tolerant_system.stop_monitoring()
    logger.info("Fault tolerance system shutdown")