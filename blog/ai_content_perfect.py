"""
Идеальная ИИ система для блога
Включает продвинутые алгоритмы, множественные провайдеры, оптимизацию и мониторинг
"""

import os
import re
import json
import time
import asyncio
import aiohttp
import openai
import anthropic
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import pickle
from collections import defaultdict, deque
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import jieba
# import pymorphy2  # Несовместим с Python 3.13
from transformers import pipeline, AutoTokenizer, AutoModel
import torch

from blog.models import Post, Category, Tag, User, db
from blog import db as database

# Загрузка NLTK данных
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

class AIProvider(Enum):
    """Провайдеры ИИ"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"

class ContentType(Enum):
    """Типы контента"""
    POST = "post"
    COMMENT = "comment"
    TITLE = "title"
    DESCRIPTION = "description"
    TAG = "tag"
    CATEGORY = "category"

@dataclass
class AIRequest:
    """Запрос к ИИ"""
    prompt: str
    content_type: ContentType
    provider: AIProvider
    max_tokens: int = 1000
    temperature: float = 0.7
    language: str = 'ru'
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None

@dataclass
class AIResponse:
    """Ответ от ИИ"""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    processing_time: float
    quality_score: float
    cost: float
    timestamp: datetime
    metadata: Dict[str, Any]

class AIConfig:
    """Конфигурация ИИ системы"""
    
    # Настройки провайдеров
    PROVIDERS = {
        AIProvider.OPENAI: {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
            'default_model': 'gpt-3.5-turbo',
            'max_tokens': 4000,
            'cost_per_token': 0.0001
        },
        AIProvider.ANTHROPIC: {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'default_model': 'claude-3-sonnet',
            'max_tokens': 4000,
            'cost_per_token': 0.00015
        },
        AIProvider.GOOGLE: {
            'api_key': os.getenv('GOOGLE_API_KEY'),
            'models': ['gemini-pro', 'gemini-pro-vision'],
            'default_model': 'gemini-pro',
            'max_tokens': 4000,
            'cost_per_token': 0.00005
        },
        AIProvider.LOCAL: {
            'models': ['llama2', 'mistral', 'codellama'],
            'default_model': 'llama2',
            'max_tokens': 2000,
            'cost_per_token': 0.0
        },
        AIProvider.HUGGINGFACE: {
            'api_key': os.getenv('HUGGINGFACE_API_KEY'),
            'models': ['microsoft/DialoGPT-medium', 'facebook/blenderbot-400M-distill'],
            'default_model': 'microsoft/DialoGPT-medium',
            'max_tokens': 1000,
            'cost_per_token': 0.00001
        }
    }
    
    # Настройки качества
    QUALITY_THRESHOLD = 0.7
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    
    # Настройки кэширования
    CACHE_TTL_SECONDS = 3600
    CACHE_MAX_SIZE = 10000
    
    # Настройки мониторинга
    MONITORING_ENABLED = True
    LOG_LEVEL = logging.INFO

class AICache:
    """Кэш для ИИ запросов"""
    
    def __init__(self):
        self.cache = {}
        self.access_times = {}
        self.max_size = AIConfig.CACHE_MAX_SIZE
        self.ttl = AIConfig.CACHE_TTL_SECONDS
    
    def _generate_key(self, request: AIRequest) -> str:
        """Генерация ключа кэша"""
        key_data = {
            'prompt': request.prompt,
            'content_type': request.content_type.value,
            'provider': request.provider.value,
            'max_tokens': request.max_tokens,
            'temperature': request.temperature,
            'language': request.language
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, request: AIRequest) -> Optional[AIResponse]:
        """Получение из кэша"""
        key = self._generate_key(request)
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.access_times[key] = time.time()
                return response
            else:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
        return None
    
    def set(self, request: AIRequest, response: AIResponse):
        """Сохранение в кэш"""
        key = self._generate_key(request)
        
        # Очистка старых записей
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = (response, time.time())
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """Удаление самых старых записей"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]

