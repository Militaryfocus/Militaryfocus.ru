"""
Система мониторинга и логирования для блога
Отслеживает производительность, ошибки и метрики системы
"""

import os
import json
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import threading
from functools import wraps

from blog.models_perfect import Post, User, Comment
from blog import db

class SystemMonitor:
    """Монитор системных ресурсов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_cpu_usage(self) -> float:
        """Получение использования CPU"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            self.logger.error(f"Ошибка получения CPU: {e}")
            return 0.0
    
    def get_memory_usage(self) -> float:
        """Получение использования памяти"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            self.logger.error(f"Ошибка получения памяти: {e}")
            return 0.0
    
    def get_disk_usage(self) -> float:
        """Получение использования диска"""
        try:
            disk = psutil.disk_usage('/')
            return (disk.used / disk.total) * 100
        except Exception as e:
            self.logger.error(f"Ошибка получения диска: {e}")
            return 0.0
    
    def get_system_info(self) -> Dict[str, Any]:
        """Получение информации о системе"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'boot_time': psutil.boot_time(),
                'platform': psutil.platform()
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения системной информации: {e}")
            return {}

class MetricsCollector:
    """Сборщик метрик системы"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history))
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, timestamp: Optional[datetime] = None):
        """Запись метрики"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self._lock:
            self.metrics_history[name].append({
                'value': value,
                'timestamp': timestamp.isoformat()
            })
    
    def increment_counter(self, name: str, amount: int = 1):
        """Увеличение счетчика"""
        with self._lock:
            self.counters[name] += amount
    
    def record_timing(self, name: str, duration: float):
        """Запись времени выполнения"""
        with self._lock:
            self.timers[name].append(duration)
            # Ограничиваем историю таймеров
            if len(self.timers[name]) > 100:
                self.timers[name] = self.timers[name][-100:]
    
    def get_metric_stats(self, name: str) -> Dict:
        """Получение статистики по метрике"""
        with self._lock:
            history = list(self.metrics_history[name])
            
            if not history:
                return {'count': 0}
            
            values = [item['value'] for item in history]
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1] if values else None,
                'last_updated': history[-1]['timestamp'] if history else None
            }
    
    def get_counter_value(self, name: str) -> int:
        """Получение значения счетчика"""
        return self.counters.get(name, 0)
    
    def get_timing_stats(self, name: str) -> Dict:
        """Получение статистики по времени выполнения"""
        with self._lock:
            timings = self.timers.get(name, [])
            
            if not timings:
                return {'count': 0}
            
            return {
                'count': len(timings),
                'min': min(timings),
                'max': max(timings),
                'avg': sum(timings) / len(timings),
                'p95': sorted(timings)[int(len(timings) * 0.95)] if len(timings) > 1 else timings[0]
            }

