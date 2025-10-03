"""
Интегрированная система ИИ с защитными механизмами
Объединяет все компоненты для создания безопасного и качественного ИИ-контента
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from blog.ai_validation import ai_content_validator, ValidationResult
from blog.enhanced_ai_content import EnhancedAIContentGenerator
from blog.error_detection import error_detector
from blog.bias_mitigation import bias_detector
from blog.ai_monitoring import track_ai_content_generation, ai_monitoring_dashboard
from blog.fault_tolerance import ai_circuit_breaker, safe_db_operation
from blog.monitoring import monitoring_system

logger = logging.getLogger(__name__)

class ContentStatus(Enum):
    """Статус контента"""
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    NEEDS_CORRECTION = "needs_correction"
    PUBLISHED = "published"

@dataclass
class ContentGenerationResult:
    """Результат генерации контента"""
    content: str
    title: str
    excerpt: str
    category: str
    tags: List[str]
    status: ContentStatus
    quality_score: float
    safety_score: float
    bias_score: float
    error_count: int
    processing_time: float
    validation_report: Any
    corrections_applied: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

class SafeAIContentGenerator:
    """Безопасный генератор ИИ-контента с полной защитой"""
    
    def __init__(self):
        self.base_generator = EnhancedAIContentGenerator()
        
        # Настройки безопасности
        self.safety_config = {
            'min_quality_score': 0.7,
            'max_bias_score': 0.3,
            'min_safety_score': 0.8,
            'max_error_count': 5,
            'max_hallucination_risk': 0.4,
            'auto_correction_enabled': True,
            'manual_review_threshold': 0.6
        }
        
        # Статистика работы
        self.generation_stats = {
            'total_attempts': 0,
            'successful_generations': 0,
            'auto_corrections': 0,
            'manual_reviews': 0,
            'rejections': 0
        }
    
    @ai_circuit_breaker
    def generate_safe_content(self, category: str = None, topic: str = None,
                            max_attempts: int = 3) -> Optional[ContentGenerationResult]:
        """Генерация безопасного контента с полной проверкой"""
        start_time = time.time()
        generation_start = time.time()
        
        self.generation_stats['total_attempts'] += 1
        
        try:
            # Этап 1: Базовая генерация контента
            logger.info(f"🤖 Начинаем генерацию контента: категория={category}, тема={topic}")
            
            base_content = self.base_generator.generate_validated_post(category, topic, max_attempts)
            if not base_content:
                logger.error("❌ Не удалось сгенерировать базовый контент")
                return None
            
            generation_time = time.time() - generation_start
            validation_start = time.time()
            
            # Этап 2: Комплексная валидация
            logger.info("🔍 Проводим комплексную валидацию контента")
            validation_report = ai_content_validator.validate_content(
                base_content['content'], 
                base_content['title'], 
                base_content['category']
            )
            
            validation_time = time.time() - validation_start
            correction_start = time.time()
            
            # Этап 3: Обнаружение и исправление ошибок
            logger.info("🔧 Обнаруживаем и исправляем ошибки")
            errors = error_detector.detect_all_errors(base_content['content'])
            
            # Автоматическое исправление ошибок
            corrected_content = base_content['content']
            applied_corrections = []
            
            if self.safety_config['auto_correction_enabled'] and errors:
                corrected_content, corrections = error_detector.auto_correct_text(
                    base_content['content'], min_confidence=0.8
                )
                applied_corrections.extend([f"Исправлена ошибка: {c.description}" for c in corrections])
                self.generation_stats['auto_corrections'] += len(corrections)
            
            # Этап 4: Обнаружение и устранение предвзятости
            logger.info("⚖️ Проверяем и устраняем предвзятость")
            bias_report = bias_detector.get_bias_report(corrected_content)
            
            if bias_report['bias_score'] > self.safety_config['max_bias_score']:
                # Пытаемся автоматически исправить предвзятость
                bias_corrected_content, bias_corrections = bias_detector.auto_correct_bias(
                    corrected_content, min_confidence=0.7
                )
                if bias_corrections:
                    corrected_content = bias_corrected_content
                    applied_corrections.extend([f"Устранена предвзятость: {c.description}" for c in bias_corrections])
            
            correction_time = time.time() - correction_start
            
            # Этап 5: Финальная оценка качества
            logger.info("📊 Проводим финальную оценку качества")
            final_validation = ai_content_validator.validate_content(
                corrected_content, base_content['title'], base_content['category']
            )
            
            # Определяем статус контента
            status = self._determine_content_status(
                final_validation, errors, bias_report, applied_corrections
            )
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(
                final_validation, errors, bias_report, applied_corrections
            )
            
            # Создаем результат
            result = ContentGenerationResult(
                content=corrected_content,
                title=base_content['title'],
                excerpt=base_content['excerpt'],
                category=base_content['category'],
                tags=base_content['tags'],
                status=status,
                quality_score=final_validation.confidence_score,
                safety_score=final_validation.quality_metrics.get('safety_score', 0.0),
                bias_score=bias_report['bias_score'],
                error_count=len(errors),
                processing_time=time.time() - start_time,
                validation_report=final_validation,
                corrections_applied=applied_corrections,
                recommendations=recommendations,
                metadata={
                    'generation_time': generation_time,
                    'validation_time': validation_time,
                    'correction_time': correction_time,
                    'original_content_length': len(base_content['content']),
                    'final_content_length': len(corrected_content),
                    'auto_corrections_count': len(applied_corrections)
                }
            )
            
            # Обновляем статистику
            if status == ContentStatus.APPROVED:
                self.generation_stats['successful_generations'] += 1
            elif status in [ContentStatus.NEEDS_REVIEW, ContentStatus.NEEDS_CORRECTION]:
                self.generation_stats['manual_reviews'] += 1
            else:
                self.generation_stats['rejections'] += 1
            
            # Отслеживаем метрики
            track_ai_content_generation(
                corrected_content, base_content['title'], result.processing_time,
                generation_time, validation_time, correction_time,
                status == ContentStatus.APPROVED, base_content['category']
            )
            
            logger.info(f"✅ Контент сгенерирован: статус={status.value}, качество={result.quality_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации безопасного контента: {e}")
            monitoring_system.error_tracker.record_error(e, {'function': 'generate_safe_content'})
            return None
    
    def _determine_content_status(self, validation_report, errors, bias_report, 
                                corrections) -> ContentStatus:
        """Определение статуса контента на основе всех проверок"""
        
        # Критические проблемы безопасности
        if validation_report.quality_metrics.get('safety_score', 0) < self.safety_config['min_safety_score']:
            return ContentStatus.REJECTED
        
        # Слишком много ошибок
        if len(errors) > self.safety_config['max_error_count']:
            return ContentStatus.NEEDS_CORRECTION
        
        # Высокий уровень предвзятости
        if bias_report['bias_score'] > self.safety_config['max_bias_score']:
            return ContentStatus.NEEDS_CORRECTION
        
        # Низкое качество
        if validation_report.confidence_score < self.safety_config['min_quality_score']:
            return ContentStatus.NEEDS_CORRECTION
        
        # Требует ручной проверки
        if (validation_report.confidence_score < self.safety_config['manual_review_threshold'] or
            len(corrections) > 3 or
            validation_report.result == ValidationResult.NEEDS_REVIEW):
            return ContentStatus.NEEDS_REVIEW
        
        # Одобрено
        return ContentStatus.APPROVED
    
    def _generate_recommendations(self, validation_report, errors, bias_report, 
                                corrections) -> List[str]:
        """Генерация рекомендаций по улучшению контента"""
        recommendations = []
        
        # Рекомендации по качеству
        if validation_report.confidence_score < 0.8:
            recommendations.append("Рекомендуется улучшить общее качество контента")
        
        # Рекомендации по ошибкам
        if errors:
            error_types = set(error.error_type.value for error in errors)
            if 'spelling' in error_types:
                recommendations.append("Проверьте орфографию")
            if 'grammar' in error_types:
                recommendations.append("Исправьте грамматические ошибки")
            if 'logical' in error_types:
                recommendations.append("Устраните логические противоречия")
        
        # Рекомендации по предвзятости
        if bias_report['bias_score'] > 0.2:
            recommendations.extend(bias_report.get('recommendations', []))
        
        # Рекомендации по исправлениям
        if len(corrections) > 2:
            recommendations.append("Много автоматических исправлений - рекомендуется ручная проверка")
        
        # Общие рекомендации
        if validation_report.suggestions:
            recommendations.extend(validation_report.suggestions[:3])  # Первые 3 предложения
        
        return recommendations[:5]  # Ограничиваем количество рекомендаций
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Получение статистики генерации"""
        total = self.generation_stats['total_attempts']
        
        if total == 0:
            return self.generation_stats
        
        return {
            **self.generation_stats,
            'success_rate': self.generation_stats['successful_generations'] / total,
            'correction_rate': self.generation_stats['auto_corrections'] / total,
            'review_rate': self.generation_stats['manual_reviews'] / total,
            'rejection_rate': self.generation_stats['rejections'] / total
        }
    
    def update_safety_config(self, new_config: Dict[str, Any]):
        """Обновление конфигурации безопасности"""
        self.safety_config.update(new_config)
        logger.info(f"Конфигурация безопасности обновлена: {new_config}")

