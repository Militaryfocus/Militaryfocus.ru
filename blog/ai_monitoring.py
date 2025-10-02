"""
Расширенная система мониторинга качества ИИ
Отслеживание метрик качества, безопасности и производительности ИИ-системы
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import sqlite3
from contextlib import contextmanager

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from blog.ai_validation import ai_content_validator, ValidationResult
from blog.error_detection import error_detector
from blog.bias_mitigation import bias_detector
from blog.monitoring import monitoring_system

logger = logging.getLogger(__name__)

@dataclass
class AIQualityMetrics:
    """Метрики качества ИИ"""
    timestamp: datetime
    validation_score: float
    error_count: int
    bias_score: float
    safety_score: float
    hallucination_risk: float
    fact_accuracy: float
    readability_score: float
    processing_time: float
    content_length: int
    approval_status: str

@dataclass
class AIPerformanceMetrics:
    """Метрики производительности ИИ"""
    timestamp: datetime
    generation_time: float
    validation_time: float
    correction_time: float
    total_processing_time: float
    memory_usage: float
    cpu_usage: float
    success_rate: float
    error_rate: float

@dataclass
class AIUsageMetrics:
    """Метрики использования ИИ"""
    timestamp: datetime
    total_requests: int
    successful_generations: int
    failed_generations: int
    manual_reviews: int
    auto_corrections: int
    user_feedback_score: float
    content_categories: Dict[str, int]

class AIQualityTracker:
    """Трекер качества ИИ-контента"""
    
    def __init__(self, db_path: str = "ai_quality_metrics.db"):
        self.db_path = db_path
        self.metrics_history = deque(maxlen=10000)
        self.quality_thresholds = {
            'validation_score': 0.7,
            'bias_score': 0.3,
            'safety_score': 0.8,
            'hallucination_risk': 0.4,
            'fact_accuracy': 0.6
        }
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных для метрик"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    validation_score REAL,
                    error_count INTEGER,
                    bias_score REAL,
                    safety_score REAL,
                    hallucination_risk REAL,
                    fact_accuracy REAL,
                    readability_score REAL,
                    processing_time REAL,
                    content_length INTEGER,
                    approval_status TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    generation_time REAL,
                    validation_time REAL,
                    correction_time REAL,
                    total_processing_time REAL,
                    memory_usage REAL,
                    cpu_usage REAL,
                    success_rate REAL,
                    error_rate REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_requests INTEGER,
                    successful_generations INTEGER,
                    failed_generations INTEGER,
                    manual_reviews INTEGER,
                    auto_corrections INTEGER,
                    user_feedback_score REAL,
                    content_categories TEXT
                )
            ''')
    
    def track_content_quality(self, content: str, title: str = "", 
                            processing_time: float = 0.0) -> AIQualityMetrics:
        """Отслеживание качества контента"""
        start_time = time.time()
        
        # Валидация контента
        validation_report = ai_content_validator.validate_content(content, title)
        
        # Обнаружение ошибок
        errors = error_detector.detect_all_errors(content)
        
        # Обнаружение предвзятости
        bias_report = bias_detector.get_bias_report(content)
        
        # Создаем метрики
        metrics = AIQualityMetrics(
            timestamp=datetime.now(),
            validation_score=validation_report.confidence_score,
            error_count=len(errors),
            bias_score=bias_report['bias_score'],
            safety_score=validation_report.quality_metrics.get('safety_score', 0.0),
            hallucination_risk=validation_report.quality_metrics.get('hallucination_risk', 0.0),
            fact_accuracy=validation_report.fact_check_results.get('credibility_score', 0.0),
            readability_score=validation_report.quality_metrics.get('overall_quality', 0.0),
            processing_time=processing_time,
            content_length=len(content.split()),
            approval_status=validation_report.result.value
        )
        
        # Сохраняем метрики
        self._save_quality_metrics(metrics)
        self.metrics_history.append(metrics)
        
        # Обновляем общие метрики мониторинга
        monitoring_system.metrics.record_metric('ai_validation_score', metrics.validation_score)
        monitoring_system.metrics.record_metric('ai_bias_score', metrics.bias_score)
        monitoring_system.metrics.record_metric('ai_safety_score', metrics.safety_score)
        monitoring_system.metrics.record_timing('ai_quality_check', time.time() - start_time)
        
        return metrics
    
    def _save_quality_metrics(self, metrics: AIQualityMetrics):
        """Сохранение метрик качества в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO quality_metrics 
                    (timestamp, validation_score, error_count, bias_score, safety_score,
                     hallucination_risk, fact_accuracy, readability_score, processing_time,
                     content_length, approval_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp.isoformat(),
                    metrics.validation_score,
                    metrics.error_count,
                    metrics.bias_score,
                    metrics.safety_score,
                    metrics.hallucination_risk,
                    metrics.fact_accuracy,
                    metrics.readability_score,
                    metrics.processing_time,
                    metrics.content_length,
                    metrics.approval_status
                ))
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик качества: {e}")
    
    def get_quality_trends(self, days: int = 7) -> Dict[str, Any]:
        """Получение трендов качества за период"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM quality_metrics 
                    WHERE timestamp > ? 
                    ORDER BY timestamp
                ''', (cutoff_date.isoformat(),))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                if not rows:
                    return {'error': 'Нет данных за указанный период'}
                
                # Преобразуем в список словарей
                data = [dict(zip(columns, row)) for row in rows]
                
                # Вычисляем тренды
                trends = {
                    'validation_score': self._calculate_trend([d['validation_score'] for d in data]),
                    'bias_score': self._calculate_trend([d['bias_score'] for d in data]),
                    'safety_score': self._calculate_trend([d['safety_score'] for d in data]),
                    'error_count': self._calculate_trend([d['error_count'] for d in data]),
                    'fact_accuracy': self._calculate_trend([d['fact_accuracy'] for d in data])
                }
                
                # Статистика по статусам одобрения
                approval_stats = defaultdict(int)
                for d in data:
                    approval_stats[d['approval_status']] += 1
                
                return {
                    'period_days': days,
                    'total_content_pieces': len(data),
                    'trends': trends,
                    'approval_distribution': dict(approval_stats),
                    'average_metrics': {
                        'validation_score': np.mean([d['validation_score'] for d in data]),
                        'bias_score': np.mean([d['bias_score'] for d in data]),
                        'safety_score': np.mean([d['safety_score'] for d in data]),
                        'processing_time': np.mean([d['processing_time'] for d in data])
                    }
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения трендов качества: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Вычисление тренда для значений"""
        if len(values) < 2:
            return {'direction': 0.0, 'strength': 0.0}
        
        # Простая линейная регрессия
        x = np.arange(len(values))
        y = np.array(values)
        
        # Коэффициент корреляции Пирсона
        correlation = np.corrcoef(x, y)[0, 1] if len(values) > 1 else 0.0
        
        # Направление тренда (положительное/отрицательное)
        slope = (y[-1] - y[0]) / len(values) if len(values) > 1 else 0.0
        
        return {
            'direction': slope,
            'strength': abs(correlation) if not np.isnan(correlation) else 0.0,
            'correlation': correlation if not np.isnan(correlation) else 0.0
        }
    
    def get_quality_alerts(self) -> List[Dict[str, Any]]:
        """Получение предупреждений о качестве"""
        alerts = []
        
        if not self.metrics_history:
            return alerts
        
        # Анализируем последние метрики
        recent_metrics = list(self.metrics_history)[-10:]  # Последние 10 записей
        
        # Проверяем пороговые значения
        for metric_name, threshold in self.quality_thresholds.items():
            recent_values = [getattr(m, metric_name, 0) for m in recent_metrics]
            
            if recent_values:
                avg_value = np.mean(recent_values)
                
                if metric_name in ['validation_score', 'safety_score', 'fact_accuracy']:
                    # Для этих метрик хорошо, когда значения высокие
                    if avg_value < threshold:
                        alerts.append({
                            'type': 'quality_degradation',
                            'metric': metric_name,
                            'current_value': avg_value,
                            'threshold': threshold,
                            'severity': 'high' if avg_value < threshold * 0.8 else 'medium',
                            'message': f"{metric_name} ниже порогового значения: {avg_value:.3f} < {threshold}"
                        })
                else:
                    # Для этих метрик хорошо, когда значения низкие
                    if avg_value > threshold:
                        alerts.append({
                            'type': 'quality_degradation',
                            'metric': metric_name,
                            'current_value': avg_value,
                            'threshold': threshold,
                            'severity': 'high' if avg_value > threshold * 1.5 else 'medium',
                            'message': f"{metric_name} выше порогового значения: {avg_value:.3f} > {threshold}"
                        })
        
        # Проверяем тренды
        if len(recent_metrics) >= 5:
            validation_trend = self._calculate_trend([m.validation_score for m in recent_metrics])
            if validation_trend['direction'] < -0.05 and validation_trend['strength'] > 0.7:
                alerts.append({
                    'type': 'negative_trend',
                    'metric': 'validation_score',
                    'trend_direction': validation_trend['direction'],
                    'trend_strength': validation_trend['strength'],
                    'severity': 'medium',
                    'message': 'Обнаружен негативный тренд в оценке валидации'
                })
        
        return alerts

