"""
Продвинутая система генерации контента
Включает современные ИИ-модели, персонализацию, SEO-оптимизацию и расширенные возможности
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
import random
from collections import defaultdict, Counter
import hashlib
import requests
from urllib.parse import urljoin

import openai
import anthropic
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from textstat import flesch_reading_ease, automated_readability_index

from models import Post, Category, Tag, Comment, User
from config.database import db
# Временные заглушки для несуществующих модулей
class ValidationResult:
    def __init__(self, is_valid=True, score=0.8, issues=None):
        self.is_valid = is_valid
        self.score = score
        self.issues = issues or []

def ai_content_validator(content, title):
    return ValidationResult(is_valid=True, score=0.85)

class EnhancedAIContentGenerator:
    def generate(self, *args, **kwargs):
        return {"content": "Generated content", "title": "Generated title"}

def track_ai_content_generation(content_type, status, metadata=None):
    pass
from services.monitoring import monitoring_system

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Типы контента"""
    HOW_TO_GUIDE = "how_to_guide"
    COMPARISON_REVIEW = "comparison_review"
    ANALYTICAL_ARTICLE = "analytical_article"
    NEWS_ARTICLE = "news_article"
    EXPERT_INTERVIEW = "expert_interview"
    CASE_STUDY = "case_study"
    LISTICLE = "listicle"
    TUTORIAL = "tutorial"
    OPINION_PIECE = "opinion_piece"
    RESEARCH_SUMMARY = "research_summary"

class ContentTone(Enum):
    """Тон контента"""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    AUTHORITATIVE = "authoritative"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    INSPIRATIONAL = "inspirational"
    CRITICAL = "critical"
    HUMOROUS = "humorous"

class TargetAudience(Enum):
    """Целевая аудитория"""
    BEGINNERS = "beginners"
    INTERMEDIATE = "intermediate"
    EXPERTS = "experts"
    GENERAL_PUBLIC = "general_public"
    PROFESSIONALS = "professionals"
    STUDENTS = "students"
    ENTREPRENEURS = "entrepreneurs"

@dataclass
class ContentRequest:
    """Запрос на генерацию контента"""
    topic: str
    content_type: ContentType
    tone: ContentTone
    target_audience: TargetAudience
    length: str  # "short", "medium", "long"
    keywords: List[str]
    exclude_keywords: List[str]
    include_images: bool = True
    include_quotes: bool = True
    include_statistics: bool = True
    include_examples: bool = True
    seo_optimized: bool = True
    personalized: bool = False
    user_preferences: Dict[str, Any] = None

@dataclass
class GeneratedContent:
    """Сгенерированный контент"""
    title: str
    content: str
    excerpt: str
    meta_description: str
    tags: List[str]
    category: str
    content_type: ContentType
    tone: ContentTone
    target_audience: TargetAudience
    word_count: int
    reading_time: int
    seo_score: float
    readability_score: float
    engagement_score: float
    quality_score: float
    images_suggestions: List[Dict[str, str]]
    internal_links: List[Dict[str, str]]
    external_links: List[Dict[str, str]]
    call_to_action: str
    social_media_posts: Dict[str, str]
    generated_at: datetime
    processing_time: float

