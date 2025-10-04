"""
Интегрированная система управления контентом
Объединяет все компоненты: генерацию, персонализацию, SEO, валидацию и мониторинг
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path

from blog.models_perfect import Post, Category, Tag, Comment, User, View
from blog import db
from blog.advanced_content_generator import (
    AdvancedContentGenerator, ContentRequest, ContentType, ContentTone, 
    TargetAudience, GeneratedContent, generate_advanced_content
)
from blog.ai_provider_manager import (
    AIProviderManager, AIProvider, ModelConfig, ModelType, 
    generate_with_ai, get_ai_provider_stats
)
from blog.content_personalization import (
    ContentPersonalizer, PersonalizedContentGenerator, UserBehaviorAnalyzer,
    generate_personalized_content, get_personalized_recommendations, get_user_insights
)
from blog.seo_optimization import (
    KeywordResearch, ContentSEOAnalyzer, ContentSEOOptimizer,
    research_keywords, analyze_content_seo, optimize_content_seo,
    generate_seo_title, generate_seo_meta_description
)
from blog.ai_validation import ai_content_validator, ValidationResult
from blog.enhanced_ai_content import EnhancedAIContentGenerator
from blog.ai_monitoring import track_ai_content_generation, ai_monitoring_dashboard
from blog.monitoring import monitoring_system

logger = logging.getLogger(__name__)

class ContentWorkflow(Enum):
    """Рабочие процессы контента"""
    MANUAL_CREATION = "manual_creation"
    AI_GENERATION = "ai_generation"
    PERSONALIZED_GENERATION = "personalized_generation"
    SEO_OPTIMIZED_GENERATION = "seo_optimized_generation"
    BATCH_GENERATION = "batch_generation"
    SCHEDULED_GENERATION = "scheduled_generation"

class ContentStatus(Enum):
    """Статус контента"""
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATED = "validated"
    OPTIMIZED = "optimized"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"

@dataclass
class ContentCreationRequest:
    """Запрос на создание контента"""
    topic: str
    content_type: str = "how_to_guide"
    tone: str = "conversational"
    target_audience: str = "general_public"
    length: str = "medium"
    keywords: List[str] = None
    exclude_keywords: List[str] = None
    workflow: ContentWorkflow = ContentWorkflow.AI_GENERATION
    user_id: Optional[int] = None
    category_id: Optional[int] = None
    seo_optimized: bool = True
    personalized: bool = False
    include_images: bool = True
    include_quotes: bool = True
    include_statistics: bool = True
    include_examples: bool = True
    scheduled_publish: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class ContentCreationResult:
    """Результат создания контента"""
    post_id: int
    title: str
    content: str
    excerpt: str
    meta_description: str
    tags: List[str]
    category: str
    status: ContentStatus
    workflow: ContentWorkflow
    quality_score: float
    seo_score: float
    personalization_score: float
    validation_report: Any
    seo_analysis: Any
    personalization_data: Any
    processing_time: float
    created_at: datetime
    metadata: Dict[str, Any]

class IntegratedContentManager:
    """Интегрированный менеджер контента"""
    
    def __init__(self):
        self.advanced_generator = AdvancedContentGenerator()
        self.ai_provider_manager = AIProviderManager()
        self.personalizer = ContentPersonalizer()
        self.personalized_generator = PersonalizedContentGenerator()
        self.keyword_research = KeywordResearch()
        self.seo_analyzer = ContentSEOAnalyzer()
        self.seo_optimizer = ContentSEOOptimizer()
        self.enhanced_generator = EnhancedAIContentGenerator()
        
        # Статистика работы
        self.creation_stats = {
            'total_created': 0,
            'by_workflow': {},
            'by_status': {},
            'avg_quality_score': 0.0,
            'avg_seo_score': 0.0,
            'avg_processing_time': 0.0
        }
        
        # Очередь задач
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
    
    async def create_content(self, request: ContentCreationRequest) -> ContentCreationResult:
        """Создание контента с полным циклом обработки"""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Начинаем создание контента: {request.topic} (workflow: {request.workflow.value})")
            
            # Этап 1: Исследование ключевых слов
            if request.seo_optimized and not request.keywords:
                keywords_analysis = self.keyword_research.research_keywords(request.topic)
                request.keywords = [kw.keyword for kw in keywords_analysis[:5]]
                logger.info(f"Найдены ключевые слова: {request.keywords}")
            
            # Этап 2: Генерация контента
            generated_content = await self._generate_content(request)
            
            # Этап 3: Валидация контента
            validation_report = ai_content_validator.validate_content(
                generated_content.content, 
                generated_content.title, 
                generated_content.category
            )
            
            # Этап 4: SEO анализ и оптимизация
            seo_analysis = None
            if request.seo_optimized:
                seo_analysis = self.seo_analyzer.analyze_content_seo(
                    generated_content.content, 
                    generated_content.title, 
                    "", 
                    request.keywords or []
                )
                
                # Оптимизируем контент если нужно
                if seo_analysis.overall_seo_score < 0.7:
                    optimization_result = await self.seo_optimizer.optimize_content(
                        generated_content.content, 
                        generated_content.title, 
                        request.keywords or []
                    )
                    generated_content.content = optimization_result.optimized_content
                    logger.info("Контент оптимизирован для SEO")
            
            # Этап 5: Персонализация (если требуется)
            personalization_data = None
            if request.personalized and request.user_id:
                personalized_content = self.personalizer.personalize_content(
                    generated_content.content, 
                    request.user_id
                )
                generated_content.content = personalized_content
                personalization_data = self.personalized_generator.get_user_insights(request.user_id)
                logger.info("Контент персонализирован")
            
            # Этап 6: Создание поста в базе данных
            post = await self._create_post_in_database(
                generated_content, request, validation_report, seo_analysis, personalization_data
            )
            
            # Этап 7: Определение статуса
            status = self._determine_content_status(validation_report, seo_analysis)
            
            # Создаем результат
            result = ContentCreationResult(
                post_id=post.id,
                title=generated_content.title,
                content=generated_content.content,
                excerpt=generated_content.excerpt,
                meta_description=generated_content.meta_description,
                tags=generated_content.tags,
                category=generated_content.category,
                status=status,
                workflow=request.workflow,
                quality_score=generated_content.quality_score,
                seo_score=seo_analysis.overall_seo_score if seo_analysis else 0.0,
                personalization_score=personalization_data.get('engagement_level', 'medium') if personalization_data else 'medium',
                validation_report=validation_report,
                seo_analysis=seo_analysis,
                personalization_data=personalization_data,
                processing_time=time.time() - start_time,
                created_at=datetime.now(),
                metadata=request.metadata or {}
            )
            
            # Обновляем статистику
            self._update_creation_stats(result)
            
            # Отслеживаем метрики
            track_ai_content_generation(
                generated_content.content, 
                generated_content.title, 
                result.processing_time,
                result.processing_time * 0.4,  # generation_time
                result.processing_time * 0.3,  # validation_time
                result.processing_time * 0.3,  # correction_time
                status == ContentStatus.APPROVED, 
                generated_content.category
            )
            
            logger.info(f"Контент успешно создан: ID={post.id}, статус={status.value}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка создания контента: {e}")
            monitoring_system.error_tracker.record_error(e, {'function': 'create_content', 'task_id': task_id})
            raise
    
    async def _generate_content(self, request: ContentCreationRequest) -> GeneratedContent:
        """Генерация контента в зависимости от рабочего процесса"""
        
        if request.workflow == ContentWorkflow.AI_GENERATION:
            # Используем продвинутый генератор
            content_request = ContentRequest(
                topic=request.topic,
                content_type=ContentType(request.content_type),
                tone=ContentTone(request.tone),
                target_audience=TargetAudience(request.target_audience),
                length=request.length,
                keywords=request.keywords or [],
                exclude_keywords=request.exclude_keywords or [],
                include_images=request.include_images,
                include_quotes=request.include_quotes,
                include_statistics=request.include_statistics,
                include_examples=request.include_examples,
                seo_optimized=request.seo_optimized,
                personalized=request.personalized,
                user_preferences=None
            )
            
            return await self.advanced_generator.generate_content(content_request)
        
        elif request.workflow == ContentWorkflow.PERSONALIZED_GENERATION:
            # Персонализированная генерация
            if request.user_id:
                content = await generate_personalized_content(request.topic, request.user_id)
                
                # Создаем объект GeneratedContent
                return GeneratedContent(
                    title=f"{request.topic}: персонализированное руководство",
                    content=content,
                    excerpt=content[:150] + "...",
                    meta_description=content[:160] + "...",
                    tags=request.keywords or [request.topic],
                    category=request.topic,
                    content_type=ContentType(request.content_type),
                    tone=ContentTone(request.tone),
                    target_audience=TargetAudience(request.target_audience),
                    word_count=len(content.split()),
                    reading_time=max(1, len(content.split()) // 200),
                    seo_score=0.0,
                    readability_score=0.0,
                    engagement_score=0.0,
                    quality_score=0.0,
                    images_suggestions=[],
                    internal_links=[],
                    external_links=[],
                    call_to_action="Поделитесь своим мнением в комментариях!",
                    social_media_posts={},
                    generated_at=datetime.now(),
                    processing_time=0.0
                )
            else:
                raise ValueError("user_id требуется для персонализированной генерации")
        
        elif request.workflow == ContentWorkflow.SEO_OPTIMIZED_GENERATION:
            # SEO-оптимизированная генерация
            if not request.keywords:
                keywords_analysis = self.keyword_research.research_keywords(request.topic)
                request.keywords = [kw.keyword for kw in keywords_analysis[:3]]
            
            # Генерируем SEO-оптимизированный заголовок
            seo_title = await generate_seo_title(request.topic, request.keywords)
            
            # Генерируем контент
            content_request = ContentRequest(
                topic=request.topic,
                content_type=ContentType(request.content_type),
                tone=ContentTone(request.tone),
                target_audience=TargetAudience(request.target_audience),
                length=request.length,
                keywords=request.keywords,
                exclude_keywords=request.exclude_keywords or [],
                include_images=request.include_images,
                include_quotes=request.include_quotes,
                include_statistics=request.include_statistics,
                include_examples=request.include_examples,
                seo_optimized=True,
                personalized=False,
                user_preferences=None
            )
            
            generated_content = await self.advanced_generator.generate_content(content_request)
            generated_content.title = seo_title
            
            # Генерируем SEO мета-описание
            generated_content.meta_description = await generate_seo_meta_description(
                generated_content.content, request.keywords
            )
            
            return generated_content
        
        else:
            # Fallback на базовую генерацию
            return await self.enhanced_generator.generate_validated_post(request.topic)
    
    async def _create_post_in_database(self, generated_content: GeneratedContent, 
                                     request: ContentCreationRequest,
                                     validation_report: Any, seo_analysis: Any,
                                     personalization_data: Any) -> Post:
        """Создание поста в базе данных"""
        
        # Получаем или создаем категорию
        category = None
        if request.category_id:
            category = Category.query.get(request.category_id)
        elif generated_content.category:
            category = Category.query.filter_by(name=generated_content.category).first()
            if not category:
                category = Category(
                    name=generated_content.category,
                    description=f"Статьи о {generated_content.category}"
                )
                db.session.add(category)
                db.session.flush()
        
        # Получаем автора
        author = None
        if request.user_id:
            author = User.query.get(request.user_id)
        
        if not author:
            # Используем первого админа
            author = User.query.filter_by(is_admin=True).first()
        
        if not author:
            raise ValueError("Не найден автор для создания поста")
        
        # Создаем пост
        post = Post(
            title=generated_content.title,
            content=generated_content.content,
            excerpt=generated_content.excerpt,
            category_id=category.id if category else None,
            author_id=author.id,
            is_published=request.scheduled_publish is None,
            published_at=request.scheduled_publish or datetime.utcnow()
        )
        
        db.session.add(post)
        db.session.flush()
        
        # Добавляем теги
        for tag_name in generated_content.tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
                db.session.flush()
            post.tags.append(tag)
        
        # Сохраняем метаданные
        metadata = {
            'workflow': request.workflow.value,
            'quality_score': generated_content.quality_score,
            'seo_score': generated_content.seo_score,
            'readability_score': generated_content.readability_score,
            'engagement_score': generated_content.engagement_score,
            'word_count': generated_content.word_count,
            'reading_time': generated_content.reading_time,
            'generated_at': generated_content.generated_at.isoformat(),
            'processing_time': generated_content.processing_time,
            'validation_result': validation_report.result.value if validation_report else None,
            'seo_analysis': asdict(seo_analysis) if seo_analysis else None,
            'personalization_data': personalization_data,
            'ai_generated': True
        }
        
        post.meta_data = json.dumps(metadata)
        
        db.session.commit()
        return post
    
    def _determine_content_status(self, validation_report: Any, seo_analysis: Any) -> ContentStatus:
        """Определение статуса контента"""
        
        if validation_report and validation_report.result == ValidationResult.REJECTED:
            return ContentStatus.REJECTED
        
        if validation_report and validation_report.result == ValidationResult.NEEDS_REVIEW:
            return ContentStatus.VALIDATED
        
        if seo_analysis and seo_analysis.overall_seo_score < 0.5:
            return ContentStatus.VALIDATED
        
        if validation_report and validation_report.result == ValidationResult.APPROVED:
            return ContentStatus.APPROVED
        
        return ContentStatus.GENERATED
    
    def _update_creation_stats(self, result: ContentCreationResult):
        """Обновление статистики создания"""
        self.creation_stats['total_created'] += 1
        
        # Статистика по рабочим процессам
        workflow = result.workflow.value
        if workflow not in self.creation_stats['by_workflow']:
            self.creation_stats['by_workflow'][workflow] = 0
        self.creation_stats['by_workflow'][workflow] += 1
        
        # Статистика по статусам
        status = result.status.value
        if status not in self.creation_stats['by_status']:
            self.creation_stats['by_status'][status] = 0
        self.creation_stats['by_status'][status] += 1
        
        # Обновляем средние значения
        total = self.creation_stats['total_created']
        
        current_avg_quality = self.creation_stats['avg_quality_score']
        self.creation_stats['avg_quality_score'] = (
            (current_avg_quality * (total - 1) + result.quality_score) / total
        )
        
        current_avg_seo = self.creation_stats['avg_seo_score']
        self.creation_stats['avg_seo_score'] = (
            (current_avg_seo * (total - 1) + result.seo_score) / total
        )
        
        current_avg_time = self.creation_stats['avg_processing_time']
        self.creation_stats['avg_processing_time'] = (
            (current_avg_time * (total - 1) + result.processing_time) / total
        )
    
    async def batch_create_content(self, requests: List[ContentCreationRequest]) -> List[ContentCreationResult]:
        """Пакетное создание контента"""
        results = []
        
        logger.info(f"Начинаем пакетное создание {len(requests)} единиц контента")
        
        for i, request in enumerate(requests):
            try:
                result = await self.create_content(request)
                results.append(result)
                logger.info(f"Создан контент {i+1}/{len(requests)}: {result.title}")
                
                # Небольшая пауза между созданиями
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка создания контента {i+1}/{len(requests)}: {e}")
        
        logger.info(f"Пакетное создание завершено: {len(results)}/{len(requests)} успешно")
        return results
    
    async def schedule_content_creation(self, request: ContentCreationRequest, 
                                      schedule_time: datetime) -> str:
        """Планирование создания контента"""
        task_id = str(uuid.uuid4())
        
        # Добавляем задачу в очередь
        await self.task_queue.put({
            'task_id': task_id,
            'request': request,
            'schedule_time': schedule_time,
            'created_at': datetime.now()
        })
        
        logger.info(f"Задача создания контента запланирована: {task_id} на {schedule_time}")
        return task_id
    
    def get_creation_statistics(self) -> Dict[str, Any]:
        """Получение статистики создания контента"""
        return dict(self.creation_stats)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            'timestamp': datetime.now().isoformat(),
            'creation_stats': self.get_creation_statistics(),
            'ai_provider_stats': get_ai_provider_stats(),
            'monitoring_status': ai_monitoring_dashboard._get_system_health_status(),
            'queue_size': self.task_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'components_status': {
                'advanced_generator': 'active',
                'ai_provider_manager': 'active',
                'personalizer': 'active',
                'seo_optimizer': 'active',
                'validation_system': 'active'
            }
        }
    
    async def optimize_content(self, post_id: int, optimization_type: str = "seo") -> Dict[str, Any]:
        """Оптимизация существующего контента"""
        
        post = Post.query.get(post_id)
        if not post:
            raise ValueError(f"Пост с ID {post_id} не найден")
        
        if optimization_type == "seo":
            # SEO оптимизация
            keywords = [tag.name for tag in post.tags]
            optimization_result = await self.seo_optimizer.optimize_content(
                post.content, post.title, keywords
            )
            
            # Обновляем пост
            post.content = optimization_result.optimized_content
            db.session.commit()
            
            return {
                'optimization_type': 'seo',
                'changes_made': optimization_result.changes_made,
                'seo_improvements': optimization_result.seo_improvements,
                'optimized_content': optimization_result.optimized_content
            }
        
        elif optimization_type == "personalization":
            # Персонализация для всех пользователей
            # Здесь можно добавить логику персонализации
            return {
                'optimization_type': 'personalization',
                'message': 'Персонализация будет применена при просмотре пользователями'
            }
        
        else:
            raise ValueError(f"Неподдерживаемый тип оптимизации: {optimization_type}")
    
    def get_content_recommendations(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение рекомендаций контента для пользователя"""
        
        recommendations = get_personalized_recommendations(user_id, limit)
        
        return [
            {
                'post_id': rec.post_id,
                'title': rec.title,
                'excerpt': rec.excerpt,
                'category': rec.category,
                'score': rec.score,
                'reasons': rec.reasons,
                'personalized_aspects': rec.personalized_aspects
            }
            for rec in recommendations
        ]
    
    def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Получение аналитики пользователя"""
        
        insights = get_user_insights(user_id)
        
        # Добавляем дополнительную аналитику
        user_posts = Post.query.filter_by(author_id=user_id).all()
        user_views = View.query.filter_by(user_id=user_id).count()
        user_comments = Comment.query.filter_by(author_id=user_id).count()
        
        return {
            **insights,
            'posts_created': len(user_posts),
            'total_views': user_views,
            'comments_made': user_comments,
            'engagement_rate': user_views / max(len(user_posts), 1),
            'content_preferences': insights.get('content_preferences', {}),
            'reading_patterns': {
                'preferred_time': insights.get('time_preferences', {}),
                'average_session': insights.get('average_session_duration', 0),
                'reading_speed': insights.get('reading_speed', 200)
            }
        }

# Глобальный экземпляр
integrated_content_manager = IntegratedContentManager()

# Удобные функции для использования
async def create_content(topic: str, content_type: str = "how_to_guide",
                        tone: str = "conversational", target_audience: str = "general_public",
                        keywords: List[str] = None, user_id: int = None,
                        seo_optimized: bool = True, personalized: bool = False) -> ContentCreationResult:
    """Удобная функция для создания контента"""
    
    request = ContentCreationRequest(
        topic=topic,
        content_type=content_type,
        tone=tone,
        target_audience=target_audience,
        keywords=keywords,
        user_id=user_id,
        seo_optimized=seo_optimized,
        personalized=personalized,
        workflow=ContentWorkflow.PERSONALIZED_GENERATION if personalized else ContentWorkflow.AI_GENERATION
    )
    
    return await integrated_content_manager.create_content(request)

async def batch_create_content(requests: List[ContentCreationRequest]) -> List[ContentCreationResult]:
    """Пакетное создание контента"""
    return await integrated_content_manager.batch_create_content(requests)

def get_content_manager_stats() -> Dict[str, Any]:
    """Получение статистики менеджера контента"""
    return integrated_content_manager.get_creation_statistics()

def get_system_status() -> Dict[str, Any]:
    """Получение статуса системы"""
    return integrated_content_manager.get_system_status()

async def optimize_existing_content(post_id: int, optimization_type: str = "seo") -> Dict[str, Any]:
    """Оптимизация существующего контента"""
    return await integrated_content_manager.optimize_content(post_id, optimization_type)

def get_user_content_recommendations(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Получение рекомендаций контента для пользователя"""
    return integrated_content_manager.get_content_recommendations(user_id, limit)

def get_user_analytics(user_id: int) -> Dict[str, Any]:
    """Получение аналитики пользователя"""
    return integrated_content_manager.get_user_analytics(user_id)