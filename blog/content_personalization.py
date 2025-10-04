"""
Система персонализации контента
Анализ пользовательских предпочтений, адаптация контента и рекомендации
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import sqlite3
from contextlib import contextmanager
import pickle
import hashlib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import pandas as pd

from blog.models_perfect import Post, Category, Tag, Comment, User, View
from blog import db
from blog.ai_provider_manager import generate_with_ai

logger = logging.getLogger(__name__)

class UserSegment(Enum):
    """Сегменты пользователей"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    CASUAL_READER = "casual_reader"
    PROFESSIONAL = "professional"
    STUDENT = "student"
    ENTREPRENEUR = "entrepreneur"

class ContentPreference(Enum):
    """Предпочтения контента"""
    SHORT_FORM = "short_form"
    LONG_FORM = "long_form"
    VISUAL_HEAVY = "visual_heavy"
    TEXT_FOCUSED = "text_focused"
    TECHNICAL = "technical"
    SIMPLIFIED = "simplified"
    NEWS_FOCUSED = "news_focused"
    TUTORIAL_FOCUSED = "tutorial_focused"

@dataclass
class UserProfile:
    """Профиль пользователя"""
    user_id: int
    segments: List[UserSegment]
    preferences: Dict[ContentPreference, float]
    reading_history: List[int]  # post_ids
    engagement_scores: Dict[int, float]  # post_id -> score
    time_preferences: Dict[str, int]  # hour -> count
    category_preferences: Dict[str, float]
    topic_preferences: Dict[str, float]
    reading_speed: float  # words per minute
    average_session_duration: float  # minutes
    preferred_content_length: str  # short, medium, long
    preferred_tone: str
    last_updated: datetime

@dataclass
class ContentRecommendation:
    """Рекомендация контента"""
    post_id: int
    title: str
    excerpt: str
    category: str
    score: float
    reasons: List[str]
    personalized_aspects: Dict[str, Any]