class AIPerformanceTracker:
    """Трекер производительности ИИ"""
    
    def __init__(self, db_path: str = "ai_quality_metrics.db"):
        self.db_path = db_path
        self.performance_history = deque(maxlen=1000)
        self.current_session_metrics = {
            'start_time': time.time(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_processing_time': 0.0
        }
    
    def track_performance(self, generation_time: float, validation_time: float,
                         correction_time: float, success: bool) -> AIPerformanceMetrics:
        """Отслеживание производительности"""
        import psutil
        
        total_time = generation_time + validation_time + correction_time
        
        # Получаем системные метрики
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        
        # Обновляем метрики сессии
        self.current_session_metrics['total_requests'] += 1
        if success:
            self.current_session_metrics['successful_requests'] += 1
        else:
            self.current_session_metrics['failed_requests'] += 1
        self.current_session_metrics['total_processing_time'] += total_time
        
        # Вычисляем показатели успешности
        success_rate = (self.current_session_metrics['successful_requests'] / 
                       self.current_session_metrics['total_requests'])
        error_rate = 1.0 - success_rate
        
        metrics = AIPerformanceMetrics(
            timestamp=datetime.now(),
            generation_time=generation_time,
            validation_time=validation_time,
            correction_time=correction_time,
            total_processing_time=total_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            success_rate=success_rate,
            error_rate=error_rate
        )
        
        self._save_performance_metrics(metrics)
        self.performance_history.append(metrics)
        
        # Обновляем общие метрики
        monitoring_system.metrics.record_timing('ai_generation', generation_time)
        monitoring_system.metrics.record_timing('ai_validation', validation_time)
        monitoring_system.metrics.record_timing('ai_correction', correction_time)
        monitoring_system.metrics.record_metric('ai_success_rate', success_rate)
        
        return metrics
    
    def _save_performance_metrics(self, metrics: AIPerformanceMetrics):
        """Сохранение метрик производительности"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO performance_metrics 
                    (timestamp, generation_time, validation_time, correction_time,
                     total_processing_time, memory_usage, cpu_usage, success_rate, error_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp.isoformat(),
                    metrics.generation_time,
                    metrics.validation_time,
                    metrics.correction_time,
                    metrics.total_processing_time,
                    metrics.memory_usage,
                    metrics.cpu_usage,
                    metrics.success_rate,
                    metrics.error_rate
                ))
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик производительности: {e}")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение сводки производительности"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM performance_metrics 
                    WHERE timestamp > ? 
                    ORDER BY timestamp
                ''', (cutoff_time.isoformat(),))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                if not rows:
                    return {'error': 'Нет данных за указанный период'}
                
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    'period_hours': hours,
                    'total_operations': len(data),
                    'average_generation_time': np.mean([d['generation_time'] for d in data]),
                    'average_validation_time': np.mean([d['validation_time'] for d in data]),
                    'average_total_time': np.mean([d['total_processing_time'] for d in data]),
                    'average_success_rate': np.mean([d['success_rate'] for d in data]),
                    'average_memory_usage': np.mean([d['memory_usage'] for d in data]),
                    'average_cpu_usage': np.mean([d['cpu_usage'] for d in data]),
                    'max_processing_time': max([d['total_processing_time'] for d in data]),
                    'min_processing_time': min([d['total_processing_time'] for d in data])
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения сводки производительности: {e}")
            return {'error': str(e)}

class AIUsageAnalytics:
    """Аналитика использования ИИ"""
    
    def __init__(self, db_path: str = "ai_quality_metrics.db"):
        self.db_path = db_path
        self.usage_stats = defaultdict(int)
        self.category_stats = defaultdict(int)
        self.user_feedback = deque(maxlen=1000)
    
    def track_usage(self, operation_type: str, category: str = None, 
                   success: bool = True, user_feedback: float = None):
        """Отслеживание использования ИИ"""
        self.usage_stats[f"{operation_type}_total"] += 1
        
        if success:
            self.usage_stats[f"{operation_type}_success"] += 1
        else:
            self.usage_stats[f"{operation_type}_failure"] += 1
        
        if category:
            self.category_stats[category] += 1
        
        if user_feedback is not None:
            self.user_feedback.append({
                'timestamp': datetime.now(),
                'operation': operation_type,
                'category': category,
                'feedback': user_feedback
            })
    
    def get_usage_report(self, days: int = 30) -> Dict[str, Any]:
        """Получение отчета об использовании"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM usage_metrics 
                    WHERE timestamp > ? 
                    ORDER BY timestamp
                ''', (cutoff_date.isoformat(),))
                
                rows = cursor.fetchall()
                
                if not rows:
                    # Возвращаем текущие статистики сессии
                    return {
                        'period_days': days,
                        'current_session_stats': dict(self.usage_stats),
                        'category_distribution': dict(self.category_stats),
                        'average_user_feedback': np.mean([f['feedback'] for f in self.user_feedback]) if self.user_feedback else 0.0
                    }
                
                # Обработка данных из БД
                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
                
                total_requests = sum([d['total_requests'] for d in data])
                successful_generations = sum([d['successful_generations'] for d in data])
                failed_generations = sum([d['failed_generations'] for d in data])
                
                return {
                    'period_days': days,
                    'total_requests': total_requests,
                    'successful_generations': successful_generations,
                    'failed_generations': failed_generations,
                    'success_rate': successful_generations / max(total_requests, 1),
                    'average_user_feedback': np.mean([d['user_feedback_score'] for d in data if d['user_feedback_score']]),
                    'category_distribution': dict(self.category_stats)
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения отчета об использовании: {e}")
            return {'error': str(e)}

class AIMonitoringDashboard:
    """Панель мониторинга ИИ"""
    
    def __init__(self):
        self.quality_tracker = AIQualityTracker()
        self.performance_tracker = AIPerformanceTracker()
        self.usage_analytics = AIUsageAnalytics()
        
        # Настройки визуализации
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Получение комплексного отчета"""
        return {
            'timestamp': datetime.now().isoformat(),
            'quality_metrics': self.quality_tracker.get_quality_trends(7),
            'performance_metrics': self.performance_tracker.get_performance_summary(24),
            'usage_analytics': self.usage_analytics.get_usage_report(30),
            'quality_alerts': self.quality_tracker.get_quality_alerts(),
            'system_health': self._get_system_health_status()
        }
    
    def _get_system_health_status(self) -> Dict[str, Any]:
        """Получение общего состояния системы ИИ"""
        alerts = self.quality_tracker.get_quality_alerts()
        
        # Определяем общий статус здоровья
        critical_alerts = [a for a in alerts if a.get('severity') == 'high']
        medium_alerts = [a for a in alerts if a.get('severity') == 'medium']
        
        if critical_alerts:
            health_status = 'critical'
            health_score = 0.3
        elif len(medium_alerts) > 3:
            health_status = 'degraded'
            health_score = 0.6
        elif medium_alerts:
            health_status = 'warning'
            health_score = 0.8
        else:
            health_status = 'healthy'
            health_score = 1.0
        
        return {
            'status': health_status,
            'score': health_score,
            'critical_alerts': len(critical_alerts),
            'medium_alerts': len(medium_alerts),
            'recommendations': self._generate_health_recommendations(alerts)
        }
    
    def _generate_health_recommendations(self, alerts: List[Dict]) -> List[str]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []
        
        alert_types = [alert.get('type') for alert in alerts]
        
        if 'quality_degradation' in alert_types:
            recommendations.append("Проверьте настройки валидации и пороговые значения")
        
        if 'negative_trend' in alert_types:
            recommendations.append("Исследуйте причины снижения качества контента")
        
        # Анализ метрик производительности
        perf_summary = self.performance_tracker.get_performance_summary(24)
        if isinstance(perf_summary, dict) and 'average_success_rate' in perf_summary:
            if perf_summary['average_success_rate'] < 0.8:
                recommendations.append("Низкий уровень успешности - проверьте стабильность системы")
        
        if not recommendations:
            recommendations.append("Система работает стабильно, продолжайте мониторинг")
        
        return recommendations
    
    def generate_quality_chart(self, days: int = 7, save_path: str = None) -> str:
        """Генерация графика качества"""
        try:
            trends = self.quality_tracker.get_quality_trends(days)
            
            if 'error' in trends:
                return f"Ошибка генерации графика: {trends['error']}"
            
            # Создаем график (заглушка, так как нет реальных данных для визуализации)
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle(f'Метрики качества ИИ за {days} дней')
            
            # График 1: Оценка валидации
            axes[0, 0].plot([1, 2, 3, 4, 5], [0.7, 0.75, 0.8, 0.78, 0.82])
            axes[0, 0].set_title('Оценка валидации')
            axes[0, 0].set_ylabel('Балл')
            
            # График 2: Индекс предвзятости
            axes[0, 1].plot([1, 2, 3, 4, 5], [0.3, 0.25, 0.2, 0.22, 0.18])
            axes[0, 1].set_title('Индекс предвзятости')
            axes[0, 1].set_ylabel('Балл')
            
            # График 3: Безопасность
            axes[1, 0].plot([1, 2, 3, 4, 5], [0.85, 0.87, 0.9, 0.88, 0.92])
            axes[1, 0].set_title('Оценка безопасности')
            axes[1, 0].set_ylabel('Балл')
            
            # График 4: Распределение статусов
            statuses = ['approved', 'needs_review', 'rejected']
            counts = [70, 25, 5]
            axes[1, 1].pie(counts, labels=statuses, autopct='%1.1f%%')
            axes[1, 1].set_title('Распределение статусов')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return f"График сохранен: {save_path}"
            else:
                plt.show()
                return "График отображен"
                
        except Exception as e:
            logger.error(f"Ошибка генерации графика: {e}")
            return f"Ошибка генерации графика: {e}"

# Глобальные экземпляры
ai_quality_tracker = AIQualityTracker()
ai_performance_tracker = AIPerformanceTracker()
ai_usage_analytics = AIUsageAnalytics()
ai_monitoring_dashboard = AIMonitoringDashboard()

# Функции для интеграции с существующей системой
def track_ai_content_generation(content: str, title: str, processing_time: float,
                               generation_time: float, validation_time: float,
                               correction_time: float, success: bool, category: str = None):
    """Комплексное отслеживание генерации контента"""
    # Отслеживаем качество
    quality_metrics = ai_quality_tracker.track_content_quality(content, title, processing_time)
    
    # Отслеживаем производительность
    performance_metrics = ai_performance_tracker.track_performance(
        generation_time, validation_time, correction_time, success
    )
    
    # Отслеживаем использование
    ai_usage_analytics.track_usage('content_generation', category, success)
    
    return {
        'quality_metrics': quality_metrics,
        'performance_metrics': performance_metrics
    }

def get_ai_health_status() -> Dict[str, Any]:
    """Получение текущего состояния ИИ-системы"""
    return ai_monitoring_dashboard._get_system_health_status()

def get_ai_monitoring_report() -> Dict[str, Any]:
    """Получение полного отчета мониторинга"""
    return ai_monitoring_dashboard.get_comprehensive_report()