"""
Система интеграции с современными ИИ-моделями
Поддержка GPT-4, Claude, Gemini, локальных моделей и других провайдеров
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import pickle
from functools import wraps
import backoff

import openai
import anthropic
import google.generativeai as genai
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModel
import torch
import numpy as np

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Провайдеры ИИ"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    REPLICATE = "replicate"

class ModelType(Enum):
    """Типы моделей"""
    TEXT_GENERATION = "text_generation"
    TEXT_CLASSIFICATION = "text_classification"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    CODE_GENERATION = "code_generation"

@dataclass
class ModelConfig:
    """Конфигурация модели"""
    provider: AIProvider
    model_name: str
    model_type: ModelType
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_attempts: int = 3
    cache_enabled: bool = True
    cost_per_token: float = 0.0
    context_window: int = 4000

@dataclass
class GenerationRequest:
    """Запрос на генерацию"""
    prompt: str
    model_config: ModelConfig
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class GenerationResponse:
    """Ответ генерации"""
    content: str
    model_used: str
    tokens_used: int
    generation_time: float
    cost: float
    cached: bool = False
    metadata: Dict[str, Any] = None

class ModelCache:
    """Кэш для моделей и ответов"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.access_times = {}
    
    def _generate_key(self, request: GenerationRequest) -> str:
        """Генерация ключа кэша"""
        key_data = {
            'prompt': request.prompt,
            'model': request.model_config.model_name,
            'temperature': request.model_config.temperature,
            'max_tokens': request.model_config.max_tokens
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, request: GenerationRequest) -> Optional[GenerationResponse]:
        """Получение из кэша"""
        if not request.model_config.cache_enabled:
            return None
        
        key = self._generate_key(request)
        
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            
            # Проверяем TTL
            if datetime.now() - timestamp < self.ttl:
                self.access_times[key] = time.time()
                cached_data.cached = True
                return cached_data
            else:
                # Удаляем устаревший элемент
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
        
        return None
    
    def set(self, request: GenerationRequest, response: GenerationResponse):
        """Сохранение в кэш"""
        if not request.model_config.cache_enabled:
            return
        
        key = self._generate_key(request)
        
        # Очищаем кэш если он переполнен
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = (response, datetime.now())
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """Удаление самых старых элементов"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def clear(self):
        """Очистка кэша"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика кэша"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': 0.0,  # Будет вычисляться отдельно
            'oldest_entry': min(self.access_times.values()) if self.access_times else None,
            'newest_entry': max(self.access_times.values()) if self.access_times else None
        }