class ModernAIIntegration:
    """Интеграция с современными ИИ-моделями"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.local_models = {}
        self.model_cache = {}
        self.init_ai_services()
    
    def init_ai_services(self):
        """Инициализация ИИ-сервисов"""
        try:
            # OpenAI GPT-4
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("✅ OpenAI GPT-4 инициализирован")
            
            # Anthropic Claude
            anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
            if anthropic_key:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("✅ Anthropic Claude инициализирован")
            
            # Локальные модели
            self._load_local_models()
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ИИ-сервисов: {e}")
    
    def _load_local_models(self):
        """Загрузка локальных моделей"""
        try:
            # Модель для генерации заголовков
            self.local_models['title_generator'] = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Модель для анализа тональности
            self.local_models['sentiment_analyzer'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Локальные модели загружены")
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить локальные модели: {e}")
    
    async def generate_with_gpt4(self, prompt: str, max_tokens: int = 2000, 
                               temperature: float = 0.7) -> str:
        """Генерация с помощью GPT-4"""
        if not self.openai_client:
            raise Exception("OpenAI клиент не инициализирован")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты эксперт по созданию качественного контента на русском языке."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Ошибка генерации с GPT-4: {e}")
            raise
    
    async def generate_with_claude(self, prompt: str, max_tokens: int = 2000) -> str:
        """Генерация с помощью Claude"""
        if not self.anthropic_client:
            raise Exception("Anthropic клиент не инициализирован")
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка генерации с Claude: {e}")
            raise
    
    def generate_title_variations(self, topic: str, content_type: ContentType) -> List[str]:
        """Генерация вариаций заголовков"""
        templates = {
            ContentType.HOW_TO_GUIDE: [
                "Как {topic}: пошаговое руководство",
                "Полное руководство по {topic}",
                "Как правильно {topic}: советы экспертов",
                "Изучаем {topic}: от А до Я"
            ],
            ContentType.COMPARISON_REVIEW: [
                "{topic}: сравнение и выбор лучшего",
                "Обзор {topic}: что выбрать?",
                "{topic}: подробное сравнение вариантов",
                "Лучшие {topic}: рейтинг и анализ"
            ],
            ContentType.ANALYTICAL_ARTICLE: [
                "Анализ {topic}: тенденции и прогнозы",
                "{topic}: глубокий анализ ситуации",
                "Что происходит с {topic}: анализ данных",
                "{topic}: исследование и выводы"
            ],
            ContentType.NEWS_ARTICLE: [
                "Новости {topic}: последние события",
                "{topic}: что изменилось?",
                "Актуальные новости о {topic}",
                "{topic}: свежие данные и факты"
            ],
            ContentType.LISTICLE: [
                "10 фактов о {topic}, которые вас удивят",
                "Топ-5 {topic} для начинающих",
                "7 способов {topic}: проверенные методы",
                "15 интересных фактов о {topic}"
            ]
        }
        
        title_templates = templates.get(content_type, [
            "Все о {topic}",
            "{topic}: полное руководство",
            "Изучаем {topic}",
            "{topic}: что нужно знать"
        ])
        
        titles = []
        for template in title_templates:
            title = template.format(topic=topic)
            titles.append(title)
            
            # Добавляем вариации
            variations = [
                f"{title}: подробный анализ",
                f"{title} в 2024 году",
                f"Экспертное мнение: {title.lower()}",
                f"{title} - полное руководство"
            ]
            titles.extend(variations)
        
        return titles[:10]  # Возвращаем топ-10

class ContentPersonalization:
    """Система персонализации контента"""
    
    def __init__(self):
        self.user_profiles = {}
        self.content_preferences = defaultdict(list)
        self.reading_history = defaultdict(list)
        self.engagement_metrics = defaultdict(dict)
    
    def analyze_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Анализ предпочтений пользователя"""
        # Получаем историю чтения пользователя
        user_posts = Post.query.join(Comment).filter(Comment.author_id == user_id).all()
        
        preferences = {
            'preferred_categories': Counter(),
            'preferred_topics': Counter(),
            'preferred_length': 'medium',
            'preferred_tone': ContentTone.CONVERSATIONAL,
            'preferred_content_types': Counter(),
            'reading_time_preference': 5,  # минут
            'engagement_level': 'medium'
        }
        
        for post in user_posts:
            if post.category:
                preferences['preferred_categories'][post.category.name] += 1
            
            # Анализируем теги
            for tag in post.tags:
                preferences['preferred_topics'][tag.name] += 1
            
            # Анализируем длину контента
            word_count = len(post.content.split())
            if word_count < 500:
                preferences['preferred_length'] = 'short'
            elif word_count > 2000:
                preferences['preferred_length'] = 'long'
        
        return preferences
    
    def personalize_content_request(self, request: ContentRequest, 
                                  user_preferences: Dict[str, Any]) -> ContentRequest:
        """Персонализация запроса на контент"""
        # Адаптируем тон под предпочтения пользователя
        if user_preferences.get('preferred_tone'):
            request.tone = user_preferences['preferred_tone']
        
        # Адаптируем длину
        if user_preferences.get('preferred_length'):
            request.length = user_preferences['preferred_length']
        
        # Добавляем предпочитаемые темы
        preferred_topics = user_preferences.get('preferred_topics', {})
        if preferred_topics:
            # Добавляем топ-3 предпочитаемые темы к ключевым словам
            top_topics = [topic for topic, count in preferred_topics.most_common(3)]
            request.keywords.extend(top_topics)
        
        return request
    
    def adapt_content_for_user(self, content: str, user_preferences: Dict[str, Any]) -> str:
        """Адаптация контента под пользователя"""
        adapted_content = content
        
        # Адаптируем сложность языка
        if user_preferences.get('engagement_level') == 'beginner':
            adapted_content = self._simplify_language(adapted_content)
        elif user_preferences.get('engagement_level') == 'expert':
            adapted_content = self._add_technical_details(adapted_content)
        
        # Адаптируем длину
        preferred_length = user_preferences.get('preferred_length', 'medium')
        if preferred_length == 'short':
            adapted_content = self._shorten_content(adapted_content)
        elif preferred_length == 'long':
            adapted_content = self._expand_content(adapted_content)
        
        return adapted_content
    
    def _simplify_language(self, content: str) -> str:
        """Упрощение языка"""
        # Заменяем сложные слова на простые
        simplifications = {
            'осуществлять': 'делать',
            'производить': 'создавать',
            'является': 'это',
            'представлять собой': 'быть',
            'иметь место': 'происходить',
            'носить характер': 'быть',
            'оказывать воздействие': 'влиять'
        }
        
        for complex_word, simple_word in simplifications.items():
            content = content.replace(complex_word, simple_word)
        
        return content
    
    def _add_technical_details(self, content: str) -> str:
        """Добавление технических деталей"""
        # Добавляем технические разделы
        technical_sections = [
            "\n\n## Технические детали\n\nДля специалистов важно отметить следующие аспекты:",
            "\n\n## Углубленный анализ\n\nС технической точки зрения можно выделить:",
            "\n\n## Экспертное мнение\n\nОпытные специалисты отмечают:"
        ]
        
        if random.random() < 0.3:  # 30% вероятность
            content += random.choice(technical_sections)
        
        return content
    
    def _shorten_content(self, content: str) -> str:
        """Сокращение контента"""
        # Берем только основные разделы
        sections = content.split('\n\n')
        if len(sections) > 4:
            # Оставляем введение, 2 основных раздела и заключение
            shortened = sections[:1] + sections[1:3] + sections[-1:]
            return '\n\n'.join(shortened)
        
        return content
    
    def _expand_content(self, content: str) -> str:
        """Расширение контента"""
        # Добавляем дополнительные разделы
        additional_sections = [
            "\n\n## Дополнительная информация\n\nДля более полного понимания темы стоит рассмотреть:",
            "\n\n## Практические советы\n\nВ практическом применении важно учитывать:",
            "\n\n## Часто задаваемые вопросы\n\nМногие читатели интересуются:"
        ]
        
        content += random.choice(additional_sections)
        return content