class PerformanceMonitor:
    """Мониторинг производительности"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logging.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logging.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                # Системные метрики
                self._collect_system_metrics()
                
                # Метрики базы данных
                self._collect_database_metrics()
                
                # Метрики приложения
                self._collect_application_metrics()
                
                time.sleep(30)  # Сбор метрик каждые 30 секунд
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.record_metric('system.cpu_percent', cpu_percent)
            
            # Память
            memory = psutil.virtual_memory()
            self.metrics.record_metric('system.memory_percent', memory.percent)
            self.metrics.record_metric('system.memory_available_mb', memory.available / 1024 / 1024)
            
            # Диск
            disk = psutil.disk_usage('.')
            self.metrics.record_metric('system.disk_percent', (disk.used / disk.total) * 100)
            self.metrics.record_metric('system.disk_free_gb', disk.free / 1024 / 1024 / 1024)
            
            # Процесс
            process = psutil.Process()
            self.metrics.record_metric('process.memory_mb', process.memory_info().rss / 1024 / 1024)
            self.metrics.record_metric('process.cpu_percent', process.cpu_percent())
            
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
    
    def _collect_database_metrics(self):
        """Сбор метрик базы данных"""
        try:
            # Количество записей
            posts_count = Post.query.count()
            users_count = User.query.count()
            comments_count = Comment.query.count()
            
            self.metrics.record_metric('database.posts_count', posts_count)
            self.metrics.record_metric('database.users_count', users_count)
            self.metrics.record_metric('database.comments_count', comments_count)
            
            # Размер базы данных (для SQLite)
            if hasattr(db.engine.url, 'database') and db.engine.url.database:
                db_path = db.engine.url.database
                if os.path.exists(db_path):
                    db_size_mb = os.path.getsize(db_path) / 1024 / 1024
                    self.metrics.record_metric('database.size_mb', db_size_mb)
            
        except Exception as e:
            logging.error(f"Error collecting database metrics: {e}")
    
    def _collect_application_metrics(self):
        """Сбор метрик приложения"""
        try:
            # Активность за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            
            new_posts = Post.query.filter(Post.created_at >= yesterday).count()
            new_comments = Comment.query.filter(Comment.created_at >= yesterday).count()
            
            self.metrics.record_metric('app.new_posts_24h', new_posts)
            self.metrics.record_metric('app.new_comments_24h', new_comments)
            
            # Популярные посты
            popular_posts = Post.query.filter_by(is_published=True).order_by(Post.views_count.desc()).limit(10).all()
            if popular_posts:
                avg_views = sum(post.views_count for post in popular_posts) / len(popular_posts)
                self.metrics.record_metric('app.avg_views_top10', avg_views)
            
        except Exception as e:
            logging.error(f"Error collecting application metrics: {e}")

class ErrorTracker:
    """Отслеживание ошибок"""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_error(self, error: Exception, context: Dict = None):
        """Запись ошибки"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context or {}
        }
        
        with self._lock:
            self.errors.append(error_info)
            self.error_counts[error_info['type']] += 1
        
        # Логирование
        logging.error(f"Error recorded: {error_info['type']} - {error_info['message']}")
    
    def get_error_stats(self) -> Dict:
        """Получение статистики ошибок"""
        with self._lock:
            total_errors = len(self.errors)
            
            # Ошибки за последний час
            hour_ago = datetime.now() - timedelta(hours=1)
            recent_errors = [
                err for err in self.errors 
                if datetime.fromisoformat(err['timestamp']) >= hour_ago
            ]
            
            return {
                'total_errors': total_errors,
                'errors_last_hour': len(recent_errors),
                'error_types': dict(self.error_counts),
                'latest_errors': list(self.errors)[-10:] if self.errors else []
            }

class AlertManager:
    """Управление уведомлениями"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alert_rules = []
        self.alert_history = deque(maxlen=100)
        self.cooldown_periods = {}
    
    def add_alert_rule(self, name: str, condition: callable, message: str, cooldown: int = 300):
        """Добавление правила уведомления"""
        self.alert_rules.append({
            'name': name,
            'condition': condition,
            'message': message,
            'cooldown': cooldown
        })
    
    def check_alerts(self):
        """Проверка условий уведомлений"""
        current_time = time.time()
        
        for rule in self.alert_rules:
            rule_name = rule['name']
            
            # Проверка cooldown
            if rule_name in self.cooldown_periods:
                if current_time - self.cooldown_periods[rule_name] < rule['cooldown']:
                    continue
            
            # Проверка условия
            try:
                if rule['condition'](self.metrics):
                    self._trigger_alert(rule)
                    self.cooldown_periods[rule_name] = current_time
            except Exception as e:
                logging.error(f"Error checking alert rule {rule_name}: {e}")
    
    def _trigger_alert(self, rule: Dict):
        """Срабатывание уведомления"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'rule_name': rule['name'],
            'message': rule['message'],
            'severity': 'warning'
        }
        
        self.alert_history.append(alert)
        logging.warning(f"ALERT: {rule['name']} - {rule['message']}")
    
    def get_active_alerts(self) -> List[Dict]:
        """Получение активных уведомлений"""
        # Уведомления за последний час считаются активными
        hour_ago = datetime.now() - timedelta(hours=1)
        
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) >= hour_ago
        ]