class ContentModerationSystem:
    """Система модерации контента"""
    
    def __init__(self):
        self.moderation_queue = []
        self.approved_content = []
        self.rejected_content = []
        
        # Автоматические правила модерации
        self.auto_moderation_rules = {
            'min_quality_threshold': 0.8,
            'max_bias_threshold': 0.2,
            'max_error_threshold': 2,
            'auto_approve_enabled': True,
            'auto_reject_enabled': True
        }
    
    def moderate_content(self, content_result: ContentGenerationResult) -> ContentStatus:
        """Модерация контента"""
        
        # Автоматическое одобрение
        if (self.auto_moderation_rules['auto_approve_enabled'] and
            content_result.quality_score >= self.auto_moderation_rules['min_quality_threshold'] and
            content_result.bias_score <= self.auto_moderation_rules['max_bias_threshold'] and
            content_result.error_count <= self.auto_moderation_rules['max_error_threshold']):
            
            content_result.status = ContentStatus.APPROVED
            self.approved_content.append(content_result)
            logger.info(f"✅ Контент автоматически одобрен: {content_result.title}")
            return ContentStatus.APPROVED
        
        # Автоматическое отклонение
        if (self.auto_moderation_rules['auto_reject_enabled'] and
            (content_result.safety_score < 0.6 or
             content_result.bias_score > 0.6 or
             content_result.error_count > 10)):
            
            content_result.status = ContentStatus.REJECTED
            self.rejected_content.append(content_result)
            logger.info(f"❌ Контент автоматически отклонен: {content_result.title}")
            return ContentStatus.REJECTED
        
        # Добавляем в очередь на ручную модерацию
        content_result.status = ContentStatus.NEEDS_REVIEW
        self.moderation_queue.append(content_result)
        logger.info(f"👁️ Контент добавлен в очередь модерации: {content_result.title}")
        return ContentStatus.NEEDS_REVIEW
    
    def get_moderation_queue(self) -> List[ContentGenerationResult]:
        """Получение очереди модерации"""
        return self.moderation_queue.copy()
    
    def approve_content(self, content_id: int) -> bool:
        """Одобрение контента из очереди"""
        if 0 <= content_id < len(self.moderation_queue):
            content = self.moderation_queue.pop(content_id)
            content.status = ContentStatus.APPROVED
            self.approved_content.append(content)
            logger.info(f"✅ Контент одобрен модератором: {content.title}")
            return True
        return False
    
    def reject_content(self, content_id: int, reason: str = "") -> bool:
        """Отклонение контента из очереди"""
        if 0 <= content_id < len(self.moderation_queue):
            content = self.moderation_queue.pop(content_id)
            content.status = ContentStatus.REJECTED
            content.metadata['rejection_reason'] = reason
            self.rejected_content.append(content)
            logger.info(f"❌ Контент отклонен модератором: {content.title} (причина: {reason})")
            return True
        return False
    
    def get_moderation_stats(self) -> Dict[str, Any]:
        """Получение статистики модерации"""
        return {
            'queue_size': len(self.moderation_queue),
            'approved_count': len(self.approved_content),
            'rejected_count': len(self.rejected_content),
            'total_moderated': len(self.approved_content) + len(self.rejected_content),
            'approval_rate': len(self.approved_content) / max(1, len(self.approved_content) + len(self.rejected_content))
        }