class SEOOptimizer:
    """SEO-оптимизатор контента"""
    
    def __init__(self):
        self.keyword_density_threshold = 0.02  # 2%
        self.max_keyword_density = 0.05  # 5%
        self.optimal_title_length = 60
        self.optimal_description_length = 160
        self.optimal_heading_structure = ['H1', 'H2', 'H3']
    
    def optimize_for_seo(self, content: str, title: str, keywords: List[str]) -> Dict[str, Any]:
        """SEO-оптимизация контента"""
        seo_analysis = {
            'title_score': self._analyze_title_seo(title, keywords),
            'content_score': self._analyze_content_seo(content, keywords),
            'structure_score': self._analyze_structure_seo(content),
            'keyword_density': self._calculate_keyword_density(content, keywords),
            'readability_score': flesch_reading_ease(content),
            'meta_score': self._analyze_meta_elements(content, title),
            'internal_linking_score': self._analyze_internal_links(content),
            'overall_seo_score': 0.0
        }
        
        # Вычисляем общий SEO-балл
        seo_analysis['overall_seo_score'] = (
            seo_analysis['title_score'] * 0.2 +
            seo_analysis['content_score'] * 0.3 +
            seo_analysis['structure_score'] * 0.2 +
            seo_analysis['meta_score'] * 0.15 +
            seo_analysis['internal_linking_score'] * 0.15
        )
        
        return seo_analysis
    
    def _analyze_title_seo(self, title: str, keywords: List[str]) -> float:
        """Анализ SEO заголовка"""
        score = 0.0
        
        # Длина заголовка
        if 30 <= len(title) <= self.optimal_title_length:
            score += 0.3
        elif len(title) > self.optimal_title_length:
            score += 0.1
        
        # Наличие ключевых слов
        title_lower = title.lower()
        for keyword in keywords:
            if keyword.lower() in title_lower:
                score += 0.3
                break
        
        # Позиция ключевого слова
        if keywords and keywords[0].lower() in title_lower[:20]:
            score += 0.2
        
        # Эмоциональные слова
        emotional_words = ['лучший', 'топ', 'полный', 'подробный', 'эксперт', 'проверенный']
        if any(word in title_lower for word in emotional_words):
            score += 0.2
        
        return min(1.0, score)
    
    def _analyze_content_seo(self, content: str, keywords: List[str]) -> float:
        """Анализ SEO контента"""
        score = 0.0
        content_lower = content.lower()
        
        # Плотность ключевых слов
        keyword_density = self._calculate_keyword_density(content, keywords)
        if 0.01 <= keyword_density <= 0.03:
            score += 0.4
        elif keyword_density > 0.03:
            score += 0.2
        
        # Длина контента
        word_count = len(content.split())
        if word_count >= 300:
            score += 0.3
        if word_count >= 1000:
            score += 0.2
        
        # Уникальность контента (упрощенная проверка)
        if len(set(content.split())) / word_count > 0.7:
            score += 0.1
        
        return min(1.0, score)
    
    def _analyze_structure_seo(self, content: str) -> float:
        """Анализ структуры для SEO"""
        score = 0.0
        
        # Наличие заголовков
        h1_count = len(re.findall(r'^#\s+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s+', content, re.MULTILINE))
        
        if h1_count == 1:
            score += 0.3
        if h2_count >= 2:
            score += 0.3
        if h3_count >= 1:
            score += 0.2
        
        # Наличие списков
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            score += 0.1
        
        # Наличие выделений
        if re.search(r'\*\*.*?\*\*', content):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_keyword_density(self, content: str, keywords: List[str]) -> float:
        """Вычисление плотности ключевых слов"""
        if not keywords:
            return 0.0
        
        content_lower = content.lower()
        total_words = len(content.split())
        
        keyword_count = 0
        for keyword in keywords:
            keyword_count += content_lower.count(keyword.lower())
        
        return keyword_count / total_words if total_words > 0 else 0.0
    
    def _analyze_meta_elements(self, content: str, title: str) -> float:
        """Анализ мета-элементов"""
        score = 0.0
        
        # Meta description (извлекаем из контента)
        sentences = content.split('.')
        meta_description = sentences[0][:self.optimal_description_length]
        
        if 120 <= len(meta_description) <= self.optimal_description_length:
            score += 0.5
        
        # Alt-текст для изображений (заглушка)
        if '![' in content:
            score += 0.3
        
        # Schema markup (заглушка)
        score += 0.2
        
        return min(1.0, score)
    
    def _analyze_internal_links(self, content: str) -> float:
        """Анализ внутренних ссылок"""
        score = 0.0
        
        # Подсчет ссылок
        link_count = len(re.findall(r'\[.*?\]\(.*?\)', content))
        
        if link_count >= 2:
            score += 0.5
        elif link_count >= 1:
            score += 0.3
        
        # Качество ссылок (заглушка)
        score += 0.5
        
        return min(1.0, score)
    
    def generate_meta_description(self, content: str, keywords: List[str]) -> str:
        """Генерация мета-описания"""
        # Берем первое предложение и оптимизируем
        sentences = content.split('.')
        first_sentence = sentences[0].strip()
        
        # Добавляем ключевые слова если их нет
        if keywords and keywords[0].lower() not in first_sentence.lower():
            first_sentence = f"{keywords[0]}: {first_sentence}"
        
        # Обрезаем до оптимальной длины
        if len(first_sentence) > self.optimal_description_length:
            first_sentence = first_sentence[:self.optimal_description_length-3] + "..."
        
        return first_sentence
    
    def suggest_internal_links(self, content: str, topic: str) -> List[Dict[str, str]]:
        """Предложение внутренних ссылок"""
        # Ищем релевантные посты в базе данных
        relevant_posts = Post.query.filter(
            Post.title.contains(topic) | Post.content.contains(topic)
        ).limit(5).all()
        
        links = []
        for post in relevant_posts:
            links.append({
                'title': post.title,
                'url': f'/post/{post.id}',
                'anchor_text': post.title[:50] + "..." if len(post.title) > 50 else post.title
            })
        
        return links