class MonitoringDashboard:
    """Панель мониторинга"""
    
    def __init__(self, metrics_collector: MetricsCollector, error_tracker: ErrorTracker, alert_manager: AlertManager):
        self.metrics = metrics_collector
        self.error_tracker = error_tracker
        self.alert_manager = alert_manager
    
    def get_dashboard_data(self) -> Dict:
        """Получение данных для панели мониторинга"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._get_system_health(),
            'performance_metrics': self._get_performance_metrics(),
            'error_summary': self.error_tracker.get_error_stats(),
            'active_alerts': self.alert_manager.get_active_alerts(),
            'database_stats': self._get_database_stats(),
            'application_stats': self._get_application_stats()
        }
    
    def _get_system_health(self) -> Dict:
        """Получение состояния системы"""
        cpu_stats = self.metrics.get_metric_stats('system.cpu_percent')
        memory_stats = self.metrics.get_metric_stats('system.memory_percent')
        disk_stats = self.metrics.get_metric_stats('system.disk_percent')
        
        # Определение общего состояния
        health_score = 100
        
        if cpu_stats.get('latest', 0) > 80:
            health_score -= 20
        if memory_stats.get('latest', 0) > 85:
            health_score -= 20
        if disk_stats.get('latest', 0) > 90:
            health_score -= 30
        
        if health_score >= 80:
            status = 'healthy'
        elif health_score >= 60:
            status = 'warning'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'score': health_score,
            'cpu_usage': cpu_stats.get('latest', 0),
            'memory_usage': memory_stats.get('latest', 0),
            'disk_usage': disk_stats.get('latest', 0)
        }
    
    def _get_performance_metrics(self) -> Dict:
        """Получение метрик производительности"""
        return {
            'response_times': {
                'page_load': self.metrics.get_timing_stats('page_load'),
                'database_query': self.metrics.get_timing_stats('database_query'),
                'ai_generation': self.metrics.get_timing_stats('ai_generation')
            },
            'throughput': {
                'requests_per_minute': self.metrics.get_counter_value('requests') / 60,
                'posts_generated_per_hour': self.metrics.get_counter_value('ai_posts_generated')
            }
        }
    
    def _get_database_stats(self) -> Dict:
        """Получение статистики базы данных"""
        return {
            'total_posts': self.metrics.get_metric_stats('database.posts_count').get('latest', 0),
            'total_users': self.metrics.get_metric_stats('database.users_count').get('latest', 0),
            'total_comments': self.metrics.get_metric_stats('database.comments_count').get('latest', 0),
            'database_size_mb': self.metrics.get_metric_stats('database.size_mb').get('latest', 0)
        }
    
    def _get_application_stats(self) -> Dict:
        """Получение статистики приложения"""
        return {
            'new_posts_24h': self.metrics.get_metric_stats('app.new_posts_24h').get('latest', 0),
            'new_comments_24h': self.metrics.get_metric_stats('app.new_comments_24h').get('latest', 0),
            'avg_views_top10': self.metrics.get_metric_stats('app.avg_views_top10').get('latest', 0)
        }

# Декораторы для мониторинга
def monitor_timing(metric_name: str):
    """Декоратор для измерения времени выполнения"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitoring_system.metrics.record_timing(metric_name, duration)
        return wrapper
    return decorator

def monitor_counter(metric_name: str):
    """Декоратор для подсчета вызовов"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitoring_system.metrics.increment_counter(metric_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def monitor_errors(context: str = None):
    """Декоратор для отслеживания ошибок"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                monitoring_system.error_tracker.record_error(e, {'function': func.__name__, 'context': context})
                raise
        return wrapper
    return decorator

class MonitoringSystem:
    """Основная система мониторинга"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.performance_monitor = PerformanceMonitor(self.metrics)
        self.error_tracker = ErrorTracker()
        self.alert_manager = AlertManager(self.metrics)
        self.dashboard = MonitoringDashboard(self.metrics, self.error_tracker, self.alert_manager)
        
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Настройка стандартных уведомлений"""
        
        # Высокое использование CPU
        self.alert_manager.add_alert_rule(
            'high_cpu',
            lambda metrics: metrics.get_metric_stats('system.cpu_percent').get('latest', 0) > 90,
            'Высокое использование CPU (>90%)',
            cooldown=600
        )
        
        # Высокое использование памяти
        self.alert_manager.add_alert_rule(
            'high_memory',
            lambda metrics: metrics.get_metric_stats('system.memory_percent').get('latest', 0) > 90,
            'Высокое использование памяти (>90%)',
            cooldown=600
        )
        
        # Мало свободного места на диске
        self.alert_manager.add_alert_rule(
            'low_disk_space',
            lambda metrics: metrics.get_metric_stats('system.disk_free_gb').get('latest', 100) < 1,
            'Мало свободного места на диске (<1GB)',
            cooldown=3600
        )
        
        # Много ошибок
        def check_error_rate(metrics):
            error_stats = self.error_tracker.get_error_stats()
            return error_stats['errors_last_hour'] > 10
        
        self.alert_manager.add_alert_rule(
            'high_error_rate',
            check_error_rate,
            'Высокий уровень ошибок (>10 за час)',
            cooldown=1800
        )
    
    def start(self):
        """Запуск системы мониторинга"""
        self.performance_monitor.start_monitoring()
        logging.info("Monitoring system started")
    
    def stop(self):
        """Остановка системы мониторинга"""
        self.performance_monitor.stop_monitoring()
        logging.info("Monitoring system stopped")
    
    def check_health(self):
        """Проверка состояния системы"""
        self.alert_manager.check_alerts()
        return self.dashboard.get_dashboard_data()

# Глобальный экземпляр системы мониторинга
monitoring_system = MonitoringSystem()