class OpenAIProvider:
    """Провайдер OpenAI"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.models = {
            'gpt-4': ModelConfig(
                provider=AIProvider.OPENAI,
                model_name='gpt-4',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.00003,
                context_window=8000
            ),
            'gpt-4-turbo': ModelConfig(
                provider=AIProvider.OPENAI,
                model_name='gpt-4-turbo',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.00001,
                context_window=128000
            ),
            'gpt-3.5-turbo': ModelConfig(
                provider=AIProvider.OPENAI,
                model_name='gpt-3.5-turbo',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.000002,
                context_window=16000
            )
        }
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Генерация текста"""
        start_time = time.time()
        
        try:
            model_config = self.models.get(request.model_config.model_name, request.model_config)
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            response = self.client.chat.completions.create(
                model=model_config.model_name,
                messages=messages,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                top_p=model_config.top_p,
                frequency_penalty=model_config.frequency_penalty,
                presence_penalty=model_config.presence_penalty
            )
            
            generation_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            cost = tokens_used * model_config.cost_per_token
            
            return GenerationResponse(
                content=response.choices[0].message.content,
                model_used=model_config.model_name,
                tokens_used=tokens_used,
                generation_time=generation_time,
                cost=cost,
                metadata={
                    'finish_reason': response.choices[0].finish_reason,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации OpenAI: {e}")
            raise

class AnthropicProvider:
    """Провайдер Anthropic"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.models = {
            'claude-3-opus': ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name='claude-3-opus-20240229',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.000015,
                context_window=200000
            ),
            'claude-3-sonnet': ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name='claude-3-sonnet-20240229',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.000003,
                context_window=200000
            ),
            'claude-3-haiku': ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name='claude-3-haiku-20240307',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.00000025,
                context_window=200000
            )
        }
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Генерация текста"""
        start_time = time.time()
        
        try:
            model_config = self.models.get(request.model_config.model_name, request.model_config)
            
            # Объединяем system prompt с основным prompt
            full_prompt = ""
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
            else:
                full_prompt = request.prompt
            
            response = self.client.messages.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            generation_time = time.time() - start_time
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = tokens_used * model_config.cost_per_token
            
            return GenerationResponse(
                content=response.content[0].text,
                model_used=model_config.model_name,
                tokens_used=tokens_used,
                generation_time=generation_time,
                cost=cost,
                metadata={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'stop_reason': response.stop_reason
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации Anthropic: {e}")
            raise

class GoogleProvider:
    """Провайдер Google Gemini"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.models = {
            'gemini-pro': ModelConfig(
                provider=AIProvider.GOOGLE,
                model_name='gemini-pro',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.0000005,
                context_window=32000
            ),
            'gemini-pro-vision': ModelConfig(
                provider=AIProvider.GOOGLE,
                model_name='gemini-pro-vision',
                model_type=ModelType.TEXT_GENERATION,
                max_tokens=4000,
                cost_per_token=0.0000005,
                context_window=16000
            )
        }
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Генерация текста"""
        start_time = time.time()
        
        try:
            model_config = self.models.get(request.model_config.model_name, request.model_config)
            model = genai.GenerativeModel(model_config.model_name)
            
            # Объединяем system prompt с основным prompt
            full_prompt = ""
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
            else:
                full_prompt = request.prompt
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=model_config.max_tokens,
                    temperature=model_config.temperature,
                    top_p=model_config.top_p
                )
            )
            
            generation_time = time.time() - start_time
            tokens_used = len(full_prompt.split()) + len(response.text.split())  # Приблизительно
            cost = tokens_used * model_config.cost_per_token
            
            return GenerationResponse(
                content=response.text,
                model_used=model_config.model_name,
                tokens_used=tokens_used,
                generation_time=generation_time,
                cost=cost,
                metadata={
                    'finish_reason': response.candidates[0].finish_reason if response.candidates else None,
                    'safety_ratings': [rating.category for rating in response.candidates[0].safety_ratings] if response.candidates else []
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации Google: {e}")
            raise

class LocalProvider:
    """Провайдер локальных моделей"""
    
    def __init__(self):
        self.models = {}
        self.pipelines = {}
        self._load_models()
    
    def _load_models(self):
        """Загрузка локальных моделей"""
        try:
            # Модель для генерации текста
            self.pipelines['text_generation'] = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Модель для анализа тональности
            self.pipelines['sentiment'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Модель для суммаризации
            self.pipelines['summarization'] = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Локальные модели загружены")
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить локальные модели: {e}")
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Генерация текста"""
        start_time = time.time()
        
        try:
            model_type = request.model_config.model_type
            
            if model_type == ModelType.TEXT_GENERATION:
                pipeline_name = 'text_generation'
            elif model_type == ModelType.SENTIMENT_ANALYSIS:
                pipeline_name = 'sentiment'
            elif model_type == ModelType.SUMMARIZATION:
                pipeline_name = 'summarization'
            else:
                raise ValueError(f"Неподдерживаемый тип модели: {model_type}")
            
            if pipeline_name not in self.pipelines:
                raise ValueError(f"Модель {pipeline_name} не загружена")
            
            pipeline = self.pipelines[pipeline_name]
            
            # Генерируем контент
            if model_type == ModelType.TEXT_GENERATION:
                result = pipeline(
                    request.prompt,
                    max_length=request.model_config.max_tokens,
                    temperature=request.model_config.temperature,
                    do_sample=True,
                    pad_token_id=pipeline.tokenizer.eos_token_id
                )
                content = result[0]['generated_text']
            elif model_type == ModelType.SENTIMENT_ANALYSIS:
                result = pipeline(request.prompt)
                content = f"Тональность: {result[0]['label']}, Уверенность: {result[0]['score']:.2f}"
            elif model_type == ModelType.SUMMARIZATION:
                result = pipeline(request.prompt, max_length=request.model_config.max_tokens)
                content = result[0]['summary_text']
            else:
                content = "Ошибка генерации"
            
            generation_time = time.time() - start_time
            tokens_used = len(content.split())
            cost = 0.0  # Локальные модели бесплатны
            
            return GenerationResponse(
                content=content,
                model_used=f"local_{model_type.value}",
                tokens_used=tokens_used,
                generation_time=generation_time,
                cost=cost,
                metadata={
                    'model_type': model_type.value,
                    'local_model': True
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации локальной модели: {e}")
            raise

class AIProviderManager:
    """Менеджер провайдеров ИИ"""
    
    def __init__(self):
        self.providers = {}
        self.cache = ModelCache()
        self.usage_stats = defaultdict(lambda: {
            'requests': 0,
            'tokens': 0,
            'cost': 0.0,
            'errors': 0,
            'avg_response_time': 0.0
        })
        self._init_providers()
    
    def _init_providers(self):
        """Инициализация провайдеров"""
        try:
            # OpenAI
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                self.providers[AIProvider.OPENAI] = OpenAIProvider(openai_key)
                logger.info("✅ OpenAI провайдер инициализирован")
            
            # Anthropic
            anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
            if anthropic_key:
                self.providers[AIProvider.ANTHROPIC] = AnthropicProvider(anthropic_key)
                logger.info("✅ Anthropic провайдер инициализирован")
            
            # Google
            google_key = os.environ.get('GOOGLE_API_KEY')
            if google_key:
                self.providers[AIProvider.GOOGLE] = GoogleProvider(google_key)
                logger.info("✅ Google провайдер инициализирован")
            
            # Локальные модели
            self.providers[AIProvider.LOCAL] = LocalProvider()
            logger.info("✅ Локальный провайдер инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации провайдеров: {e}")
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Генерация с помощью выбранного провайдера"""
        
        # Проверяем кэш
        cached_response = self.cache.get(request)
        if cached_response:
            return cached_response
        
        provider = self.providers.get(request.model_config.provider)
        if not provider:
            raise ValueError(f"Провайдер {request.model_config.provider} не найден")
        
        try:
            response = await provider.generate(request)
            
            # Сохраняем в кэш
            self.cache.set(request, response)
            
            # Обновляем статистику
            self._update_usage_stats(request.model_config.provider, response)
            
            return response
            
        except Exception as e:
            # Обновляем статистику ошибок
            self.usage_stats[request.model_config.provider]['errors'] += 1
            logger.error(f"Ошибка генерации через {request.model_config.provider}: {e}")
            raise
    
    def _update_usage_stats(self, provider: AIProvider, response: GenerationResponse):
        """Обновление статистики использования"""
        stats = self.usage_stats[provider]
        stats['requests'] += 1
        stats['tokens'] += response.tokens_used
        stats['cost'] += response.cost
        
        # Обновляем среднее время ответа
        if stats['requests'] == 1:
            stats['avg_response_time'] = response.generation_time
        else:
            stats['avg_response_time'] = (
                (stats['avg_response_time'] * (stats['requests'] - 1) + response.generation_time) 
                / stats['requests']
            )
    
    def get_available_models(self) -> Dict[AIProvider, List[str]]:
        """Получение доступных моделей"""
        available_models = {}
        
        for provider_type, provider in self.providers.items():
            if hasattr(provider, 'models'):
                available_models[provider_type] = list(provider.models.keys())
            else:
                available_models[provider_type] = ['default']
        
        return available_models
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Получение статистики использования"""
        return {
            'providers': dict(self.usage_stats),
            'cache_stats': self.cache.get_stats(),
            'total_requests': sum(stats['requests'] for stats in self.usage_stats.values()),
            'total_tokens': sum(stats['tokens'] for stats in self.usage_stats.values()),
            'total_cost': sum(stats['cost'] for stats in self.usage_stats.values())
        }
    
    def get_best_provider_for_task(self, task_type: str, budget_limit: float = None) -> AIProvider:
        """Выбор лучшего провайдера для задачи"""
        
        # Простая логика выбора провайдера
        if task_type == 'high_quality':
            if AIProvider.OPENAI in self.providers:
                return AIProvider.OPENAI
            elif AIProvider.ANTHROPIC in self.providers:
                return AIProvider.ANTHROPIC
        
        elif task_type == 'fast':
            if AIProvider.LOCAL in self.providers:
                return AIProvider.LOCAL
            elif AIProvider.GOOGLE in self.providers:
                return AIProvider.GOOGLE
        
        elif task_type == 'cheap':
            if AIProvider.LOCAL in self.providers:
                return AIProvider.LOCAL
            elif AIProvider.GOOGLE in self.providers:
                return AIProvider.GOOGLE
        
        # По умолчанию возвращаем первый доступный
        return next(iter(self.providers.keys()), AIProvider.LOCAL)
    
    def clear_cache(self):
        """Очистка кэша"""
        self.cache.clear()
    
    def get_provider_config(self, provider: AIProvider, model_name: str) -> Optional[ModelConfig]:
        """Получение конфигурации модели"""
        provider_instance = self.providers.get(provider)
        if provider_instance and hasattr(provider_instance, 'models'):
            return provider_instance.models.get(model_name)
        return None

# Глобальный экземпляр менеджера
ai_provider_manager = AIProviderManager()

# Удобные функции для использования
async def generate_with_ai(prompt: str, provider: str = "openai", 
                          model: str = "gpt-4", max_tokens: int = 2000,
                          temperature: float = 0.7, system_prompt: str = None) -> str:
    """Удобная функция для генерации текста"""
    
    provider_enum = AIProvider(provider)
    model_config = ModelConfig(
        provider=provider_enum,
        model_name=model,
        model_type=ModelType.TEXT_GENERATION,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    request = GenerationRequest(
        prompt=prompt,
        model_config=model_config,
        system_prompt=system_prompt
    )
    
    response = await ai_provider_manager.generate(request)
    return response.content

async def generate_content_variations(prompt: str, count: int = 3) -> List[str]:
    """Генерация вариаций контента"""
    variations = []
    
    for i in range(count):
        temperature = 0.7 + (i * 0.1)  # Разные температуры для разнообразия
        content = await generate_with_ai(prompt, temperature=temperature)
        variations.append(content)
    
    return variations

def get_ai_provider_stats() -> Dict[str, Any]:
    """Получение статистики провайдеров"""
    return ai_provider_manager.get_usage_stats()

def get_available_ai_models() -> Dict[str, List[str]]:
    """Получение доступных моделей"""
    models = ai_provider_manager.get_available_models()
    return {provider.value: model_list for provider, model_list in models.items()}