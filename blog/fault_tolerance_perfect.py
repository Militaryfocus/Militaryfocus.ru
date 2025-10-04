"""
Идеальная система отказоустойчивости для блога
Включает мониторинг, автоматическое восстановление, резервирование и масштабирование
"""

import os
import time
import json
import logging
import threading
import asyncio
import aiohttp
import psutil
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import queue
import subprocess
import signal
import sys
from contextlib import contextmanager
import sqlite3
import requests
from flask import current_app
from sqlalchemy import text, create_engine
from sqlalchemy.pool import QueuePool
# import docker  # Необязательный импорт
# import kubernetes  # Необязательный импорт
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from blog.database import db
from blog.database import db as database

class HealthStatus(Enum):
    """Статусы здоровья"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """Типы сервисов"""
    DATABASE = "database"
    REDIS = "redis"
    AI_SERVICE = "ai_service"
    STORAGE = "storage"
    EMAIL = "email"
    CDN = "cdn"
    MONITORING = "monitoring"

@dataclass
class HealthCheck:
    """Результат проверки здоровья"""
    service: ServiceType
    status: HealthStatus
    response_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class Alert:
    """Алерт системы"""
    id: str
    service: ServiceType
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

class CircuitBreaker:
    """Circuit Breaker для защиты от каскадных сбоев"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Вызов функции через circuit breaker"""
        with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                
                raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Получение состояния circuit breaker"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time,
            'failure_threshold': self.failure_threshold
        }

class RetryMechanism:
    """Механизм повторных попыток"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
    
    def execute(self, func: Callable, *args, **kwargs):
        """Выполнение функции с повторными попытками"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self.base_delay * (self.backoff_factor ** attempt)
                    time.sleep(delay)
                else:
                    break
        
        raise last_exception

class LoadBalancer:
    """Балансировщик нагрузки"""
    
    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current_index = 0
        self.endpoint_health = {endpoint: True for endpoint in endpoints}
        self.endpoint_stats = {endpoint: {'requests': 0, 'errors': 0} for endpoint in endpoints}
        self.lock = threading.Lock()
    
    def get_endpoint(self) -> str:
        """Получение следующего доступного endpoint"""
        with self.lock:
            # Round-robin с проверкой здоровья
            for _ in range(len(self.endpoints)):
                endpoint = self.endpoints[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.endpoints)
                
                if self.endpoint_health[endpoint]:
                    self.endpoint_stats[endpoint]['requests'] += 1
                    return endpoint
            
            # Если все endpoint недоступны, возвращаем первый
            return self.endpoints[0]
    
    def mark_endpoint_unhealthy(self, endpoint: str):
        """Помечание endpoint как нездорового"""
        with self.lock:
            self.endpoint_health[endpoint] = False
            self.endpoint_stats[endpoint]['errors'] += 1
    
    def mark_endpoint_healthy(self, endpoint: str):
        """Помечание endpoint как здорового"""
        with self.lock:
            self.endpoint_health[endpoint] = True
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        with self.lock:
            return {
                'endpoints': self.endpoints,
                'health': self.endpoint_health.copy(),
                'stats': self.endpoint_stats.copy()
            }