class UserBehaviorAnalyzer:
    """Анализатор поведения пользователей"""
    
    def __init__(self, db_path: str = "user_analytics.db"):
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных для аналитики"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    profile_data TEXT,
                    last_updated TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    post_id INTEGER,
                    start_time TEXT,
                    end_time TEXT,
                    scroll_depth REAL,
                    time_spent REAL,
                    engagement_score REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS content_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    post_id INTEGER,
                    interaction_type TEXT,
                    timestamp TEXT,
                    metadata TEXT
                )
            ''')
    
    def analyze_user_behavior(self, user_id: int) -> UserProfile:
        """Анализ поведения пользователя"""
        
        # Получаем данные о чтении
        reading_sessions = self._get_reading_sessions(user_id)
        interactions = self._get_user_interactions(user_id)
        
        # Анализируем предпочтения по категориям
        category_preferences = self._analyze_category_preferences(user_id)
        
        # Анализируем предпочтения по темам
        topic_preferences = self._analyze_topic_preferences(user_id)
        
        # Определяем сегменты пользователя
        segments = self._determine_user_segments(user_id, reading_sessions, interactions)
        
        # Анализируем предпочтения контента
        content_preferences = self._analyze_content_preferences(user_id)
        
        # Анализируем временные предпочтения
        time_preferences = self._analyze_time_preferences(user_id)
        
        # Вычисляем скорость чтения
        reading_speed = self._calculate_reading_speed(user_id)
        
        # Вычисляем среднюю длительность сессии
        avg_session_duration = self._calculate_avg_session_duration(user_id)
        
        # Определяем предпочитаемую длину контента
        preferred_length = self._determine_preferred_length(user_id)
        
        # Определяем предпочитаемый тон
        preferred_tone = self._determine_preferred_tone(user_id)
        
        # Получаем историю чтения
        reading_history = self._get_reading_history(user_id)
        
        # Вычисляем оценки вовлеченности
        engagement_scores = self._calculate_engagement_scores(user_id)
        
        profile = UserProfile(
            user_id=user_id,
            segments=segments,
            preferences=content_preferences,
            reading_history=reading_history,
            engagement_scores=engagement_scores,
            time_preferences=time_preferences,
            category_preferences=category_preferences,
            topic_preferences=topic_preferences,
            reading_speed=reading_speed,
            average_session_duration=avg_session_duration,
            preferred_content_length=preferred_length,
            preferred_tone=preferred_tone,
            last_updated=datetime.now()
        )
        
        # Сохраняем профиль
        self._save_user_profile(profile)
        
        return profile
    
    def _get_reading_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение сессий чтения пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM reading_sessions 
                    WHERE user_id = ? 
                    ORDER BY start_time DESC 
                    LIMIT 100
                ''', (user_id,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except:
            return []
    
    def _get_user_interactions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение взаимодействий пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM content_interactions 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 200
                ''', (user_id,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except:
            return []
    
    def _analyze_category_preferences(self, user_id: int) -> Dict[str, float]:
        """Анализ предпочтений по категориям"""
        preferences = defaultdict(float)
        
        # Получаем посты, которые читал пользователь
        user_posts = db.session.query(Post).join(View).filter(
            View.user_id == user_id
        ).all()
        
        total_posts = len(user_posts)
        if total_posts == 0:
            return {}
        
        # Подсчитываем предпочтения
        for post in user_posts:
            if post.category:
                category_name = post.category.name
                preferences[category_name] += 1.0
        
        # Нормализуем
        for category in preferences:
            preferences[category] /= total_posts
        
        return dict(preferences)
    
    def _analyze_topic_preferences(self, user_id: int) -> Dict[str, float]:
        """Анализ предпочтений по темам"""
        preferences = defaultdict(float)
        
        # Получаем теги из постов, которые читал пользователь
        user_posts = db.session.query(Post).join(View).filter(
            View.user_id == user_id
        ).all()
        
        total_tags = 0
        for post in user_posts:
            for tag in post.tags:
                preferences[tag.name] += 1.0
                total_tags += 1
        
        if total_tags == 0:
            return {}
        
        # Нормализуем
        for topic in preferences:
            preferences[topic] /= total_tags
        
        return dict(preferences)
    
    def _determine_user_segments(self, user_id: int, reading_sessions: List[Dict], 
                               interactions: List[Dict]) -> List[UserSegment]:
        """Определение сегментов пользователя"""
        segments = []
        
        # Анализируем активность
        total_sessions = len(reading_sessions)
        avg_session_duration = np.mean([s.get('time_spent', 0) for s in reading_sessions]) if reading_sessions else 0
        
        # Сегмент по активности
        if total_sessions > 50:
            segments.append(UserSegment.EXPERT)
        elif total_sessions > 20:
            segments.append(UserSegment.INTERMEDIATE)
        else:
            segments.append(UserSegment.BEGINNER)
        
        # Сегмент по времени чтения
        if avg_session_duration > 10:
            segments.append(UserSegment.PROFESSIONAL)
        elif avg_session_duration > 5:
            segments.append(UserSegment.INTERMEDIATE)
        else:
            segments.append(UserSegment.CASUAL_READER)
        
        # Анализируем типы взаимодействий
        interaction_types = [i.get('interaction_type', '') for i in interactions]
        if 'comment' in interaction_types:
            segments.append(UserSegment.EXPERT)
        if 'share' in interaction_types:
            segments.append(UserSegment.ENTREPRENEUR)
        
        return list(set(segments))  # Убираем дубликаты
    
    def _analyze_content_preferences(self, user_id: int) -> Dict[ContentPreference, float]:
        """Анализ предпочтений контента"""
        preferences = defaultdict(float)
        
        # Получаем посты пользователя
        user_posts = db.session.query(Post).join(View).filter(
            View.user_id == user_id
        ).all()
        
        if not user_posts:
            return {}
        
        for post in user_posts:
            word_count = len(post.content.split())
            
            # Предпочтения по длине
            if word_count < 500:
                preferences[ContentPreference.SHORT_FORM] += 1.0
            elif word_count > 2000:
                preferences[ContentPreference.LONG_FORM] += 1.0
            
            # Предпочтения по типу контента
            if '##' in post.content:  # Структурированный контент
                preferences[ContentPreference.TUTORIAL_FOCUSED] += 1.0
            
            if any(word in post.content.lower() for word in ['новости', 'события', 'происходит']):
                preferences[ContentPreference.NEWS_FOCUSED] += 1.0
            
            if any(word in post.content.lower() for word in ['технический', 'алгоритм', 'код']):
                preferences[ContentPreference.TECHNICAL] += 1.0
        
        # Нормализуем
        total_posts = len(user_posts)
        for preference in preferences:
            preferences[preference] /= total_posts
        
        return dict(preferences)
    
    def _analyze_time_preferences(self, user_id: int) -> Dict[str, int]:
        """Анализ временных предпочтений"""
        preferences = defaultdict(int)
        
        # Получаем время просмотров
        views = db.session.query(View).filter(View.user_id == user_id).all()
        
        for view in views:
            if view.timestamp:
                hour = view.timestamp.hour
                preferences[str(hour)] += 1
        
        return dict(preferences)
    
    def _calculate_reading_speed(self, user_id: int) -> float:
        """Вычисление скорости чтения"""
        # Получаем сессии с известным временем чтения
        sessions = self._get_reading_sessions(user_id)
        
        if not sessions:
            return 200.0  # Средняя скорость по умолчанию
        
        total_words = 0
        total_time = 0
        
        for session in sessions:
            post_id = session.get('post_id')
            time_spent = session.get('time_spent', 0)
            
            if post_id and time_spent > 0:
                post = Post.query.get(post_id)
                if post:
                    word_count = len(post.content.split())
                    total_words += word_count
                    total_time += time_spent
        
        if total_time > 0:
            return total_words / (total_time / 60)  # слова в минуту
        
        return 200.0
    
    def _calculate_avg_session_duration(self, user_id: int) -> float:
        """Вычисление средней длительности сессии"""
        sessions = self._get_reading_sessions(user_id)
        
        if not sessions:
            return 5.0  # Средняя длительность по умолчанию
        
        durations = [s.get('time_spent', 0) for s in sessions if s.get('time_spent', 0) > 0]
        
        if durations:
            return np.mean(durations)
        
        return 5.0
    
    def _determine_preferred_length(self, user_id: int) -> str:
        """Определение предпочитаемой длины контента"""
        user_posts = db.session.query(Post).join(View).filter(
            View.user_id == user_id
        ).all()
        
        if not user_posts:
            return 'medium'
        
        word_counts = [len(post.content.split()) for post in user_posts]
        avg_word_count = np.mean(word_counts)
        
        if avg_word_count < 500:
            return 'short'
        elif avg_word_count > 2000:
            return 'long'
        else:
            return 'medium'
    
    def _determine_preferred_tone(self, user_id: int) -> str:
        """Определение предпочитаемого тона"""
        # Простая эвристика на основе комментариев пользователя
        user_comments = Comment.query.filter_by(author_id=user_id).all()
        
        if not user_comments:
            return 'conversational'
        
        # Анализируем стиль комментариев
        formal_words = ['согласно', 'следовательно', 'таким образом', 'в связи с']
        casual_words = ['круто', 'классно', 'прикольно', 'норм']
        
        formal_count = sum(1 for comment in user_comments 
                          for word in formal_words 
                          if word in comment.content.lower())
        casual_count = sum(1 for comment in user_comments 
                          for word in casual_words 
                          if word in comment.content.lower())
        
        if formal_count > casual_count:
            return 'professional'
        elif casual_count > formal_count:
            return 'conversational'
        else:
            return 'conversational'
    
    def _get_reading_history(self, user_id: int) -> List[int]:
        """Получение истории чтения"""
        views = db.session.query(View).filter(View.user_id == user_id).order_by(
            View.timestamp.desc()
        ).limit(100).all()
        
        return [view.post_id for view in views if view.post_id]
    
    def _calculate_engagement_scores(self, user_id: int) -> Dict[int, float]:
        """Вычисление оценок вовлеченности"""
        scores = {}
        
        # Получаем взаимодействия пользователя
        interactions = self._get_user_interactions(user_id)
        
        for interaction in interactions:
            post_id = interaction.get('post_id')
            interaction_type = interaction.get('interaction_type', '')
            
            if post_id:
                if post_id not in scores:
                    scores[post_id] = 0.0
                
                # Разные типы взаимодействий имеют разный вес
                if interaction_type == 'like':
                    scores[post_id] += 1.0
                elif interaction_type == 'comment':
                    scores[post_id] += 2.0
                elif interaction_type == 'share':
                    scores[post_id] += 3.0
                elif interaction_type == 'bookmark':
                    scores[post_id] += 1.5
        
        return scores
    
    def _save_user_profile(self, profile: UserProfile):
        """Сохранение профиля пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                profile_data = json.dumps(asdict(profile), default=str)
                conn.execute('''
                    INSERT OR REPLACE INTO user_profiles 
                    (user_id, profile_data, last_updated)
                    VALUES (?, ?, ?)
                ''', (profile.user_id, profile_data, datetime.now().isoformat()))
        except Exception as e:
            logger.error(f"Ошибка сохранения профиля пользователя: {e}")
    
    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Получение профиля пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT profile_data FROM user_profiles WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    profile_data = json.loads(row[0])
                    return UserProfile(**profile_data)
        except Exception as e:
            logger.error(f"Ошибка получения профиля пользователя: {e}")
        
        return None

class ContentPersonalizer:
    """Персонализатор контента"""
    
    def __init__(self):
        self.behavior_analyzer = UserBehaviorAnalyzer()
        self.content_vectorizer = TfidfVectorizer(max_features=500)
        self.user_profiles_cache = {}
    
    def personalize_content_request(self, request: Dict[str, Any], 
                                  user_id: int) -> Dict[str, Any]:
        """Персонализация запроса на контент"""
        
        # Получаем профиль пользователя
        profile = self._get_user_profile(user_id)
        
        if not profile:
            return request
        
        # Адаптируем параметры запроса
        personalized_request = request.copy()
        
        # Адаптируем длину контента
        personalized_request['length'] = profile.preferred_content_length
        
        # Адаптируем тон
        personalized_request['tone'] = profile.preferred_tone
        
        # Добавляем предпочитаемые темы
        if profile.topic_preferences:
            top_topics = sorted(profile.topic_preferences.items(), 
                              key=lambda x: x[1], reverse=True)[:3]
            preferred_topics = [topic for topic, score in top_topics]
            
            if 'keywords' not in personalized_request:
                personalized_request['keywords'] = []
            personalized_request['keywords'].extend(preferred_topics)
        
        # Адаптируем тип контента
        if profile.preferences:
            top_preference = max(profile.preferences.items(), key=lambda x: x[1])
            if top_preference[0] == ContentPreference.TUTORIAL_FOCUSED:
                personalized_request['content_type'] = 'how_to_guide'
            elif top_preference[0] == ContentPreference.NEWS_FOCUSED:
                personalized_request['content_type'] = 'news_article'
            elif top_preference[0] == ContentPreference.TECHNICAL:
                personalized_request['content_type'] = 'analytical_article'
        
        return personalized_request
    
    def personalize_content(self, content: str, user_id: int) -> str:
        """Персонализация контента"""
        
        profile = self._get_user_profile(user_id)
        
        if not profile:
            return content
        
        personalized_content = content
        
        # Адаптируем сложность языка
        if UserSegment.BEGINNER in profile.segments:
            personalized_content = self._simplify_language(personalized_content)
        elif UserSegment.EXPERT in profile.segments:
            personalized_content = self._add_technical_details(personalized_content)
        
        # Адаптируем длину
        if profile.preferred_content_length == 'short':
            personalized_content = self._shorten_content(personalized_content)
        elif profile.preferred_content_length == 'long':
            personalized_content = self._expand_content(personalized_content)
        
        # Адаптируем тон
        if profile.preferred_tone == 'professional':
            personalized_content = self._make_professional(personalized_content)
        elif profile.preferred_tone == 'conversational':
            personalized_content = self._make_conversational(personalized_content)
        
        return personalized_content
    
    def generate_personalized_recommendations(self, user_id: int, 
                                            limit: int = 10) -> List[ContentRecommendation]:
        """Генерация персонализированных рекомендаций"""
        
        profile = self._get_user_profile(user_id)
        
        if not profile:
            return []
        
        # Получаем все посты
        all_posts = Post.query.filter_by(is_published=True).all()
        
        recommendations = []
        
        for post in all_posts:
            # Пропускаем уже прочитанные
            if post.id in profile.reading_history:
                continue
            
            score = self._calculate_recommendation_score(post, profile)
            
            if score > 0.3:  # Минимальный порог
                reasons = self._generate_recommendation_reasons(post, profile)
                
                recommendation = ContentRecommendation(
                    post_id=post.id,
                    title=post.title,
                    excerpt=post.excerpt,
                    category=post.category.name if post.category else 'Без категории',
                    score=score,
                    reasons=reasons,
                    personalized_aspects={
                        'category_match': profile.category_preferences.get(
                            post.category.name, 0) if post.category else 0,
                        'topic_match': self._calculate_topic_match(post, profile),
                        'length_match': self._calculate_length_match(post, profile),
                        'tone_match': self._calculate_tone_match(post, profile)
                    }
                )
                
                recommendations.append(recommendation)
        
        # Сортируем по релевантности
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return recommendations[:limit]
    
    def _get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Получение профиля пользователя с кэшированием"""
        
        # Проверяем кэш
        if user_id in self.user_profiles_cache:
            profile, timestamp = self.user_profiles_cache[user_id]
            if datetime.now() - timestamp < timedelta(hours=1):
                return profile
        
        # Получаем из базы данных
        profile = self.behavior_analyzer.get_user_profile(user_id)
        
        if not profile:
            # Создаем новый профиль
            profile = self.behavior_analyzer.analyze_user_behavior(user_id)
        
        # Сохраняем в кэш
        self.user_profiles_cache[user_id] = (profile, datetime.now())
        
        return profile
    
    def _simplify_language(self, content: str) -> str:
        """Упрощение языка"""
        simplifications = {
            'осуществлять': 'делать',
            'производить': 'создавать',
            'является': 'это',
            'представлять собой': 'быть',
            'иметь место': 'происходить',
            'носить характер': 'быть',
            'оказывать воздействие': 'влиять',
            'концептуализация': 'понимание',
            'имплементация': 'внедрение',
            'оптимизация': 'улучшение'
        }
        
        for complex_word, simple_word in simplifications.items():
            content = content.replace(complex_word, simple_word)
        
        return content
    
    def _add_technical_details(self, content: str) -> str:
        """Добавление технических деталей"""
        technical_sections = [
            "\n\n## Технические детали\n\nДля специалистов важно отметить:",
            "\n\n## Углубленный анализ\n\nС технической точки зрения:",
            "\n\n## Экспертное мнение\n\nОпытные специалисты отмечают:"
        ]
        
        if np.random.random() < 0.3:  # 30% вероятность
            content += np.random.choice(technical_sections)
        
        return content
    
    def _shorten_content(self, content: str) -> str:
        """Сокращение контента"""
        sections = content.split('\n\n')
        if len(sections) > 4:
            # Оставляем введение, 2 основных раздела и заключение
            shortened = sections[:1] + sections[1:3] + sections[-1:]
            return '\n\n'.join(shortened)
        
        return content
    
    def _expand_content(self, content: str) -> str:
        """Расширение контента"""
        additional_sections = [
            "\n\n## Дополнительная информация\n\nДля более полного понимания:",
            "\n\n## Практические советы\n\nВ практическом применении:",
            "\n\n## Часто задаваемые вопросы\n\nМногие читатели интересуются:"
        ]
        
        content += np.random.choice(additional_sections)
        return content
    
    def _make_professional(self, content: str) -> str:
        """Сделать контент более профессиональным"""
        # Заменяем разговорные выражения на формальные
        replacements = {
            'круто': 'эффективно',
            'классно': 'отлично',
            'прикольно': 'интересно',
            'норм': 'хорошо',
            'короче': 'вкратце',
            'кстати': 'кроме того'
        }
        
        for casual, formal in replacements.items():
            content = content.replace(casual, formal)
        
        return content
    
    def _make_conversational(self, content: str) -> str:
        """Сделать контент более разговорным"""
        # Добавляем разговорные элементы
        conversational_elements = [
            "Кстати, ",
            "Кстати говоря, ",
            "Между прочим, ",
            "Кроме того, ",
            "Также стоит отметить, что "
        ]
        
        sentences = content.split('.')
        for i in range(1, len(sentences), 3):  # Каждое третье предложение
            if i < len(sentences) and sentences[i].strip():
                sentences[i] = np.random.choice(conversational_elements) + sentences[i].lower()
        
        return '.'.join(sentences)
    
    def _calculate_recommendation_score(self, post: Post, profile: UserProfile) -> float:
        """Вычисление оценки рекомендации"""
        score = 0.0
        
        # Совпадение по категории
        if post.category and post.category.name in profile.category_preferences:
            score += profile.category_preferences[post.category.name] * 0.4
        
        # Совпадение по темам
        topic_match = self._calculate_topic_match(post, profile)
        score += topic_match * 0.3
        
        # Совпадение по длине
        length_match = self._calculate_length_match(post, profile)
        score += length_match * 0.2
        
        # Совпадение по тону
        tone_match = self._calculate_tone_match(post, profile)
        score += tone_match * 0.1
        
        return min(1.0, score)
    
    def _calculate_topic_match(self, post: Post, profile: UserProfile) -> float:
        """Вычисление совпадения по темам"""
        if not profile.topic_preferences:
            return 0.0
        
        post_tags = [tag.name for tag in post.tags]
        if not post_tags:
            return 0.0
        
        match_score = 0.0
        for tag in post_tags:
            if tag in profile.topic_preferences:
                match_score += profile.topic_preferences[tag]
        
        return min(1.0, match_score)
    
    def _calculate_length_match(self, post: Post, profile: UserProfile) -> float:
        """Вычисление совпадения по длине"""
        word_count = len(post.content.split())
        
        if profile.preferred_content_length == 'short' and word_count < 500:
            return 1.0
        elif profile.preferred_content_length == 'medium' and 500 <= word_count <= 2000:
            return 1.0
        elif profile.preferred_content_length == 'long' and word_count > 2000:
            return 1.0
        
        return 0.5  # Частичное совпадение
    
    def _calculate_tone_match(self, post: Post, profile: UserProfile) -> float:
        """Вычисление совпадения по тону"""
        # Простая эвристика на основе ключевых слов
        content_lower = post.content.lower()
        
        professional_words = ['согласно', 'следовательно', 'таким образом', 'анализ']
        conversational_words = ['кстати', 'между прочим', 'кроме того', 'также']
        
        professional_count = sum(1 for word in professional_words if word in content_lower)
        conversational_count = sum(1 for word in conversational_words if word in content_lower)
        
        if profile.preferred_tone == 'professional' and professional_count > conversational_count:
            return 1.0
        elif profile.preferred_tone == 'conversational' and conversational_count > professional_count:
            return 1.0
        
        return 0.5
    
    def _generate_recommendation_reasons(self, post: Post, profile: UserProfile) -> List[str]:
        """Генерация причин рекомендации"""
        reasons = []
        
        # Причины на основе категории
        if post.category and post.category.name in profile.category_preferences:
            score = profile.category_preferences[post.category.name]
            if score > 0.5:
                reasons.append(f"Вы часто читаете статьи о {post.category.name}")
        
        # Причины на основе тем
        matching_topics = []
        for tag in post.tags:
            if tag.name in profile.topic_preferences:
                matching_topics.append(tag.name)
        
        if matching_topics:
            reasons.append(f"Статья затрагивает интересующие вас темы: {', '.join(matching_topics[:2])}")
        
        # Причины на основе длины
        word_count = len(post.content.split())
        if profile.preferred_content_length == 'short' and word_count < 500:
            reasons.append("Короткая статья, как вы предпочитаете")
        elif profile.preferred_content_length == 'long' and word_count > 2000:
            reasons.append("Подробная статья, соответствующая вашим предпочтениям")
        
        return reasons[:3]  # Максимум 3 причины

class PersonalizedContentGenerator:
    """Генератор персонализированного контента"""
    
    def __init__(self):
        self.personalizer = ContentPersonalizer()
        self.behavior_analyzer = UserBehaviorAnalyzer()
    
    async def generate_personalized_content(self, topic: str, user_id: int, 
                                          base_request: Dict[str, Any] = None) -> str:
        """Генерация персонализированного контента"""
        
        # Базовый запрос
        if not base_request:
            base_request = {
                'topic': topic,
                'content_type': 'how_to_guide',
                'tone': 'conversational',
                'target_audience': 'general_public',
                'length': 'medium',
                'keywords': []
            }
        
        # Персонализируем запрос
        personalized_request = self.personalizer.personalize_content_request(
            base_request, user_id
        )
        
        # Генерируем контент
        prompt = self._create_generation_prompt(personalized_request)
        
        try:
            content = await generate_with_ai(
                prompt=prompt,
                provider="openai",
                model="gpt-4",
                max_tokens=2000,
                temperature=0.7
            )
            
            # Персонализируем сгенерированный контент
            personalized_content = self.personalizer.personalize_content(content, user_id)
            
            return personalized_content
            
        except Exception as e:
            logger.error(f"Ошибка генерации персонализированного контента: {e}")
            # Fallback на базовую генерацию
            return self._generate_fallback_content(topic)
    
    def _create_generation_prompt(self, request: Dict[str, Any]) -> str:
        """Создание промпта для генерации"""
        prompt = f"""
        Напиши статью на тему "{request['topic']}" со следующими характеристиками:
        
        - Тип контента: {request['content_type']}
        - Тон: {request['tone']}
        - Целевая аудитория: {request['target_audience']}
        - Длина: {request['length']}
        - Ключевые слова: {', '.join(request.get('keywords', []))}
        
        Статья должна быть информативной, хорошо структурированной и интересной для чтения.
        Используй заголовки, списки и выделения для улучшения читаемости.
        """
        
        return prompt
    
    def _generate_fallback_content(self, topic: str) -> str:
        """Fallback генерация контента"""
        return f"""
        # {topic}
        
        В современном мире тема {topic} становится все более актуальной. 
        В этой статье мы рассмотрим основные аспекты этой важной темы.
        
        ## Основные моменты
        
        - Первый важный аспект
        - Второй ключевой момент
        - Третий значимый фактор
        
        ## Заключение
        
        Таким образом, {topic} представляет собой важную область для изучения и развития.
        """
    
    def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Получение инсайтов о пользователе"""
        profile = self.personalizer._get_user_profile(user_id)
        
        if not profile:
            return {}
        
        return {
            'user_segments': [segment.value for segment in profile.segments],
            'preferred_categories': profile.category_preferences,
            'preferred_topics': profile.topic_preferences,
            'reading_speed': profile.reading_speed,
            'average_session_duration': profile.average_session_duration,
            'preferred_content_length': profile.preferred_content_length,
            'preferred_tone': profile.preferred_tone,
            'total_posts_read': len(profile.reading_history),
            'engagement_level': self._calculate_engagement_level(profile),
            'content_preferences': {pref.value: score for pref, score in profile.preferences.items()}
        }
    
    def _calculate_engagement_level(self, profile: UserProfile) -> str:
        """Вычисление уровня вовлеченности"""
        total_engagement = sum(profile.engagement_scores.values())
        posts_read = len(profile.reading_history)
        
        if posts_read == 0:
            return 'low'
        
        avg_engagement = total_engagement / posts_read
        
        if avg_engagement > 2.0:
            return 'high'
        elif avg_engagement > 1.0:
            return 'medium'
        else:
            return 'low'

# Глобальные экземпляры
user_behavior_analyzer = UserBehaviorAnalyzer()
content_personalizer = ContentPersonalizer()
personalized_content_generator = PersonalizedContentGenerator()

# Удобные функции
def analyze_user_behavior(user_id: int) -> UserProfile:
    """Анализ поведения пользователя"""
    return user_behavior_analyzer.analyze_user_behavior(user_id)

def get_personalized_recommendations(user_id: int, limit: int = 10) -> List[ContentRecommendation]:
    """Получение персонализированных рекомендаций"""
    return content_personalizer.generate_personalized_recommendations(user_id, limit)

async def generate_personalized_content(topic: str, user_id: int) -> str:
    """Генерация персонализированного контента"""
    return await personalized_content_generator.generate_personalized_content(topic, user_id)

def get_user_insights(user_id: int) -> Dict[str, Any]:
    """Получение инсайтов о пользователе"""
    return personalized_content_generator.get_user_insights(user_id)