class AIMonitor:
    """Мониторинг ИИ системы"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.provider_stats = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'avg_response_time': 0.0
        })
        self.quality_scores = deque(maxlen=1000)
        self.error_logs = deque(maxlen=1000)
    
    def log_request(self, request: AIRequest, response: AIResponse, success: bool):
        """Логирование запроса"""
        provider = request.provider.value
        
        self.provider_stats[provider]['requests'] += 1
        if success:
            self.provider_stats[provider]['successes'] += 1
            self.provider_stats[provider]['total_tokens'] += response.tokens_used
            self.provider_stats[provider]['total_cost'] += response.cost
            
            # Обновление среднего времени ответа
            current_avg = self.provider_stats[provider]['avg_response_time']
            requests = self.provider_stats[provider]['requests']
            self.provider_stats[provider]['avg_response_time'] = (
                (current_avg * (requests - 1) + response.processing_time) / requests
            )
        else:
            self.provider_stats[provider]['failures'] += 1
        
        # Сохранение метрик
        self.metrics[provider].append({
            'timestamp': response.timestamp,
            'success': success,
            'tokens_used': response.tokens_used,
            'cost': response.cost,
            'processing_time': response.processing_time,
            'quality_score': response.quality_score
        })
        
        # Сохранение качества
        if success:
            self.quality_scores.append(response.quality_score)
    
    def log_error(self, error: Exception, request: AIRequest):
        """Логирование ошибки"""
        self.error_logs.append({
            'timestamp': datetime.utcnow(),
            'error': str(error),
            'provider': request.provider.value,
            'content_type': request.content_type.value
        })
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получение статистики провайдеров"""
        stats = {}
        for provider, data in self.provider_stats.items():
            stats[provider] = {
                'requests': data['requests'],
                'success_rate': data['successes'] / data['requests'] if data['requests'] > 0 else 0,
                'total_tokens': data['total_tokens'],
                'total_cost': data['total_cost'],
                'avg_response_time': data['avg_response_time']
            }
        return stats
    
    def get_quality_stats(self) -> Dict[str, float]:
        """Получение статистики качества"""
        if not self.quality_scores:
            return {'avg_quality': 0.0, 'min_quality': 0.0, 'max_quality': 0.0}
        
        scores = list(self.quality_scores)
        return {
            'avg_quality': np.mean(scores),
            'min_quality': np.min(scores),
            'max_quality': np.max(scores),
            'quality_std': np.std(scores)
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних ошибок"""
        return list(self.error_logs)[-limit:]

class ContentAnalyzer:
    """Анализатор контента"""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english') + stopwords.words('russian'))
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=list(self.stop_words))
        # self.morph = pymorphy2.MorphAnalyzer()  # Несовместим с Python 3.13
        self.morph = None
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализ текста"""
        # Базовая статистика
        words = word_tokenize(text.lower())
        sentences = text.split('.')
        
        # Удаление стоп-слов
        filtered_words = [word for word in words if word not in self.stop_words and word.isalpha()]
        
        # Анализ тональности
        sentiment = self._analyze_sentiment(text)
        
        # Анализ читаемости
        readability = self._calculate_readability(text)
        
        # Извлечение ключевых слов
        keywords = self._extract_keywords(text)
        
        # Анализ тематики
        topics = self._extract_topics(text)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'unique_words': len(set(words)),
            'avg_word_length': np.mean([len(word) for word in words]),
            'avg_sentence_length': np.mean([len(sentence.split()) for sentence in sentences]),
            'sentiment': sentiment,
            'readability': readability,
            'keywords': keywords,
            'topics': topics,
            'complexity_score': self._calculate_complexity(text)
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Анализ тональности"""
        # Простой анализ тональности на основе словаря
        positive_words = ['хорошо', 'отлично', 'прекрасно', 'замечательно', 'великолепно']
        negative_words = ['плохо', 'ужасно', 'отвратительно', 'кошмар', 'ужас']
        
        words = word_tokenize(text.lower())
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        neutral_score = 1.0 - positive_score - negative_score
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }
    
    def _calculate_readability(self, text: str) -> float:
        """Расчет читаемости (упрощенный индекс Флеша)"""
        sentences = text.split('.')
        words = text.split()
        
        if len(sentences) == 0 or len(words) == 0:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = np.mean([self._count_syllables(word) for word in words])
        
        # Упрощенная формула Флеша
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, readability))
    
    def _count_syllables(self, word: str) -> int:
        """Подсчет слогов в слове"""
        vowels = 'aeiouy'
        word = word.lower()
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        if word.endswith('e'):
            count -= 1
        
        return max(1, count)
    
    def _extract_keywords(self, text: str) -> List[Tuple[str, float]]:
        """Извлечение ключевых слов"""
        words = word_tokenize(text.lower())
        filtered_words = [word for word in words if word not in self.stop_words and word.isalpha()]
        
        # Подсчет частоты
        word_freq = defaultdict(int)
        for word in filtered_words:
            word_freq[word] += 1
        
        # Сортировка по частоте
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return keywords[:10]
    
    def _extract_topics(self, text: str) -> List[str]:
        """Извлечение тем"""
        # Простое извлечение тем на основе ключевых слов
        keywords = self._extract_keywords(text)
        topics = []
        
        # Маппинг ключевых слов на темы
        topic_mapping = {
            'технология': ['технология', 'технологии', 'технологический', 'программирование', 'код', 'алгоритм'],
            'наука': ['наука', 'научный', 'исследование', 'эксперимент', 'теория', 'гипотеза'],
            'искусство': ['искусство', 'художественный', 'творчество', 'дизайн', 'красота', 'эстетика'],
            'спорт': ['спорт', 'спортивный', 'тренировка', 'фитнес', 'здоровье', 'активность'],
            'путешествие': ['путешествие', 'путешествовать', 'туризм', 'отпуск', 'страна', 'город']
        }
        
        for keyword, freq in keywords:
            for topic, words in topic_mapping.items():
                if keyword in words:
                    topics.append(topic)
                    break
        
        return list(set(topics))
    
    def _calculate_complexity(self, text: str) -> float:
        """Расчет сложности текста"""
        words = word_tokenize(text.lower())
        sentences = text.split('.')
        
        if len(sentences) == 0 or len(words) == 0:
            return 0.0
        
        # Факторы сложности
        avg_word_length = np.mean([len(word) for word in words])
        avg_sentence_length = len(words) / len(sentences)
        unique_word_ratio = len(set(words)) / len(words)
        
        # Комплексная оценка
        complexity = (avg_word_length * 0.3 + avg_sentence_length * 0.4 + unique_word_ratio * 0.3)
        return min(1.0, complexity / 10)  # Нормализация

class AIProviderManager:
    """Менеджер провайдеров ИИ"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Инициализация провайдеров"""
        # OpenAI
        if AIConfig.PROVIDERS[AIProvider.OPENAI]['api_key']:
            openai.api_key = AIConfig.PROVIDERS[AIProvider.OPENAI]['api_key']
            self.providers[AIProvider.OPENAI] = self._create_openai_provider()
        
        # Anthropic
        if AIConfig.PROVIDERS[AIProvider.ANTHROPIC]['api_key']:
            self.providers[AIProvider.ANTHROPIC] = self._create_anthropic_provider()
        
        # Google
        if AIConfig.PROVIDERS[AIProvider.GOOGLE]['api_key']:
            genai.configure(api_key=AIConfig.PROVIDERS[AIProvider.GOOGLE]['api_key'])
            self.providers[AIProvider.GOOGLE] = self._create_google_provider()
        
        # Local
        self.providers[AIProvider.LOCAL] = self._create_local_provider()
        
        # HuggingFace
        if AIConfig.PROVIDERS[AIProvider.HUGGINGFACE]['api_key']:
            self.providers[AIProvider.HUGGINGFACE] = self._create_huggingface_provider()
    
    def _create_openai_provider(self):
        """Создание провайдера OpenAI"""
        class OpenAIProvider:
            def __init__(self):
                self.client = openai.OpenAI()
            
            async def generate(self, request: AIRequest) -> AIResponse:
                start_time = time.time()
                
                try:
                    response = await self.client.chat.completions.create(
                        model=AIConfig.PROVIDERS[AIProvider.OPENAI]['default_model'],
                        messages=[{"role": "user", "content": request.prompt}],
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                    
                    content = response.choices[0].message.content
                    tokens_used = response.usage.total_tokens
                    processing_time = time.time() - start_time
                    
                    return AIResponse(
                        content=content,
                        provider=AIProvider.OPENAI,
                        model=AIConfig.PROVIDERS[AIProvider.OPENAI]['default_model'],
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        quality_score=0.9,  # Высокое качество
                        cost=tokens_used * AIConfig.PROVIDERS[AIProvider.OPENAI]['cost_per_token'],
                        timestamp=datetime.utcnow(),
                        metadata={'response_id': response.id}
                    )
                except Exception as e:
                    raise Exception(f"OpenAI error: {str(e)}")
        
        return OpenAIProvider()
    
    def _create_anthropic_provider(self):
        """Создание провайдера Anthropic"""
        class AnthropicProvider:
            def __init__(self):
                self.client = anthropic.Anthropic()
            
            async def generate(self, request: AIRequest) -> AIResponse:
                start_time = time.time()
                
                try:
                    response = await self.client.messages.create(
                        model=AIConfig.PROVIDERS[AIProvider.ANTHROPIC]['default_model'],
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        messages=[{"role": "user", "content": request.prompt}]
                    )
                    
                    content = response.content[0].text
                    tokens_used = response.usage.input_tokens + response.usage.output_tokens
                    processing_time = time.time() - start_time
                    
                    return AIResponse(
                        content=content,
                        provider=AIProvider.ANTHROPIC,
                        model=AIConfig.PROVIDERS[AIProvider.ANTHROPIC]['default_model'],
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        quality_score=0.95,  # Очень высокое качество
                        cost=tokens_used * AIConfig.PROVIDERS[AIProvider.ANTHROPIC]['cost_per_token'],
                        timestamp=datetime.utcnow(),
                        metadata={'response_id': response.id}
                    )
                except Exception as e:
                    raise Exception(f"Anthropic error: {str(e)}")
        
        return AnthropicProvider()
    
    def _create_google_provider(self):
        """Создание провайдера Google"""
        class GoogleProvider:
            def __init__(self):
                self.model = genai.GenerativeModel(AIConfig.PROVIDERS[AIProvider.GOOGLE]['default_model'])
            
            async def generate(self, request: AIRequest) -> AIResponse:
                start_time = time.time()
                
                try:
                    response = await self.model.generate_content_async(
                        request.prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=request.max_tokens,
                            temperature=request.temperature
                        )
                    )
                    
                    content = response.text
                    tokens_used = len(request.prompt.split()) + len(content.split())
                    processing_time = time.time() - start_time
                    
                    return AIResponse(
                        content=content,
                        provider=AIProvider.GOOGLE,
                        model=AIConfig.PROVIDERS[AIProvider.GOOGLE]['default_model'],
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        quality_score=0.85,  # Хорошее качество
                        cost=tokens_used * AIConfig.PROVIDERS[AIProvider.GOOGLE]['cost_per_token'],
                        timestamp=datetime.utcnow(),
                        metadata={'response_id': response.candidates[0].finish_reason}
                    )
                except Exception as e:
                    raise Exception(f"Google error: {str(e)}")
        
        return GoogleProvider()
    
    def _create_local_provider(self):
        """Создание локального провайдера"""
        class LocalProvider:
            def __init__(self):
                self.model = None
                self.tokenizer = None
                self._load_model()
            
            def _load_model(self):
                """Загрузка локальной модели"""
                try:
                    # Загрузка модели HuggingFace
                    model_name = "microsoft/DialoGPT-medium"
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModel.from_pretrained(model_name)
                except Exception as e:
                    print(f"Failed to load local model: {e}")
            
            async def generate(self, request: AIRequest) -> AIResponse:
                start_time = time.time()
                
                try:
                    if self.model is None:
                        # Fallback к простому генератору
                        content = self._simple_generate(request.prompt)
                    else:
                        content = self._model_generate(request.prompt)
                    
                    tokens_used = len(request.prompt.split()) + len(content.split())
                    processing_time = time.time() - start_time
                    
                    return AIResponse(
                        content=content,
                        provider=AIProvider.LOCAL,
                        model=AIConfig.PROVIDERS[AIProvider.LOCAL]['default_model'],
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        quality_score=0.6,  # Среднее качество
                        cost=0.0,  # Бесплатно
                        timestamp=datetime.utcnow(),
                        metadata={'model_type': 'local'}
                    )
                except Exception as e:
                    raise Exception(f"Local model error: {str(e)}")
            
            def _simple_generate(self, prompt: str) -> str:
                """Простая генерация текста"""
                # Базовые шаблоны ответов
                templates = {
                    'title': ['Интересная статья о', 'Подробный анализ', 'Новое исследование'],
                    'content': ['В этой статье мы рассмотрим', 'Важно отметить', 'Стоит подчеркнуть'],
                    'comment': ['Интересная точка зрения', 'Согласен с автором', 'Хорошая статья']
                }
                
                # Определение типа контента
                content_type = 'content'
                if 'заголовок' in prompt.lower() or 'title' in prompt.lower():
                    content_type = 'title'
                elif 'комментарий' in prompt.lower() or 'comment' in prompt.lower():
                    content_type = 'comment'
                
                template = templates[content_type][0]
                return f"{template} {prompt[:50]}..."
            
            def _model_generate(self, prompt: str) -> str:
                """Генерация с помощью модели"""
                inputs = self.tokenizer.encode(prompt, return_tensors='pt')
                with torch.no_grad():
                    outputs = self.model.generate(inputs, max_length=100, num_return_sequences=1)
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return LocalProvider()
    
    def _create_huggingface_provider(self):
        """Создание провайдера HuggingFace"""
        class HuggingFaceProvider:
            def __init__(self):
                self.pipeline = None
                self._load_pipeline()
            
            def _load_pipeline(self):
                """Загрузка пайплайна"""
                try:
                    self.pipeline = pipeline(
                        "text-generation",
                        model="microsoft/DialoGPT-medium",
                        tokenizer="microsoft/DialoGPT-medium"
                    )
                except Exception as e:
                    print(f"Failed to load HuggingFace pipeline: {e}")
            
            async def generate(self, request: AIRequest) -> AIResponse:
                start_time = time.time()
                
                try:
                    if self.pipeline is None:
                        content = f"Generated content for: {request.prompt[:100]}..."
                    else:
                        result = self.pipeline(
                            request.prompt,
                            max_length=request.max_tokens,
                            temperature=request.temperature,
                            do_sample=True
                        )
                        content = result[0]['generated_text']
                    
                    tokens_used = len(request.prompt.split()) + len(content.split())
                    processing_time = time.time() - start_time
                    
                    return AIResponse(
                        content=content,
                        provider=AIProvider.HUGGINGFACE,
                        model=AIConfig.PROVIDERS[AIProvider.HUGGINGFACE]['default_model'],
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        quality_score=0.7,  # Хорошее качество
                        cost=tokens_used * AIConfig.PROVIDERS[AIProvider.HUGGINGFACE]['cost_per_token'],
                        timestamp=datetime.utcnow(),
                        metadata={'model_type': 'huggingface'}
                    )
                except Exception as e:
                    raise Exception(f"HuggingFace error: {str(e)}")
        
        return HuggingFaceProvider()
    
    async def generate_content(self, request: AIRequest) -> AIResponse:
        """Генерация контента"""
        provider = self.providers.get(request.provider)
        if not provider:
            raise Exception(f"Provider {request.provider.value} not available")
        
        return await provider.generate(request)

class PerfectAIContentGenerator:
    """Идеальный генератор ИИ контента"""
    
    def __init__(self):
        self.provider_manager = AIProviderManager()
        self.cache = AICache()
        self.monitor = AIMonitor()
        self.content_analyzer = ContentAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Настройка логирования
        logging.basicConfig(level=AIConfig.LOG_LEVEL)
    
    async def generate_content(self, request: AIRequest) -> AIResponse:
        """Генерация контента с кэшированием и мониторингом"""
        # Проверка кэша
        cached_response = self.cache.get(request)
        if cached_response:
            self.logger.info(f"Cache hit for request: {request.content_type.value}")
            return cached_response
        
        # Генерация контента
        try:
            response = await self.provider_manager.generate_content(request)
            
            # Анализ качества
            analysis = self.content_analyzer.analyze_text(response.content)
            response.quality_score = self._calculate_quality_score(analysis)
            
            # Проверка качества
            if response.quality_score < AIConfig.QUALITY_THRESHOLD:
                self.logger.warning(f"Low quality content generated: {response.quality_score}")
                # Попробовать другой провайдер
                response = await self._try_alternative_provider(request)
            
            # Сохранение в кэш
            self.cache.set(request, response)
            
            # Логирование
            self.monitor.log_request(request, response, True)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            self.monitor.log_error(e, request)
            self.monitor.log_request(request, None, False)
            raise
    
    async def _try_alternative_provider(self, request: AIRequest) -> AIResponse:
        """Попытка генерации с альтернативным провайдером"""
        available_providers = [p for p in AIProvider if p in self.provider_manager.providers]
        
        for provider in available_providers:
            if provider != request.provider:
                try:
                    request.provider = provider
                    response = await self.provider_manager.generate_content(request)
                    
                    # Анализ качества
                    analysis = self.content_analyzer.analyze_text(response.content)
                    response.quality_score = self._calculate_quality_score(analysis)
                    
                    if response.quality_score >= AIConfig.QUALITY_THRESHOLD:
                        return response
                        
                except Exception as e:
                    self.logger.warning(f"Alternative provider {provider.value} failed: {str(e)}")
                    continue
        
        # Если все провайдеры не справились, возвращаем лучший результат
        raise Exception("All providers failed to generate quality content")
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Расчет оценки качества"""
        # Факторы качества
        readability_score = analysis['readability'] / 100
        complexity_score = analysis['complexity_score']
        keyword_diversity = len(analysis['keywords']) / 10
        topic_relevance = len(analysis['topics']) / 5
        
        # Взвешенная оценка
        quality_score = (
            readability_score * 0.3 +
            complexity_score * 0.2 +
            keyword_diversity * 0.3 +
            topic_relevance * 0.2
        )
        
        return min(1.0, quality_score)
    
    def generate_post_title(self, topic: str, language: str = 'ru') -> str:
        """Генерация заголовка поста"""
        prompt = f"Создай привлекательный заголовок для статьи на тему '{topic}' на {language} языке. Заголовок должен быть информативным и привлекательным."
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.TITLE,
            provider=AIProvider.OPENAI,
            max_tokens=100,
            temperature=0.8,
            language=language
        )
        
        # Синхронная генерация для простых запросов
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.generate_content(request))
            return response.content.strip()
        finally:
            loop.close()
    
    def generate_post_content(self, title: str, topic: str, length: int = 1000, language: str = 'ru') -> str:
        """Генерация контента поста"""
        prompt = f"Напиши подробную статью на тему '{topic}' с заголовком '{title}' на {language} языке. Длина статьи должна быть примерно {length} слов. Статья должна быть информативной, хорошо структурированной и интересной для чтения."
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.POST,
            provider=AIProvider.OPENAI,
            max_tokens=length,
            temperature=0.7,
            language=language
        )
        
        # Синхронная генерация
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.generate_content(request))
            return response.content.strip()
        finally:
            loop.close()
    
    def generate_post_excerpt(self, content: str, length: int = 200, language: str = 'ru') -> str:
        """Генерация краткого описания поста"""
        prompt = f"Создай краткое описание (примерно {length} символов) для следующей статьи на {language} языке:\n\n{content[:500]}..."
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.DESCRIPTION,
            provider=AIProvider.OPENAI,
            max_tokens=100,
            temperature=0.6,
            language=language
        )
        
        # Синхронная генерация
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.generate_content(request))
            return response.content.strip()
        finally:
            loop.close()
    
    def generate_tags(self, content: str, count: int = 5, language: str = 'ru') -> List[str]:
        """Генерация тегов для поста"""
        prompt = f"Создай {count} релевантных тегов для следующей статьи на {language} языке:\n\n{content[:500]}...\n\nТеги должны быть короткими и отражать основную тематику статьи."
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.TAG,
            provider=AIProvider.OPENAI,
            max_tokens=100,
            temperature=0.5,
            language=language
        )
        
        # Синхронная генерация
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.generate_content(request))
            # Парсинг тегов
            tags = [tag.strip() for tag in response.content.split(',')]
            return tags[:count]
        finally:
            loop.close()
    
    def generate_comment(self, post_content: str, language: str = 'ru') -> str:
        """Генерация комментария к посту"""
        prompt = f"Напиши интересный и конструктивный комментарий к следующей статье на {language} языке:\n\n{post_content[:300]}...\n\nКомментарий должен быть релевантным и добавлять ценность к обсуждению."
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.COMMENT,
            provider=AIProvider.OPENAI,
            max_tokens=200,
            temperature=0.7,
            language=language
        )
        
        # Синхронная генерация
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.generate_content(request))
            return response.content.strip()
        finally:
            loop.close()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Получение статистики системы"""
        return {
            'provider_stats': self.monitor.get_provider_stats(),
            'quality_stats': self.monitor.get_quality_stats(),
            'recent_errors': self.monitor.get_recent_errors(),
            'cache_size': len(self.cache.cache),
            'available_providers': list(self.provider_manager.providers.keys())
        }
    
    def optimize_performance(self):
        """Оптимизация производительности"""
        # Очистка кэша
        self.cache.cache.clear()
        self.cache.access_times.clear()
        
        # Очистка метрик
        self.monitor.metrics.clear()
        self.monitor.quality_scores.clear()
        self.monitor.error_logs.clear()
        
        self.logger.info("AI system performance optimized")

# Глобальный экземпляр идеального генератора ИИ
perfect_ai_generator = PerfectAIContentGenerator()

# Алиасы для совместимости
AIContentGenerator = PerfectAIContentGenerator

class ContentScheduler:
    """Планировщик контента"""
    
    def __init__(self):
        self.scheduled_tasks = []
        self.logger = logging.getLogger(__name__)
    
    def schedule_post_creation(self, topic: str, publish_time: datetime, user_id: int = None):
        """Планирование создания поста"""
        task = {
            'type': 'post',
            'topic': topic,
            'publish_time': publish_time,
            'user_id': user_id,
            'created_at': datetime.utcnow()
        }
        self.scheduled_tasks.append(task)
        self.logger.info(f"Scheduled post creation for topic: {topic}")
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Получение запланированных задач"""
        return self.scheduled_tasks

def populate_blog_with_ai_content(num_posts: int = 10, user_id: int = None):
    """Заполнение блога ИИ контентом"""
    generator = perfect_ai_generator
    
    # Темы для постов
    topics = [
        "Искусственный интеллект в современном мире",
        "Программирование на Python",
        "Веб-разработка с Flask",
        "Машинное обучение и нейронные сети",
        "Кибербезопасность и защита данных",
        "Облачные технологии и DevOps",
        "Мобильная разработка",
        "Анализ данных и визуализация",
        "Блокчейн и криптовалюты",
        "Интернет вещей (IoT)"
    ]
    
    created_posts = []
    
    for i in range(min(num_posts, len(topics))):
        try:
            topic = topics[i]
            
            # Генерация заголовка
            title = generator.generate_post_title(topic)
            
            # Генерация контента
            content = generator.generate_post_content(title, topic)
            
            # Генерация описания
            excerpt = generator.generate_post_excerpt(content)
            
            # Генерация тегов
            tags = generator.generate_tags(content)
            
            # Создание поста
            post = Post(
                title=title,
                content=content,
                excerpt=excerpt,
                author_id=user_id or 1,  # По умолчанию admin
                is_published=True,
                created_at=datetime.utcnow()
            )
            
            database.session.add(post)
            database.session.flush()  # Получаем ID поста
            
            # Добавление тегов
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    database.session.add(tag)
                    database.session.flush()
                
                post.tags.append(tag)
            
            created_posts.append(post)
            
        except Exception as e:
            generator.logger.error(f"Error creating post {i+1}: {str(e)}")
            continue
    
    try:
        database.session.commit()
        generator.logger.info(f"Successfully created {len(created_posts)} AI posts")
        return created_posts
    except Exception as e:
        database.session.rollback()
        generator.logger.error(f"Error committing posts: {str(e)}")
        raise