class IntegratedAISystem:
    """Интегрированная система ИИ"""
    
    def __init__(self):
        self.content_generator = SafeAIContentGenerator()
        self.moderation_system = ContentModerationSystem()
        
        # Настройки системы
        self.system_config = {
            'auto_publish_enabled': False,
            'batch_generation_enabled': True,
            'max_concurrent_generations': 3,
            'quality_improvement_enabled': True
        }
    
    def generate_and_moderate_content(self, category: str = None, topic: str = None) -> Optional[ContentGenerationResult]:
        """Полный цикл генерации и модерации контента"""
        
        # Генерируем контент
        content_result = self.content_generator.generate_safe_content(category, topic)
        
        if not content_result:
            return None
        
        # Модерируем контент
        final_status = self.moderation_system.moderate_content(content_result)
        content_result.status = final_status
        
        # Автоматическая публикация (если включена)
        if (self.system_config['auto_publish_enabled'] and 
            final_status == ContentStatus.APPROVED):
            self._auto_publish_content(content_result)
        
        return content_result
    
    def _auto_publish_content(self, content_result: ContentGenerationResult):
        """Автоматическая публикация одобренного контента"""
        try:
            with safe_db_operation():
                # Здесь должна быть логика сохранения в базу данных
                # Используем существующую логику из enhanced_ai_content
                from blog.enhanced_ai_content import enhanced_scheduler
                
                post_data = {
                    'title': content_result.title,
                    'content': content_result.content,
                    'excerpt': content_result.excerpt,
                    'category': content_result.category,
                    'tags': content_result.tags,
                    'validation_report': content_result.validation_report,
                    'generated_at': datetime.now()
                }
                
                success = enhanced_scheduler._create_post_in_db(post_data)
                
                if success:
                    content_result.status = ContentStatus.PUBLISHED
                    logger.info(f"📰 Контент автоматически опубликован: {content_result.title}")
                else:
                    logger.error(f"❌ Ошибка автоматической публикации: {content_result.title}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка автоматической публикации: {e}")
    
    def batch_generate_content(self, count: int, categories: List[str] = None) -> List[ContentGenerationResult]:
        """Пакетная генерация контента"""
        results = []
        
        logger.info(f"🚀 Начинаем пакетную генерацию {count} единиц контента")
        
        for i in range(count):
            category = categories[i % len(categories)] if categories else None
            
            try:
                result = self.generate_and_moderate_content(category)
                if result:
                    results.append(result)
                    logger.info(f"✅ Сгенерирован контент {i+1}/{count}: {result.title}")
                else:
                    logger.warning(f"⚠️ Не удалось сгенерировать контент {i+1}/{count}")
                
                # Небольшая пауза между генерациями
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Ошибка генерации контента {i+1}/{count}: {e}")
        
        logger.info(f"🏁 Пакетная генерация завершена: {len(results)}/{count} успешно")
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            'timestamp': datetime.now().isoformat(),
            'generator_stats': self.content_generator.get_generation_statistics(),
            'moderation_stats': self.moderation_system.get_moderation_stats(),
            'ai_health': ai_monitoring_dashboard._get_system_health_status(),
            'system_config': self.system_config,
            'recommendations': self._get_system_recommendations()
        }
    
    def _get_system_recommendations(self) -> List[str]:
        """Получение рекомендаций по системе"""
        recommendations = []
        
        gen_stats = self.content_generator.get_generation_statistics()
        mod_stats = self.moderation_system.get_moderation_stats()
        
        if gen_stats.get('success_rate', 0) < 0.7:
            recommendations.append("Низкий уровень успешности генерации - проверьте настройки")
        
        if gen_stats.get('rejection_rate', 0) > 0.3:
            recommendations.append("Высокий уровень отклонений - пересмотрите критерии качества")
        
        if mod_stats.get('queue_size', 0) > 10:
            recommendations.append("Большая очередь модерации - рассмотрите автоматизацию")
        
        if not recommendations:
            recommendations.append("Система работает стабильно")
        
        return recommendations
    
    def optimize_system_parameters(self):
        """Автоматическая оптимизация параметров системы"""
        logger.info("🔧 Начинаем оптимизацию параметров системы")
        
        gen_stats = self.content_generator.get_generation_statistics()
        
        # Адаптивная настройка порогов качества
        if gen_stats.get('rejection_rate', 0) > 0.4:
            # Слишком много отклонений - снижаем требования
            current_threshold = self.content_generator.safety_config['min_quality_score']
            new_threshold = max(0.6, current_threshold - 0.05)
            self.content_generator.update_safety_config({'min_quality_score': new_threshold})
            logger.info(f"📉 Снижен порог качества: {current_threshold} → {new_threshold}")
        
        elif gen_stats.get('success_rate', 0) > 0.9:
            # Слишком высокий успех - можно повысить требования
            current_threshold = self.content_generator.safety_config['min_quality_score']
            new_threshold = min(0.9, current_threshold + 0.05)
            self.content_generator.update_safety_config({'min_quality_score': new_threshold})
            logger.info(f"📈 Повышен порог качества: {current_threshold} → {new_threshold}")
        
        logger.info("✅ Оптимизация параметров завершена")

# Глобальный экземпляр интегрированной системы
integrated_ai_system = IntegratedAISystem()

# Функции для удобного использования
def generate_safe_content(category: str = None, topic: str = None) -> Optional[ContentGenerationResult]:
    """Генерация безопасного контента"""
    return integrated_ai_system.generate_and_moderate_content(category, topic)

def batch_generate_safe_content(count: int, categories: List[str] = None) -> List[ContentGenerationResult]:
    """Пакетная генерация безопасного контента"""
    return integrated_ai_system.batch_generate_content(count, categories)

def get_ai_system_status() -> Dict[str, Any]:
    """Получение статуса ИИ-системы"""
    return integrated_ai_system.get_system_status()

def optimize_ai_system():
    """Оптимизация ИИ-системы"""
    return integrated_ai_system.optimize_system_parameters()