class HealthChecker:
    """Проверка здоровья сервисов"""
    
    def __init__(self):
        self.checkers = {
            ServiceType.DATABASE: self._check_database,
            ServiceType.REDIS: self._check_redis,
            ServiceType.AI_SERVICE: self._check_ai_service,
            ServiceType.STORAGE: self._check_storage,
            ServiceType.EMAIL: self._check_email,
            ServiceType.CDN: self._check_cdn,
            ServiceType.MONITORING: self._check_monitoring
        }
        self.circuit_breakers = {
            service: CircuitBreaker() for service in ServiceType
        }
        self.retry_mechanisms = {
            service: RetryMechanism() for service in ServiceType
        }
    
    def check_service(self, service: ServiceType) -> HealthCheck:
        """Проверка здоровья сервиса"""
        checker = self.checkers.get(service)
        if not checker:
            return HealthCheck(
                service=service,
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                error_message="No checker available"
            )
        
        start_time = time.time()
        
        try:
            # Используем circuit breaker и retry mechanism
            circuit_breaker = self.circuit_breakers[service]
            retry_mechanism = self.retry_mechanisms[service]
            
            result = circuit_breaker.call(retry_mechanism.execute, checker)
            
            response_time = time.time() - start_time
            
            return HealthCheck(
                service=service,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                metadata=result
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            return HealthCheck(
                service=service,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error_message=str(e)
            )
    
    def _check_database(self) -> Dict[str, Any]:
        """Проверка базы данных"""
        try:
            # Проверка подключения
            with database.engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if not result:
                    raise Exception("Database query failed")
            
            # Проверка производительности
            start_time = time.time()
            with database.engine.connect() as conn:
                conn.execute(text("SELECT COUNT(*) FROM users"))
            query_time = time.time() - start_time
            
            # Проверка размера базы
            db_size = self._get_database_size()
            
            return {
                'connection': 'ok',
                'query_time': query_time,
                'database_size': db_size,
                'active_connections': database.engine.pool.size()
            }
            
        except Exception as e:
            raise Exception(f"Database health check failed: {str(e)}")
    
    def _check_redis(self) -> Dict[str, Any]:
        """Проверка Redis"""
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            
            # Проверка подключения
            redis_client.ping()
            
            # Проверка производительности
            start_time = time.time()
            redis_client.set('health_check', 'ok', ex=10)
            redis_client.get('health_check')
            response_time = time.time() - start_time
            
            # Получение статистики
            info = redis_client.info()
            
            return {
                'connection': 'ok',
                'response_time': response_time,
                'memory_usage': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'uptime': info.get('uptime_in_seconds')
            }
            
        except Exception as e:
            raise Exception(f"Redis health check failed: {str(e)}")
    
    def _check_ai_service(self) -> Dict[str, Any]:
        """Проверка ИИ сервиса"""
        try:
            # Проверка доступности ИИ провайдеров
            from blog.ai_content_perfect import perfect_ai_generator
            
            # Простой тест генерации
            start_time = time.time()
            test_title = perfect_ai_generator.generate_post_title("тест")
            response_time = time.time() - start_time
            
            # Получение статистики
            stats = perfect_ai_generator.get_system_stats()
            
            return {
                'connection': 'ok',
                'response_time': response_time,
                'available_providers': len(stats['available_providers']),
                'quality_score': stats['quality_stats']['avg_quality'],
                'cache_size': stats['cache_size']
            }
            
        except Exception as e:
            raise Exception(f"AI service health check failed: {str(e)}")
    
    def _check_storage(self) -> Dict[str, Any]:
        """Проверка хранилища"""
        try:
            # Проверка доступности директорий
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Проверка свободного места
            statvfs = os.statvfs(upload_dir)
            free_space = statvfs.f_frsize * statvfs.f_bavail
            total_space = statvfs.f_frsize * statvfs.f_blocks
            
            # Проверка записи
            test_file = os.path.join(upload_dir, 'health_check.txt')
            with open(test_file, 'w') as f:
                f.write('health check')
            
            with open(test_file, 'r') as f:
                content = f.read()
            
            os.remove(test_file)
            
            if content != 'health check':
                raise Exception("Storage write/read test failed")
            
            return {
                'connection': 'ok',
                'free_space': free_space,
                'total_space': total_space,
                'free_percentage': (free_space / total_space) * 100
            }
            
        except Exception as e:
            raise Exception(f"Storage health check failed: {str(e)}")
    
    def _check_email(self) -> Dict[str, Any]:
        """Проверка email сервиса"""
        try:
            # Проверка конфигурации SMTP
            smtp_server = current_app.config.get('MAIL_SERVER')
            smtp_port = current_app.config.get('MAIL_PORT')
            
            if not smtp_server or not smtp_port:
                raise Exception("Email configuration missing")
            
            # Простая проверка подключения
            import smtplib
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.quit()
            
            return {
                'connection': 'ok',
                'smtp_server': smtp_server,
                'smtp_port': smtp_port
            }
            
        except Exception as e:
            raise Exception(f"Email service health check failed: {str(e)}")
    
    def _check_cdn(self) -> Dict[str, Any]:
        """Проверка CDN"""
        try:
            # Проверка доступности CDN
            cdn_url = current_app.config.get('CDN_URL', 'https://cdn.jsdelivr.net')
            
            start_time = time.time()
            response = requests.get(cdn_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"CDN returned status {response.status_code}")
            
            return {
                'connection': 'ok',
                'response_time': response_time,
                'status_code': response.status_code,
                'cdn_url': cdn_url
            }
            
        except Exception as e:
            raise Exception(f"CDN health check failed: {str(e)}")
    
    def _check_monitoring(self) -> Dict[str, Any]:
        """Проверка системы мониторинга"""
        try:
            # Проверка Prometheus
            prometheus_port = current_app.config.get('PROMETHEUS_PORT', 9090)
            
            start_time = time.time()
            response = requests.get(f'http://localhost:{prometheus_port}/api/v1/query?query=up', timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Prometheus returned status {response.status_code}")
            
            return {
                'connection': 'ok',
                'response_time': response_time,
                'prometheus_port': prometheus_port
            }
            
        except Exception as e:
            raise Exception(f"Monitoring health check failed: {str(e)}")
    
    def _get_database_size(self) -> str:
        """Получение размера базы данных"""
        try:
            if database.engine.url.drivername == 'sqlite':
                db_path = database.engine.url.database
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    return f"{size_bytes / 1024 / 1024:.2f} MB"
            return "Unknown"
        except Exception:
            return "Unknown"

class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self.alerts = {}
        self.alert_rules = {
            ServiceType.DATABASE: {
                'response_time_threshold': 5.0,
                'error_threshold': 3
            },
            ServiceType.REDIS: {
                'response_time_threshold': 1.0,
                'error_threshold': 3
            },
            ServiceType.AI_SERVICE: {
                'response_time_threshold': 10.0,
                'error_threshold': 2
            },
            ServiceType.STORAGE: {
                'free_space_threshold': 10.0,  # 10% свободного места
                'error_threshold': 1
            }
        }
        self.notification_channels = []
        self.lock = threading.Lock()
    
    def check_health_and_alert(self, health_check: HealthCheck):
        """Проверка здоровья и отправка алертов"""
        service = health_check.service
        rules = self.alert_rules.get(service, {})
        
        # Проверка правил алертов
        should_alert = False
        alert_message = ""
        
        if health_check.status == HealthStatus.CRITICAL:
            should_alert = True
            alert_message = f"Critical: {service.value} is in critical state"
        elif health_check.status == HealthStatus.UNHEALTHY:
            should_alert = True
            alert_message = f"Unhealthy: {service.value} is not responding"
        elif health_check.response_time > rules.get('response_time_threshold', 10.0):
            should_alert = True
            alert_message = f"Slow response: {service.value} response time {health_check.response_time:.2f}s"
        elif health_check.error_message:
            should_alert = True
            alert_message = f"Error: {service.value} - {health_check.error_message}"
        
        if should_alert:
            self._create_alert(service, 'warning', alert_message, health_check.metadata)
    
    def _create_alert(self, service: ServiceType, severity: str, message: str, metadata: Dict[str, Any] = None):
        """Создание алерта"""
        alert_id = f"{service.value}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            service=service,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        with self.lock:
            self.alerts[alert_id] = alert
        
        # Отправка уведомлений
        self._send_notifications(alert)
    
    def _send_notifications(self, alert: Alert):
        """Отправка уведомлений"""
        for channel in self.notification_channels:
            try:
                channel.send_alert(alert)
            except Exception as e:
                logging.error(f"Failed to send alert via {channel.__class__.__name__}: {e}")
    
    def resolve_alert(self, alert_id: str):
        """Разрешение алерта"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].resolved_at = datetime.utcnow()
    
    def get_active_alerts(self) -> List[Alert]:
        """Получение активных алертов"""
        with self.lock:
            return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Получение статистики алертов"""
        with self.lock:
            total_alerts = len(self.alerts)
            active_alerts = len([a for a in self.alerts.values() if not a.resolved])
            resolved_alerts = total_alerts - active_alerts
            
            alerts_by_service = defaultdict(int)
            alerts_by_severity = defaultdict(int)
            
            for alert in self.alerts.values():
                alerts_by_service[alert.service.value] += 1
                alerts_by_severity[alert.severity] += 1
            
            return {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'resolved_alerts': resolved_alerts,
                'alerts_by_service': dict(alerts_by_service),
                'alerts_by_severity': dict(alerts_by_severity)
            }

class AutoRecovery:
    """Автоматическое восстановление"""
    
    def __init__(self):
        self.recovery_actions = {
            ServiceType.DATABASE: self._recover_database,
            ServiceType.REDIS: self._recover_redis,
            ServiceType.AI_SERVICE: self._recover_ai_service,
            ServiceType.STORAGE: self._recover_storage
        }
        self.recovery_history = deque(maxlen=100)
    
    def attempt_recovery(self, service: ServiceType, health_check: HealthCheck) -> bool:
        """Попытка автоматического восстановления"""
        recovery_action = self.recovery_actions.get(service)
        if not recovery_action:
            return False
        
        try:
            start_time = time.time()
            success = recovery_action(health_check)
            recovery_time = time.time() - start_time
            
            self.recovery_history.append({
                'service': service.value,
                'timestamp': datetime.utcnow(),
                'success': success,
                'recovery_time': recovery_time,
                'health_check': health_check
            })
            
            return success
            
        except Exception as e:
            logging.error(f"Recovery failed for {service.value}: {e}")
            return False
    
    def _recover_database(self, health_check: HealthCheck) -> bool:
        """Восстановление базы данных"""
        try:
            # Переподключение к базе
            database.engine.dispose()
            database.engine.connect()
            
            # Проверка целостности
            with database.engine.connect() as conn:
                conn.execute(text("PRAGMA integrity_check"))
            
            return True
            
        except Exception as e:
            logging.error(f"Database recovery failed: {e}")
            return False
    
    def _recover_redis(self, health_check: HealthCheck) -> bool:
        """Восстановление Redis"""
        try:
            # Переподключение к Redis
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.ping()
            
            # Очистка кэша при необходимости
            if health_check.metadata and health_check.metadata.get('memory_usage', '0B') > '100MB':
                redis_client.flushdb()
            
            return True
            
        except Exception as e:
            logging.error(f"Redis recovery failed: {e}")
            return False
    
    def _recover_ai_service(self, health_check: HealthCheck) -> bool:
        """Восстановление ИИ сервиса"""
        try:
            # Перезагрузка ИИ генератора
            from blog.ai_content_perfect import perfect_ai_generator
            perfect_ai_generator.optimize_performance()
            
            # Тест генерации
            test_title = perfect_ai_generator.generate_post_title("тест восстановления")
            if not test_title:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"AI service recovery failed: {e}")
            return False
    
    def _recover_storage(self, health_check: HealthCheck) -> bool:
        """Восстановление хранилища"""
        try:
            # Проверка и создание директорий
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Очистка временных файлов
            for file in os.listdir(upload_dir):
                if file.startswith('temp_'):
                    os.remove(os.path.join(upload_dir, file))
            
            return True
            
        except Exception as e:
            logging.error(f"Storage recovery failed: {e}")
            return False

class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.prometheus_metrics = {
            'health_check_duration': Histogram('health_check_duration_seconds', 'Health check duration', ['service']),
            'health_check_status': Gauge('health_check_status', 'Health check status', ['service']),
            'alert_count': Counter('alert_total', 'Total alerts', ['service', 'severity']),
            'recovery_attempts': Counter('recovery_attempts_total', 'Recovery attempts', ['service', 'success'])
        }
        
        # Запуск Prometheus сервера
        try:
            start_http_server(9090)
        except Exception as e:
            logging.warning(f"Failed to start Prometheus server: {e}")
    
    def record_health_check(self, health_check: HealthCheck):
        """Запись метрик проверки здоровья"""
        service = health_check.service.value
        
        # Prometheus метрики
        self.prometheus_metrics['health_check_duration'].labels(service=service).observe(health_check.response_time)
        
        status_value = {
            HealthStatus.HEALTHY: 1,
            HealthStatus.DEGRADED: 0.5,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: -1
        }.get(health_check.status, -1)
        
        self.prometheus_metrics['health_check_status'].labels(service=service).set(status_value)
        
        # Внутренние метрики
        self.metrics[service].append({
            'timestamp': health_check.timestamp,
            'status': health_check.status.value,
            'response_time': health_check.response_time,
            'error_message': health_check.error_message
        })
    
    def record_alert(self, alert: Alert):
        """Запись метрик алерта"""
        service = alert.service.value
        severity = alert.severity
        
        self.prometheus_metrics['alert_count'].labels(service=service, severity=severity).inc()
    
    def record_recovery(self, service: ServiceType, success: bool):
        """Запись метрик восстановления"""
        service_name = service.value
        success_str = 'true' if success else 'false'
        
        self.prometheus_metrics['recovery_attempts'].labels(service=service_name, success=success_str).inc()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        summary = {}
        
        for service, metrics_list in self.metrics.items():
            if not metrics_list:
                continue
            
            recent_metrics = metrics_list[-10:]  # Последние 10 проверок
            
            summary[service] = {
                'total_checks': len(metrics_list),
                'recent_checks': len(recent_metrics),
                'avg_response_time': sum(m['response_time'] for m in recent_metrics) / len(recent_metrics),
                'last_status': recent_metrics[-1]['status'] if recent_metrics else 'unknown',
                'error_rate': len([m for m in recent_metrics if m['error_message']]) / len(recent_metrics)
            }
        
        return summary

class PerfectFaultToleranceSystem:
    """Идеальная система отказоустойчивости"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.auto_recovery = AutoRecovery()
        self.metrics_collector = MetricsCollector()
        
        self.monitoring_thread = None
        self.is_monitoring = False
        self.monitoring_interval = 30  # секунд
        
        self.system_stats = {
            'uptime_start': datetime.utcnow(),
            'total_health_checks': 0,
            'total_alerts': 0,
            'total_recoveries': 0,
            'successful_recoveries': 0
        }
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Fault tolerance monitoring started")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        
        self.logger.info("Fault tolerance monitoring stopped")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.is_monitoring:
            try:
                # Проверка всех сервисов
                for service in ServiceType:
                    health_check = self.health_checker.check_service(service)
                    
                    # Запись метрик
                    self.metrics_collector.record_health_check(health_check)
                    self.system_stats['total_health_checks'] += 1
                    
                    # Проверка алертов
                    self.alert_manager.check_health_and_alert(health_check)
                    
                    # Автоматическое восстановление
                    if health_check.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                        recovery_success = self.auto_recovery.attempt_recovery(service, health_check)
                        self.system_stats['total_recoveries'] += 1
                        if recovery_success:
                            self.system_stats['successful_recoveries'] += 1
                        
                        self.metrics_collector.record_recovery(service, recovery_success)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Получение общего здоровья системы"""
        health_checks = {}
        overall_status = HealthStatus.HEALTHY
        
        for service in ServiceType:
            health_check = self.health_checker.check_service(service)
            health_checks[service.value] = {
                'status': health_check.status.value,
                'response_time': health_check.response_time,
                'error_message': health_check.error_message,
                'timestamp': health_check.timestamp.isoformat()
            }
            
            # Определение общего статуса
            if health_check.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
            elif health_check.status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                overall_status = HealthStatus.UNHEALTHY
            elif health_check.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'overall_status': overall_status.value,
            'services': health_checks,
            'uptime': (datetime.utcnow() - self.system_stats['uptime_start']).total_seconds(),
            'stats': self.system_stats,
            'alerts': self.alert_manager.get_alert_stats(),
            'metrics': self.metrics_collector.get_metrics_summary()
        }
    
    def get_service_health(self, service: ServiceType) -> Dict[str, Any]:
        """Получение здоровья конкретного сервиса"""
        health_check = self.health_checker.check_service(service)
        
        return {
            'service': service.value,
            'status': health_check.status.value,
            'response_time': health_check.response_time,
            'error_message': health_check.error_message,
            'metadata': health_check.metadata,
            'timestamp': health_check.timestamp.isoformat(),
            'circuit_breaker': self.health_checker.circuit_breakers[service].get_state()
        }
    
    def force_recovery(self, service: ServiceType) -> bool:
        """Принудительное восстановление сервиса"""
        health_check = self.health_checker.check_service(service)
        return self.auto_recovery.attempt_recovery(service, health_check)
    
    def get_recovery_history(self) -> List[Dict[str, Any]]:
        """Получение истории восстановления"""
        return [
            {
                'service': item['service'],
                'timestamp': item['timestamp'].isoformat(),
                'success': item['success'],
                'recovery_time': item['recovery_time']
            }
            for item in self.auto_recovery.recovery_history
        ]
    
    def add_notification_channel(self, channel):
        """Добавление канала уведомлений"""
        self.alert_manager.notification_channels.append(channel)
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Получение детальной статистики"""
        return {
            'system_stats': self.system_stats,
            'alert_stats': self.alert_manager.get_alert_stats(),
            'metrics_summary': self.metrics_collector.get_metrics_summary(),
            'recovery_history': self.get_recovery_history(),
            'circuit_breakers': {
                service.value: breaker.get_state()
                for service, breaker in self.health_checker.circuit_breakers.items()
            }
        }

# Глобальный экземпляр идеальной системы отказоустойчивости
perfect_fault_tolerance_system = PerfectFaultToleranceSystem()

# Функции для совместимости с app.py
def init_fault_tolerance():
    """Инициализация системы отказоустойчивости"""
    global perfect_fault_tolerance_system
    perfect_fault_tolerance_system.start()
    return perfect_fault_tolerance_system

def shutdown_fault_tolerance():
    """Корректное завершение системы отказоустойчивости"""
    global perfect_fault_tolerance_system
    perfect_fault_tolerance_system.stop()