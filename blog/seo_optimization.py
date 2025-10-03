"""
Расширенная система SEO-оптимизации
Включает анализ ключевых слов, оптимизацию контента, техническое SEO и аналитику
"""

import os
import json
import time
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
import hashlib
from urllib.parse import urljoin, urlparse
from collections import defaultdict, Counter
import sqlite3
from contextlib import contextmanager

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from textstat import flesch_reading_ease, automated_readability_index

from blog.models import Post, Category, Tag, Comment, User
from blog import db
from blog.ai_provider_manager import generate_with_ai

logger = logging.getLogger(__name__)

class SEOElement(Enum):
    """SEO элементы"""
    TITLE = "title"
    META_DESCRIPTION = "meta_description"
    HEADINGS = "headings"
    CONTENT = "content"
    IMAGES = "images"
    LINKS = "links"
    URL = "url"
    SCHEMA = "schema"

class KeywordDifficulty(Enum):
    """Сложность ключевых слов"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"

@dataclass
class KeywordAnalysis:
    """Анализ ключевого слова"""
    keyword: str
    search_volume: int
    difficulty: KeywordDifficulty
    cpc: float  # Cost per click
    competition: float
    trend: str  # rising, stable, falling
    related_keywords: List[str]
    long_tail_variations: List[str]

@dataclass
class SEOAnalysis:
    """SEO анализ контента"""
    url: str
    title_score: float
    meta_description_score: float
    content_score: float
    structure_score: float
    keyword_density_score: float
    readability_score: float
    internal_linking_score: float
    external_linking_score: float
    image_optimization_score: float
    technical_seo_score: float
    overall_seo_score: float
    recommendations: List[str]
    issues: List[str]
    keyword_analysis: Dict[str, KeywordAnalysis]
    competitor_analysis: Dict[str, Any]

@dataclass
class ContentOptimization:
    """Оптимизация контента"""
    original_content: str
    optimized_content: str
    changes_made: List[str]
    seo_improvements: List[str]
    readability_improvements: List[str]
    keyword_optimizations: List[str]

class KeywordResearch:
    """Исследование ключевых слов"""
    
    def __init__(self):
        self.api_keys = {
            'google_trends': os.environ.get('GOOGLE_TRENDS_API_KEY'),
            'semrush': os.environ.get('SEMRUSH_API_KEY'),
            'ahrefs': os.environ.get('AHREFS_API_KEY'),
            'moz': os.environ.get('MOZ_API_KEY')
        }
        self.keyword_cache = {}
        self.cache_ttl = 3600  # 1 час
    
    def research_keywords(self, topic: str, language: str = 'ru') -> List[KeywordAnalysis]:
        """Исследование ключевых слов для темы"""
        
        # Проверяем кэш
        cache_key = f"{topic}_{language}"
        if cache_key in self.keyword_cache:
            cached_data, timestamp = self.keyword_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        keywords = []
        
        # Генерируем базовые ключевые слова
        base_keywords = self._generate_base_keywords(topic)
        
        # Исследуем каждое ключевое слово
        for keyword in base_keywords:
            analysis = self._analyze_keyword(keyword, language)
            if analysis:
                keywords.append(analysis)
        
        # Добавляем длинные хвосты
        long_tail_keywords = self._generate_long_tail_keywords(topic, keywords)
        for keyword in long_tail_keywords:
            analysis = self._analyze_keyword(keyword, language)
            if analysis:
                keywords.append(analysis)
        
        # Сортируем по релевантности
        keywords.sort(key=lambda x: x.search_volume * (1 - x.competition), reverse=True)
        
        # Кэшируем результат
        self.keyword_cache[cache_key] = (keywords, time.time())
        
        return keywords[:20]  # Возвращаем топ-20
    
    def _generate_base_keywords(self, topic: str) -> List[str]:
        """Генерация базовых ключевых слов"""
        keywords = [topic]
        
        # Добавляем вариации
        variations = [
            f"как {topic}",
            f"что такое {topic}",
            f"{topic} для начинающих",
            f"{topic} руководство",
            f"{topic} советы",
            f"{topic} примеры",
            f"{topic} лучший",
            f"{topic} обзор",
            f"{topic} сравнение",
            f"{topic} цена"
        ]
        
        keywords.extend(variations)
        
        # Добавляем синонимы (упрощенная версия)
        synonyms = self._get_synonyms(topic)
        keywords.extend(synonyms)
        
        return keywords
    
    def _generate_long_tail_keywords(self, topic: str, base_keywords: List[KeywordAnalysis]) -> List[str]:
        """Генерация длинных хвостовых ключевых слов"""
        long_tail = []
        
        # Используем базовые ключевые слова для генерации длинных хвостов
        for keyword_analysis in base_keywords[:5]:
            keyword = keyword_analysis.keyword
            
            # Добавляем модификаторы
            modifiers = [
                "как правильно",
                "лучший способ",
                "пошаговое руководство",
                "для новичков",
                "профессиональный",
                "бесплатно",
                "2024",
                "обзор",
                "сравнение",
                "отзывы"
            ]
            
            for modifier in modifiers:
                long_tail.append(f"{modifier} {keyword}")
        
        return long_tail
    
    def _get_synonyms(self, word: str) -> List[str]:
        """Получение синонимов (упрощенная версия)"""
        # В реальной реализации здесь был бы API синонимов или словарь
        synonym_dict = {
            'технология': ['технологии', 'технологический', 'IT', 'информационные технологии'],
            'обучение': ['изучение', 'образование', 'курс', 'тренинг'],
            'разработка': ['создание', 'программирование', 'кодирование'],
            'бизнес': ['предпринимательство', 'коммерция', 'дело'],
            'здоровье': ['медицина', 'здоровый образ жизни', 'фитнес']
        }
        
        return synonym_dict.get(word.lower(), [])
    
    def _analyze_keyword(self, keyword: str, language: str) -> Optional[KeywordAnalysis]:
        """Анализ отдельного ключевого слова"""
        
        # Симуляция анализа ключевого слова
        # В реальной реализации здесь были бы API от Google Keyword Planner, SEMrush и т.д.
        
        # Генерируем случайные данные для демонстрации
        search_volume = np.random.randint(100, 10000)
        difficulty_score = np.random.uniform(0, 1)
        
        if difficulty_score < 0.3:
            difficulty = KeywordDifficulty.EASY
        elif difficulty_score < 0.6:
            difficulty = KeywordDifficulty.MEDIUM
        elif difficulty_score < 0.8:
            difficulty = KeywordDifficulty.HARD
        else:
            difficulty = KeywordDifficulty.VERY_HARD
        
        cpc = np.random.uniform(0.1, 5.0)
        competition = difficulty_score
        
        # Определяем тренд
        trend_options = ['rising', 'stable', 'falling']
        trend = np.random.choice(trend_options, p=[0.3, 0.5, 0.2])
        
        # Генерируем связанные ключевые слова
        related_keywords = self._generate_related_keywords(keyword)
        
        # Генерируем длинные хвосты
        long_tail_variations = self._generate_long_tail_variations(keyword)
        
        return KeywordAnalysis(
            keyword=keyword,
            search_volume=search_volume,
            difficulty=difficulty,
            cpc=cpc,
            competition=competition,
            trend=trend,
            related_keywords=related_keywords,
            long_tail_variations=long_tail_variations
        )
    
    def _generate_related_keywords(self, keyword: str) -> List[str]:
        """Генерация связанных ключевых слов"""
        # Упрощенная генерация связанных ключевых слов
        related = []
        
        # Добавляем вариации с разными окончаниями
        if keyword.endswith('ие'):
            related.append(keyword[:-2] + 'ия')
        elif keyword.endswith('ая'):
            related.append(keyword[:-2] + 'ое')
        
        # Добавляем прилагательные
        related.extend([
            f"{keyword}ный",
            f"{keyword}ский",
            f"{keyword}овой"
        ])
        
        return related[:5]
    
    def _generate_long_tail_variations(self, keyword: str) -> List[str]:
        """Генерация длинных хвостовых вариаций"""
        variations = [
            f"как {keyword} работает",
            f"что такое {keyword} простыми словами",
            f"{keyword} для чайников",
            f"лучший {keyword} 2024",
            f"{keyword} отзывы и обзоры"
        ]
        
        return variations

class ContentSEOAnalyzer:
    """SEO анализатор контента"""
    
    def __init__(self):
        self.keyword_research = KeywordResearch()
        self.stop_words = set(stopwords.words('russian'))
        self.seo_rules = self._load_seo_rules()
    
    def _load_seo_rules(self) -> Dict[str, Any]:
        """Загрузка SEO правил"""
        return {
            'title': {
                'min_length': 30,
                'max_length': 60,
                'keyword_position': 'beginning',
                'required_elements': ['keyword']
            },
            'meta_description': {
                'min_length': 120,
                'max_length': 160,
                'keyword_position': 'beginning',
                'required_elements': ['keyword', 'call_to_action']
            },
            'content': {
                'min_word_count': 300,
                'optimal_word_count': 1000,
                'max_keyword_density': 0.03,
                'min_keyword_density': 0.01,
                'required_elements': ['headings', 'lists', 'images']
            },
            'headings': {
                'h1_count': 1,
                'h2_min_count': 2,
                'keyword_in_headings': True
            },
            'images': {
                'alt_text_required': True,
                'file_size_optimal': 100,  # KB
                'dimensions_optimal': (1200, 630)
            }
        }
    
    def analyze_content_seo(self, content: str, title: str, url: str = "", 
                           target_keywords: List[str] = None) -> SEOAnalysis:
        """Комплексный SEO анализ контента"""
        
        if not target_keywords:
            target_keywords = self._extract_keywords_from_content(content)
        
        # Анализируем различные SEO элементы
        title_score = self._analyze_title_seo(title, target_keywords)
        meta_description_score = self._analyze_meta_description_seo(content, target_keywords)
        content_score = self._analyze_content_seo(content, target_keywords)
        structure_score = self._analyze_structure_seo(content, target_keywords)
        keyword_density_score = self._analyze_keyword_density(content, target_keywords)
        readability_score = self._analyze_readability_seo(content)
        internal_linking_score = self._analyze_internal_linking(content)
        external_linking_score = self._analyze_external_linking(content)
        image_optimization_score = self._analyze_image_optimization(content)
        technical_seo_score = self._analyze_technical_seo(url, content)
        
        # Вычисляем общий SEO балл
        overall_seo_score = (
            title_score * 0.15 +
            meta_description_score * 0.10 +
            content_score * 0.25 +
            structure_score * 0.15 +
            keyword_density_score * 0.10 +
            readability_score * 0.10 +
            internal_linking_score * 0.05 +
            external_linking_score * 0.05 +
            image_optimization_score * 0.03 +
            technical_seo_score * 0.02
        )
        
        # Генерируем рекомендации
        recommendations = self._generate_seo_recommendations(
            title_score, meta_description_score, content_score, structure_score,
            keyword_density_score, readability_score, internal_linking_score,
            external_linking_score, image_optimization_score, technical_seo_score,
            content, title, target_keywords
        )
        
        # Выявляем проблемы
        issues = self._identify_seo_issues(
            title_score, meta_description_score, content_score, structure_score,
            keyword_density_score, readability_score, content, title, target_keywords
        )
        
        # Анализируем ключевые слова
        keyword_analysis = {}
        for keyword in target_keywords:
            analysis = self.keyword_research._analyze_keyword(keyword, 'ru')
            if analysis:
                keyword_analysis[keyword] = analysis
        
        # Анализ конкурентов (заглушка)
        competitor_analysis = self._analyze_competitors(target_keywords)
        
        return SEOAnalysis(
            url=url,
            title_score=title_score,
            meta_description_score=meta_description_score,
            content_score=content_score,
            structure_score=structure_score,
            keyword_density_score=keyword_density_score,
            readability_score=readability_score,
            internal_linking_score=internal_linking_score,
            external_linking_score=external_linking_score,
            image_optimization_score=image_optimization_score,
            technical_seo_score=technical_seo_score,
            overall_seo_score=overall_seo_score,
            recommendations=recommendations,
            issues=issues,
            keyword_analysis=keyword_analysis,
            competitor_analysis=competitor_analysis
        )
    
    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """Извлечение ключевых слов из контента"""
        # Убираем HTML теги и Markdown
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'[#*`]', '', clean_content)
        
        # Токенизируем
        words = word_tokenize(clean_content.lower())
        
        # Фильтруем стоп-слова и короткие слова
        keywords = [word for word in words 
                   if word not in self.stop_words 
                   and len(word) > 3 
                   and word.isalpha()]
        
        # Подсчитываем частоту
        word_freq = Counter(keywords)
        
        # Возвращаем топ-10 самых частых слов
        return [word for word, count in word_freq.most_common(10)]
    
    def _analyze_title_seo(self, title: str, keywords: List[str]) -> float:
        """Анализ SEO заголовка"""
        score = 0.0
        rules = self.seo_rules['title']
        
        # Длина заголовка
        if rules['min_length'] <= len(title) <= rules['max_length']:
            score += 0.4
        elif len(title) > rules['max_length']:
            score += 0.2
        
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
            score += 0.1
        
        return min(1.0, score)
    
    def _analyze_meta_description_seo(self, content: str, keywords: List[str]) -> float:
        """Анализ SEO мета-описания"""
        score = 0.0
        rules = self.seo_rules['meta_description']
        
        # Извлекаем мета-описание из контента
        sentences = sent_tokenize(content)
        meta_description = sentences[0][:rules['max_length']] if sentences else ""
        
        # Длина мета-описания
        if rules['min_length'] <= len(meta_description) <= rules['max_length']:
            score += 0.4
        
        # Наличие ключевых слов
        meta_lower = meta_description.lower()
        for keyword in keywords:
            if keyword.lower() in meta_lower:
                score += 0.3
                break
        
        # Призыв к действию
        cta_words = ['узнать', 'читать', 'подробнее', 'скачать', 'заказать']
        if any(word in meta_lower for word in cta_words):
            score += 0.3
        
        return min(1.0, score)
    
    def _analyze_content_seo(self, content: str, keywords: List[str]) -> float:
        """Анализ SEO контента"""
        score = 0.0
        rules = self.seo_rules['content']
        
        # Длина контента
        word_count = len(content.split())
        if word_count >= rules['min_word_count']:
            score += 0.3
        if word_count >= rules['optimal_word_count']:
            score += 0.2
        
        # Плотность ключевых слов
        keyword_density = self._calculate_keyword_density(content, keywords)
        if rules['min_keyword_density'] <= keyword_density <= rules['max_keyword_density']:
            score += 0.3
        
        # Уникальность контента
        unique_words = len(set(content.split()))
        if unique_words / word_count > 0.7:
            score += 0.2
        
        return min(1.0, score)
    
    def _analyze_structure_seo(self, content: str, keywords: List[str]) -> float:
        """Анализ структуры для SEO"""
        score = 0.0
        rules = self.seo_rules['headings']
        
        # Наличие заголовков
        h1_count = len(re.findall(r'^#\s+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s+', content, re.MULTILINE))
        
        if h1_count == rules['h1_count']:
            score += 0.3
        if h2_count >= rules['h2_min_count']:
            score += 0.3
        
        # Ключевые слова в заголовках
        if rules['keyword_in_headings']:
            headings_text = ' '.join(re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE))
            for keyword in keywords:
                if keyword.lower() in headings_text.lower():
                    score += 0.2
                    break
        
        # Наличие списков
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            score += 0.1
        
        # Наличие выделений
        if re.search(r'\*\*.*?\*\*', content):
            score += 0.1
        
        return min(1.0, score)
    
    def _analyze_keyword_density(self, content: str, keywords: List[str]) -> float:
        """Анализ плотности ключевых слов"""
        if not keywords:
            return 0.0
        
        keyword_density = self._calculate_keyword_density(content, keywords)
        rules = self.seo_rules['content']
        
        if rules['min_keyword_density'] <= keyword_density <= rules['max_keyword_density']:
            return 1.0
        elif keyword_density < rules['min_keyword_density']:
            return 0.5
        else:
            return 0.2
    
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
    
    def _analyze_readability_seo(self, content: str) -> float:
        """Анализ читаемости для SEO"""
        try:
            readability_score = flesch_reading_ease(content)
            
            # Оптимальный диапазон для читаемости
            if 60 <= readability_score <= 80:
                return 1.0
            elif 40 <= readability_score < 60:
                return 0.7
            elif 80 < readability_score <= 100:
                return 0.8
            else:
                return 0.3
        except:
            return 0.5
    
    def _analyze_internal_linking(self, content: str) -> float:
        """Анализ внутренних ссылок"""
        score = 0.0
        
        # Подсчет внутренних ссылок
        internal_links = re.findall(r'\[([^\]]+)\]\(/[^)]+\)', content)
        
        if len(internal_links) >= 2:
            score += 0.5
        elif len(internal_links) >= 1:
            score += 0.3
        
        # Качество якорного текста
        for link_text in internal_links:
            if len(link_text) > 3 and len(link_text) < 50:
                score += 0.1
        
        return min(1.0, score)
    
    def _analyze_external_linking(self, content: str) -> float:
        """Анализ внешних ссылок"""
        score = 0.0
        
        # Подсчет внешних ссылок
        external_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', content)
        
        if len(external_links) >= 1:
            score += 0.5
        
        # Качество внешних ссылок
        for link_text, url in external_links:
            if any(domain in url for domain in ['wikipedia.org', 'gov.ru', 'edu.ru']):
                score += 0.2
        
        return min(1.0, score)
    
    def _analyze_image_optimization(self, content: str) -> float:
        """Анализ оптимизации изображений"""
        score = 0.0
        rules = self.seo_rules['images']
        
        # Подсчет изображений
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        
        if images:
            score += 0.3
            
            # Проверка alt-текста
            for alt_text, image_url in images:
                if alt_text and len(alt_text) > 3:
                    score += 0.2
                else:
                    score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _analyze_technical_seo(self, url: str, content: str) -> float:
        """Анализ технического SEO"""
        score = 0.0
        
        # Анализ URL
        if url:
            if len(url) < 100:
                score += 0.2
            if '-' in url or '_' in url:  # Читаемые URL
                score += 0.2
            if not re.search(r'[A-Z]', url):  # Нижний регистр
                score += 0.1
        
        # Скорость загрузки (заглушка)
        score += 0.3
        
        # Мобильная адаптация (заглушка)
        score += 0.3
        
        return min(1.0, score)
    
    def _generate_seo_recommendations(self, title_score: float, meta_score: float,
                                    content_score: float, structure_score: float,
                                    keyword_score: float, readability_score: float,
                                    internal_score: float, external_score: float,
                                    image_score: float, technical_score: float,
                                    content: str, title: str, keywords: List[str]) -> List[str]:
        """Генерация SEO рекомендаций"""
        recommendations = []
        
        if title_score < 0.7:
            recommendations.append("Улучшите заголовок: добавьте ключевые слова в начало, оптимизируйте длину")
        
        if meta_score < 0.7:
            recommendations.append("Создайте мета-описание с ключевыми словами и призывом к действию")
        
        if content_score < 0.7:
            recommendations.append("Увеличьте объем контента и оптимизируйте плотность ключевых слов")
        
        if structure_score < 0.7:
            recommendations.append("Добавьте больше заголовков H2 и H3, используйте списки")
        
        if keyword_score < 0.7:
            recommendations.append("Оптимизируйте плотность ключевых слов")
        
        if readability_score < 0.7:
            recommendations.append("Упростите текст для лучшей читаемости")
        
        if internal_score < 0.5:
            recommendations.append("Добавьте внутренние ссылки на релевантные страницы")
        
        if external_score < 0.5:
            recommendations.append("Добавьте авторитетные внешние ссылки")
        
        if image_score < 0.7:
            recommendations.append("Добавьте alt-текст к изображениям")
        
        if technical_score < 0.7:
            recommendations.append("Оптимизируйте технические аспекты: URL, скорость загрузки")
        
        return recommendations
    
    def _identify_seo_issues(self, title_score: float, meta_score: float,
                           content_score: float, structure_score: float,
                           keyword_score: float, readability_score: float,
                           content: str, title: str, keywords: List[str]) -> List[str]:
        """Выявление SEO проблем"""
        issues = []
        
        if title_score < 0.5:
            issues.append("Критическая проблема: заголовок не оптимизирован")
        
        if meta_score < 0.5:
            issues.append("Критическая проблема: отсутствует мета-описание")
        
        if content_score < 0.5:
            issues.append("Критическая проблема: недостаточный объем контента")
        
        if keyword_score < 0.3:
            issues.append("Критическая проблема: очень низкая плотность ключевых слов")
        
        if readability_score < 0.3:
            issues.append("Критическая проблема: очень низкая читаемость")
        
        return issues
    
    def _analyze_competitors(self, keywords: List[str]) -> Dict[str, Any]:
        """Анализ конкурентов (заглушка)"""
        return {
            'top_competitors': [],
            'competitor_analysis': 'Анализ конкурентов недоступен',
            'market_opportunities': []
        }

class ContentSEOOptimizer:
    """SEO оптимизатор контента"""
    
    def __init__(self):
        self.analyzer = ContentSEOAnalyzer()
        self.keyword_research = KeywordResearch()
    
    async def optimize_content(self, content: str, title: str, 
                             target_keywords: List[str] = None) -> ContentOptimization:
        """Оптимизация контента для SEO"""
        
        if not target_keywords:
            target_keywords = self.analyzer._extract_keywords_from_content(content)
        
        # Анализируем текущее состояние
        seo_analysis = self.analyzer.analyze_content_seo(content, title, "", target_keywords)
        
        optimized_content = content
        changes_made = []
        seo_improvements = []
        readability_improvements = []
        keyword_optimizations = []
        
        # Оптимизируем заголовки
        if seo_analysis.structure_score < 0.7:
            optimized_content, heading_changes = self._optimize_headings(optimized_content, target_keywords)
            changes_made.extend(heading_changes)
            seo_improvements.append("Оптимизированы заголовки для SEO")
        
        # Оптимизируем плотность ключевых слов
        if seo_analysis.keyword_density_score < 0.7:
            optimized_content, keyword_changes = self._optimize_keyword_density(
                optimized_content, target_keywords
            )
            changes_made.extend(keyword_changes)
            keyword_optimizations.append("Оптимизирована плотность ключевых слов")
        
        # Улучшаем читаемость
        if seo_analysis.readability_score < 0.7:
            optimized_content, readability_changes = self._improve_readability(optimized_content)
            changes_made.extend(readability_changes)
            readability_improvements.append("Улучшена читаемость текста")
        
        # Добавляем внутренние ссылки
        if seo_analysis.internal_linking_score < 0.5:
            optimized_content, linking_changes = self._add_internal_links(optimized_content, target_keywords)
            changes_made.extend(linking_changes)
            seo_improvements.append("Добавлены внутренние ссылки")
        
        # Оптимизируем изображения
        if seo_analysis.image_optimization_score < 0.7:
            optimized_content, image_changes = self._optimize_images(optimized_content, target_keywords)
            changes_made.extend(image_changes)
            seo_improvements.append("Оптимизированы изображения")
        
        return ContentOptimization(
            original_content=content,
            optimized_content=optimized_content,
            changes_made=changes_made,
            seo_improvements=seo_improvements,
            readability_improvements=readability_improvements,
            keyword_optimizations=keyword_optimizations
        )
    
    def _optimize_headings(self, content: str, keywords: List[str]) -> Tuple[str, List[str]]:
        """Оптимизация заголовков"""
        changes = []
        
        # Добавляем ключевые слова в заголовки
        lines = content.split('\n')
        optimized_lines = []
        
        for line in lines:
            if line.startswith('##') and keywords:
                # Добавляем ключевое слово в заголовок если его там нет
                heading_text = line[2:].strip()
                if not any(keyword.lower() in heading_text.lower() for keyword in keywords):
                    keyword = keywords[0]
                    optimized_line = f"## {keyword}: {heading_text}"
                    optimized_lines.append(optimized_line)
                    changes.append(f"Добавлено ключевое слово '{keyword}' в заголовок")
                else:
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines), changes
    
    def _optimize_keyword_density(self, content: str, keywords: List[str]) -> Tuple[str, List[str]]:
        """Оптимизация плотности ключевых слов"""
        changes = []
        
        # Вычисляем текущую плотность
        current_density = self.analyzer._calculate_keyword_density(content, keywords)
        target_density = 0.02  # 2%
        
        if current_density < target_density:
            # Добавляем ключевые слова в контент
            sentences = sent_tokenize(content)
            optimized_sentences = []
            
            for sentence in sentences:
                optimized_sentences.append(sentence)
                
                # Добавляем ключевое слово в некоторые предложения
                if np.random.random() < 0.1 and keywords:  # 10% вероятность
                    keyword = keywords[0]
                    if keyword.lower() not in sentence.lower():
                        additional_sentence = f"Важно отметить, что {keyword} играет ключевую роль в этом процессе."
                        optimized_sentences.append(additional_sentence)
                        changes.append(f"Добавлено предложение с ключевым словом '{keyword}'")
            
            return '. '.join(optimized_sentences), changes
        
        return content, changes
    
    def _improve_readability(self, content: str) -> Tuple[str, List[str]]:
        """Улучшение читаемости"""
        changes = []
        
        # Разбиваем длинные предложения
        sentences = sent_tokenize(content)
        optimized_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) > 25:  # Длинные предложения
                # Простое разбиение по запятым
                parts = sentence.split(',')
                if len(parts) > 1:
                    optimized_sentences.extend([part.strip() + '.' for part in parts])
                    changes.append("Разбито длинное предложение")
                else:
                    optimized_sentences.append(sentence)
            else:
                optimized_sentences.append(sentence)
        
        return '. '.join(optimized_sentences), changes
    
    def _add_internal_links(self, content: str, keywords: List[str]) -> Tuple[str, List[str]]:
        """Добавление внутренних ссылок"""
        changes = []
        
        # Ищем релевантные посты в базе данных
        relevant_posts = []
        for keyword in keywords[:3]:
            posts = Post.query.filter(
                Post.title.contains(keyword) | Post.content.contains(keyword)
            ).limit(2).all()
            relevant_posts.extend(posts)
        
        # Добавляем ссылки в контент
        if relevant_posts:
            # Добавляем раздел с дополнительными материалами
            additional_section = "\n\n## Дополнительные материалы\n\n"
            for post in relevant_posts[:3]:
                additional_section += f"- [{post.title}](/post/{post.id})\n"
            
            content += additional_section
            changes.append("Добавлены внутренние ссылки на релевантные статьи")
        
        return content, changes
    
    def _optimize_images(self, content: str, keywords: List[str]) -> Tuple[str, List[str]]:
        """Оптимизация изображений"""
        changes = []
        
        # Ищем изображения без alt-текста
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        
        optimized_content = content
        for alt_text, image_url in images:
            if not alt_text and keywords:
                # Добавляем alt-текст с ключевым словом
                keyword = keywords[0]
                new_image = f"![{keyword} - {os.path.basename(image_url)}]({image_url})"
                optimized_content = optimized_content.replace(
                    f"![{alt_text}]({image_url})", new_image
                )
                changes.append(f"Добавлен alt-текст с ключевым словом '{keyword}'")
        
        return optimized_content, changes
    
    async def generate_seo_optimized_title(self, topic: str, keywords: List[str]) -> str:
        """Генерация SEO-оптимизированного заголовка"""
        
        prompt = f"""
        Создай SEO-оптимизированный заголовок для статьи на тему "{topic}".
        
        Требования:
        - Длина: 30-60 символов
        - Включи ключевые слова: {', '.join(keywords[:3])}
        - Используй эмоциональные слова
        - Сделай заголовок привлекательным
        
        Предложи 5 вариантов заголовков.
        """
        
        try:
            response = await generate_with_ai(prompt, provider="openai", model="gpt-4")
            
            # Извлекаем заголовки из ответа
            titles = []
            for line in response.split('\n'):
                if line.strip() and not line.startswith('-') and not line.startswith('*'):
                    title = line.strip()
                    if 30 <= len(title) <= 60:
                        titles.append(title)
            
            return titles[0] if titles else f"{topic}: полное руководство"
            
        except Exception as e:
            logger.error(f"Ошибка генерации SEO заголовка: {e}")
            return f"{topic}: полное руководство"
    
    async def generate_seo_meta_description(self, content: str, keywords: List[str]) -> str:
        """Генерация SEO мета-описания"""
        
        prompt = f"""
        Создай SEO-оптимизированное мета-описание для статьи со следующим содержанием:
        
        {content[:500]}...
        
        Требования:
        - Длина: 120-160 символов
        - Включи ключевые слова: {', '.join(keywords[:2])}
        - Добавь призыв к действию
        - Сделай описание привлекательным
        
        Предложи 3 варианта мета-описания.
        """
        
        try:
            response = await generate_with_ai(prompt, provider="openai", model="gpt-4")
            
            # Извлекаем мета-описания из ответа
            descriptions = []
            for line in response.split('\n'):
                if line.strip() and not line.startswith('-') and not line.startswith('*'):
                    description = line.strip()
                    if 120 <= len(description) <= 160:
                        descriptions.append(description)
            
            return descriptions[0] if descriptions else content[:150] + "..."
            
        except Exception as e:
            logger.error(f"Ошибка генерации мета-описания: {e}")
            return content[:150] + "..."

# Глобальные экземпляры
keyword_research = KeywordResearch()
content_seo_analyzer = ContentSEOAnalyzer()
content_seo_optimizer = ContentSEOOptimizer()

# Удобные функции
def research_keywords(topic: str, language: str = 'ru') -> List[KeywordAnalysis]:
    """Исследование ключевых слов"""
    return keyword_research.research_keywords(topic, language)

def analyze_content_seo(content: str, title: str, url: str = "", 
                       target_keywords: List[str] = None) -> SEOAnalysis:
    """SEO анализ контента"""
    return content_seo_analyzer.analyze_content_seo(content, title, url, target_keywords)

async def optimize_content_seo(content: str, title: str, 
                              target_keywords: List[str] = None) -> ContentOptimization:
    """SEO оптимизация контента"""
    return await content_seo_optimizer.optimize_content(content, title, target_keywords)

async def generate_seo_title(topic: str, keywords: List[str]) -> str:
    """Генерация SEO заголовка"""
    return await content_seo_optimizer.generate_seo_optimized_title(topic, keywords)

async def generate_seo_meta_description(content: str, keywords: List[str]) -> str:
    """Генерация SEO мета-описания"""
    return await content_seo_optimizer.generate_seo_meta_description(content, keywords)