class AdvancedContentGenerator:
    """Продвинутый генератор контента"""
    
    def __init__(self):
        self.ai_integration = ModernAIIntegration()
        self.personalization = ContentPersonalization()
        self.seo_optimizer = SEOOptimizer()
        self.content_templates = self._load_content_templates()
        self.fact_checker = self._init_fact_checker()
        
        # Статистика генерации
        self.generation_stats = {
            'total_generated': 0,
            'by_content_type': defaultdict(int),
            'by_tone': defaultdict(int),
            'by_audience': defaultdict(int),
            'avg_quality_score': 0.0,
            'avg_seo_score': 0.0
        }
    
    def _load_content_templates(self) -> Dict[ContentType, Dict[str, Any]]:
        """Загрузка шаблонов контента"""
        return {
            ContentType.HOW_TO_GUIDE: {
                'structure': ['introduction', 'prerequisites', 'step_by_step', 'tips', 'conclusion'],
                'tone_keywords': ['пошагово', 'подробно', 'понятно', 'практично'],
                'min_words': 800,
                'max_words': 2000
            },
            ContentType.COMPARISON_REVIEW: {
                'structure': ['introduction', 'criteria', 'comparison', 'pros_cons', 'recommendation'],
                'tone_keywords': ['объективно', 'сравнительно', 'аналитично'],
                'min_words': 1000,
                'max_words': 2500
            },
            ContentType.ANALYTICAL_ARTICLE: {
                'structure': ['introduction', 'data_analysis', 'trends', 'implications', 'conclusion'],
                'tone_keywords': ['аналитично', 'объективно', 'научно'],
                'min_words': 1200,
                'max_words': 3000
            },
            ContentType.LISTICLE: {
                'structure': ['introduction', 'list_items', 'conclusion'],
                'tone_keywords': ['интересно', 'познавательно', 'увлекательно'],
                'min_words': 600,
                'max_words': 1500
            }
        }
    
    def _init_fact_checker(self):
        """Инициализация проверки фактов"""
        return {
            'wikipedia_api': 'https://ru.wikipedia.org/api/rest_v1/page/summary/',
            'news_api': 'https://newsapi.org/v2/everything',
            'cache': {}
        }
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Основная функция генерации контента"""
        start_time = time.time()
        
        try:
            # Персонализация запроса
            if request.personalized and request.user_preferences:
                request = self.personalization.personalize_content_request(
                    request, request.user_preferences
                )
            
            # Генерация заголовка
            title = await self._generate_title(request)
            
            # Генерация основного контента
            content = await self._generate_main_content(request, title)
            
            # Персонализация контента
            if request.personalized and request.user_preferences:
                content = self.personalization.adapt_content_for_user(
                    content, request.user_preferences
                )
            
            # SEO-оптимизация
            seo_analysis = self.seo_optimizer.optimize_for_seo(content, title, request.keywords)
            meta_description = self.seo_optimizer.generate_meta_description(content, request.keywords)
            
            # Генерация дополнительных элементов
            excerpt = self._generate_excerpt(content)
            tags = self._generate_tags(request.topic, request.keywords)
            internal_links = self.seo_optimizer.suggest_internal_links(content, request.topic)
            
            # Генерация изображений и социальных постов
            images_suggestions = await self._generate_image_suggestions(request.topic, content)
            social_posts = self._generate_social_media_posts(title, excerpt)
            
            # Вычисление метрик
            word_count = len(content.split())
            reading_time = max(1, word_count // 200)
            readability_score = flesch_reading_ease(content)
            
            # Создание результата
            result = GeneratedContent(
                title=title,
                content=content,
                excerpt=excerpt,
                meta_description=meta_description,
                tags=tags,
                category=request.topic,
                content_type=request.content_type,
                tone=request.tone,
                target_audience=request.target_audience,
                word_count=word_count,
                reading_time=reading_time,
                seo_score=seo_analysis['overall_seo_score'],
                readability_score=readability_score,
                engagement_score=self._calculate_engagement_score(content),
                quality_score=self._calculate_quality_score(content, seo_analysis),
                images_suggestions=images_suggestions,
                internal_links=internal_links,
                external_links=[],  # Заглушка
                call_to_action=self._generate_call_to_action(request),
                social_media_posts=social_posts,
                generated_at=datetime.now(),
                processing_time=time.time() - start_time
            )
            
            # Обновление статистики
            self._update_generation_stats(result)
            
            # Отслеживание метрик
            track_ai_content_generation(
                content, title, result.processing_time,
                result.processing_time * 0.4,  # generation_time
                result.processing_time * 0.3,  # validation_time
                result.processing_time * 0.3,  # correction_time
                True, request.topic
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка генерации контента: {e}")
            monitoring_system.error_tracker.record_error(e, {'function': 'generate_content'})
            raise
    
    async def _generate_title(self, request: ContentRequest) -> str:
        """Генерация заголовка"""
        title_variations = self.ai_integration.generate_title_variations(
            request.topic, request.content_type
        )
        
        # Выбираем лучший заголовок на основе SEO и привлекательности
        best_title = title_variations[0]
        best_score = 0.0
        
        for title in title_variations[:5]:
            seo_score = self.seo_optimizer._analyze_title_seo(title, request.keywords)
            attractiveness_score = self._calculate_title_attractiveness(title)
            total_score = seo_score * 0.6 + attractiveness_score * 0.4
            
            if total_score > best_score:
                best_score = total_score
                best_title = title
        
        return best_title
    
    async def _generate_main_content(self, request: ContentRequest, title: str) -> str:
        """Генерация основного контента"""
        template = self.content_templates.get(request.content_type, {})
        structure = template.get('structure', ['introduction', 'main_content', 'conclusion'])
        
        content_sections = []
        
        for section in structure:
            section_content = await self._generate_section_content(
                section, request, title
            )
            content_sections.append(section_content)
        
        return '\n\n'.join(content_sections)
    
    async def _generate_section_content(self, section: str, request: ContentRequest, 
                                      title: str) -> str:
        """Генерация содержимого секции"""
        prompts = {
            'introduction': f"Напиши введение для статьи '{title}' на тему '{request.topic}'. Тон: {request.tone.value}. Аудитория: {request.target_audience.value}. Включи ключевые слова: {', '.join(request.keywords[:3])}.",
            'main_content': f"Напиши основную часть статьи о '{request.topic}'. Тип контента: {request.content_type.value}. Включи практические примеры и статистику.",
            'conclusion': f"Напиши заключение для статьи о '{request.topic}'. Добавь призыв к действию и подведение итогов.",
            'step_by_step': f"Создай пошаговое руководство по '{request.topic}'. Сделай инструкции понятными для {request.target_audience.value}.",
            'comparison': f"Создай сравнительный анализ по теме '{request.topic}'. Объективно рассмотри разные варианты и подходы.",
            'tips': f"Дай практические советы по теме '{request.topic}'. Сделай советы полезными и применимыми."
        }
        
        prompt = prompts.get(section, f"Напиши раздел '{section}' для статьи о '{request.topic}'.")
        
        try:
            # Пробуем использовать GPT-4
            content = await self.ai_integration.generate_with_gpt4(prompt, max_tokens=800)
            return content
        except:
            # Fallback на локальную генерацию
            return self._generate_fallback_content(section, request)
    
    def _generate_fallback_content(self, section: str, request: ContentRequest) -> str:
        """Fallback генерация контента"""
        fallback_templates = {
            'introduction': f"В современном мире тема {request.topic} становится все более актуальной. В этой статье мы подробно рассмотрим все аспекты этой важной темы.",
            'main_content': f"Основные аспекты {request.topic} включают множество важных моментов. Давайте разберем их подробно.",
            'conclusion': f"Таким образом, {request.topic} представляет собой важную область для изучения и развития. Понимание основных принципов поможет в практическом применении."
        }
        
        return fallback_templates.get(section, f"Раздел о {request.topic}.")
    
    def _generate_excerpt(self, content: str) -> str:
        """Генерация краткого описания"""
        sentences = content.split('.')
        first_sentence = sentences[0].strip()
        
        if len(first_sentence) > 150:
            excerpt = first_sentence[:147] + "..."
        else:
            excerpt = first_sentence + "."
        
        return excerpt
    
    def _generate_tags(self, topic: str, keywords: List[str]) -> List[str]:
        """Генерация тегов"""
        base_tags = [topic] + keywords[:3]
        
        # Добавляем дополнительные теги
        additional_tags = [
            'полезно', 'интересно', 'практично', 'современно',
            'актуально', 'популярно', 'тренд', 'новинка'
        ]
        
        selected_additional = random.sample(additional_tags, 3)
        return base_tags + selected_additional
    
    async def _generate_image_suggestions(self, topic: str, content: str) -> List[Dict[str, str]]:
        """Генерация предложений изображений"""
        suggestions = []
        
        # Анализируем контент для поиска ключевых слов для изображений
        keywords = re.findall(r'\b\w{4,}\b', content.lower())
        keyword_counts = Counter(keywords)
        top_keywords = [word for word, count in keyword_counts.most_common(5)]
        
        for keyword in top_keywords[:3]:
            suggestions.append({
                'keyword': keyword,
                'description': f"Изображение, связанное с {keyword}",
                'alt_text': f"Иллюстрация {keyword}",
                'suggested_source': 'unsplash'
            })
        
        return suggestions
    
    def _generate_social_media_posts(self, title: str, excerpt: str) -> Dict[str, str]:
        """Генерация постов для социальных сетей"""
        return {
            'twitter': f"{title[:100]}{'...' if len(title) > 100 else ''}",
            'facebook': f"{title}\n\n{excerpt[:200]}{'...' if len(excerpt) > 200 else ''}",
            'linkedin': f"Новая статья: {title}\n\n{excerpt[:300]}{'...' if len(excerpt) > 300 else ''}",
            'telegram': f"📖 {title}\n\n{excerpt}"
        }
    
    def _generate_call_to_action(self, request: ContentRequest) -> str:
        """Генерация призыва к действию"""
        ctas = {
            ContentType.HOW_TO_GUIDE: "Попробуйте применить эти советы на практике и поделитесь результатами!",
            ContentType.COMPARISON_REVIEW: "Какой вариант вы бы выбрали? Поделитесь своим мнением в комментариях!",
            ContentType.ANALYTICAL_ARTICLE: "Что вы думаете об этих тенденциях? Обсудим в комментариях!",
            ContentType.LISTICLE: "Какие пункты вас больше всего заинтересовали? Расскажите в комментариях!"
        }
        
        return ctas.get(request.content_type, "Поделитесь своим мнением в комментариях!")
    
    def _calculate_title_attractiveness(self, title: str) -> float:
        """Вычисление привлекательности заголовка"""
        score = 0.0
        
        # Эмоциональные слова
        emotional_words = ['лучший', 'топ', 'секрет', 'проверенный', 'эффективный', 'удивительный']
        if any(word in title.lower() for word in emotional_words):
            score += 0.3
        
        # Числа в заголовке
        if re.search(r'\d+', title):
            score += 0.2
        
        # Вопросительные слова
        question_words = ['как', 'что', 'почему', 'когда', 'где']
        if any(word in title.lower() for word in question_words):
            score += 0.2
        
        # Длина заголовка
        if 30 <= len(title) <= 60:
            score += 0.3
        
        return min(1.0, score)
    
    def _calculate_engagement_score(self, content: str) -> float:
        """Вычисление оценки вовлеченности"""
        score = 0.0
        
        # Наличие вопросов
        question_count = content.count('?')
        if question_count > 0:
            score += min(0.3, question_count * 0.1)
        
        # Наличие списков
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            score += 0.2
        
        # Наличие выделений
        if re.search(r'\*\*.*?\*\*', content):
            score += 0.2
        
        # Длина контента (оптимальная)
        word_count = len(content.split())
        if 800 <= word_count <= 2000:
            score += 0.3
        
        return min(1.0, score)
    
    def _calculate_quality_score(self, content: str, seo_analysis: Dict[str, Any]) -> float:
        """Вычисление общей оценки качества"""
        readability_score = flesch_reading_ease(content) / 100
        seo_score = seo_analysis['overall_seo_score']
        engagement_score = self._calculate_engagement_score(content)
        
        return (readability_score * 0.4 + seo_score * 0.3 + engagement_score * 0.3)
    
    def _update_generation_stats(self, result: GeneratedContent):
        """Обновление статистики генерации"""
        self.generation_stats['total_generated'] += 1
        self.generation_stats['by_content_type'][result.content_type.value] += 1
        self.generation_stats['by_tone'][result.tone.value] += 1
        self.generation_stats['by_audience'][result.target_audience.value] += 1
        
        # Обновляем средние оценки
        total = self.generation_stats['total_generated']
        current_avg_quality = self.generation_stats['avg_quality_score']
        current_avg_seo = self.generation_stats['avg_seo_score']
        
        self.generation_stats['avg_quality_score'] = (
            (current_avg_quality * (total - 1) + result.quality_score) / total
        )
        self.generation_stats['avg_seo_score'] = (
            (current_avg_seo * (total - 1) + result.seo_score) / total
        )
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Получение статистики генерации"""
        return dict(self.generation_stats)

# Глобальный экземпляр
advanced_content_generator = AdvancedContentGenerator()

# Функции для удобного использования
async def generate_advanced_content(topic: str, content_type: str = "how_to_guide",
                                  tone: str = "conversational", 
                                  target_audience: str = "general_public",
                                  keywords: List[str] = None,
                                  personalized: bool = False,
                                  user_preferences: Dict[str, Any] = None) -> GeneratedContent:
    """Удобная функция для генерации контента"""
    
    request = ContentRequest(
        topic=topic,
        content_type=ContentType(content_type),
        tone=ContentTone(tone),
        target_audience=TargetAudience(target_audience),
        length="medium",
        keywords=keywords or [],
        exclude_keywords=[],
        personalized=personalized,
        user_preferences=user_preferences
    )
    
    return await advanced_content_generator.generate_content(request)

def get_advanced_generator_stats() -> Dict[str, Any]:
    """Получение статистики продвинутого генератора"""
    return advanced_content_generator.get_generation_statistics()