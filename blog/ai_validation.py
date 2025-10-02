"""
Система валидации и защиты ИИ-контента
Предотвращение галлюцинаций, проверка фактов и обеспечение качества
"""

import re
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib
import difflib
from collections import Counter

import openai
import nltk
from textstat import flesch_reading_ease, automated_readability_index
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Загружаем необходимые данные NLTK
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    """Результаты валидации"""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    NEEDS_CORRECTION = "needs_correction"

@dataclass
class ValidationReport:
    """Отчет о валидации контента"""
    result: ValidationResult
    confidence_score: float
    issues: List[str]
    suggestions: List[str]
    quality_metrics: Dict[str, float]
    safety_flags: List[str]
    fact_check_results: Dict[str, Any]
    timestamp: datetime

class FactChecker:
    """Система проверки фактов"""
    
    def __init__(self):
        self.fact_check_apis = {
            'wikipedia': self._check_wikipedia,
            'wikidata': self._check_wikidata,
            'factcheck_org': self._check_factcheck_org
        }
        self.cache = {}
        self.cache_ttl = 3600  # 1 час
    
    def check_facts(self, text: str, claims: List[str] = None) -> Dict[str, Any]:
        """Проверка фактов в тексте"""
        if not claims:
            claims = self._extract_claims(text)
        
        results = {
            'total_claims': len(claims),
            'verified_claims': 0,
            'disputed_claims': 0,
            'unverified_claims': 0,
            'claim_details': []
        }
        
        for claim in claims:
            claim_result = self._verify_claim(claim)
            results['claim_details'].append(claim_result)
            
            if claim_result['status'] == 'verified':
                results['verified_claims'] += 1
            elif claim_result['status'] == 'disputed':
                results['disputed_claims'] += 1
            else:
                results['unverified_claims'] += 1
        
        # Общая оценка достоверности
        if results['total_claims'] > 0:
            results['credibility_score'] = (
                results['verified_claims'] * 1.0 + 
                results['unverified_claims'] * 0.5
            ) / results['total_claims']
        else:
            results['credibility_score'] = 0.8  # Нейтральная оценка
        
        return results
    
    def _extract_claims(self, text: str) -> List[str]:
        """Извлечение утверждений из текста"""
        # Простое извлечение предложений с фактическими утверждениями
        sentences = nltk.sent_tokenize(text)
        claims = []
        
        # Паттерны для выявления фактических утверждений
        fact_patterns = [
            r'\d+%',  # Проценты
            r'\d+\s*(лет|года|год)',  # Годы
            r'исследования?\s+показывают?',  # Исследования
            r'согласно\s+данным',  # Ссылки на данные
            r'статистика\s+показывает',  # Статистика
            r'\d+\s*(млн|миллион|тысяч)',  # Числовые данные
        ]
        
        for sentence in sentences:
            for pattern in fact_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claims.append(sentence.strip())
                    break
        
        return claims[:10]  # Ограничиваем количество проверяемых утверждений
    
    def _verify_claim(self, claim: str) -> Dict[str, Any]:
        """Проверка отдельного утверждения"""
        claim_hash = hashlib.md5(claim.encode()).hexdigest()
        
        # Проверяем кеш
        if claim_hash in self.cache:
            cache_entry = self.cache[claim_hash]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                return cache_entry['result']
        
        result = {
            'claim': claim,
            'status': 'unverified',
            'confidence': 0.5,
            'sources': [],
            'evidence': []
        }
        
        # Проверяем через различные источники
        for source_name, check_func in self.fact_check_apis.items():
            try:
                source_result = check_func(claim)
                if source_result:
                    result['sources'].append(source_name)
                    result['evidence'].extend(source_result.get('evidence', []))
                    
                    # Обновляем статус на основе результатов
                    if source_result.get('verified', False):
                        result['status'] = 'verified'
                        result['confidence'] = max(result['confidence'], 0.8)
                    elif source_result.get('disputed', False):
                        result['status'] = 'disputed'
                        result['confidence'] = min(result['confidence'], 0.3)
                        
            except Exception as e:
                logger.warning(f"Error checking claim with {source_name}: {e}")
        
        # Кешируем результат
        self.cache[claim_hash] = {
            'result': result,
            'timestamp': time.time()
        }
        
        return result
    
    def _check_wikipedia(self, claim: str) -> Optional[Dict]:
        """Проверка через Wikipedia API"""
        try:
            # Извлекаем ключевые слова из утверждения
            keywords = self._extract_keywords(claim)
            if not keywords:
                return None
            
            # Поиск в Wikipedia
            search_url = "https://ru.wikipedia.org/api/rest_v1/page/summary/"
            for keyword in keywords[:3]:  # Проверяем только первые 3 ключевых слова
                try:
                    response = requests.get(f"{search_url}{keyword}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'extract' in data:
                            # Простая проверка на совпадение контекста
                            similarity = self._calculate_text_similarity(claim, data['extract'])
                            if similarity > 0.3:
                                return {
                                    'verified': True,
                                    'evidence': [data['extract'][:200]],
                                    'source_url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
                                }
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia fact check error: {e}")
            return None
    
    def _check_wikidata(self, claim: str) -> Optional[Dict]:
        """Проверка через Wikidata"""
        # Упрощенная реализация - в реальности нужен более сложный запрос
        return None
    
    def _check_factcheck_org(self, claim: str) -> Optional[Dict]:
        """Проверка через fact-checking сайты"""
        # Заглушка для интеграции с fact-checking API
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Простое извлечение существительных
        try:
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            keywords = [word for word, pos in pos_tags if pos.startswith('NN') and len(word) > 3]
            return keywords[:5]
        except:
            return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Вычисление схожести текстов"""
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0

class HallucinationDetector:
    """Детектор галлюцинаций в ИИ-контенте"""
    
    def __init__(self):
        self.suspicious_patterns = [
            # Слишком конкретные данные без источников
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # Точные даты
            r'\d+\,\d+\,\d+',  # Точные числа с запятыми
            r'согласно исследованию от \d+ года',  # Ссылки на несуществующие исследования
            
            # Противоречивые утверждения
            r'всегда.*никогда',
            r'все.*никто',
            r'невозможно.*возможно',
            
            # Слишком категоричные утверждения
            r'абсолютно все',
            r'никто никогда',
            r'всегда и везде',
            r'на 100% доказано',
        ]
        
        self.credibility_indicators = [
            'исследования показывают',
            'по данным',
            'согласно статистике',
            'эксперты отмечают',
            'анализ показал'
        ]
    
    def detect_hallucinations(self, text: str) -> Dict[str, Any]:
        """Обнаружение потенциальных галлюцинаций"""
        issues = []
        confidence_score = 1.0
        
        # Проверка на подозрительные паттерны
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append(f"Подозрительный паттерн: {pattern} (найдено: {len(matches)})")
                confidence_score -= 0.1
        
        # Проверка на противоречия
        contradictions = self._find_contradictions(text)
        if contradictions:
            issues.extend([f"Противоречие: {c}" for c in contradictions])
            confidence_score -= 0.2 * len(contradictions)
        
        # Проверка на избыточную конкретность
        specificity_score = self._check_excessive_specificity(text)
        if specificity_score > 0.7:
            issues.append("Избыточная конкретность без источников")
            confidence_score -= 0.15
        
        # Проверка на недостоверные источники
        fake_sources = self._detect_fake_sources(text)
        if fake_sources:
            issues.extend([f"Подозрительный источник: {s}" for s in fake_sources])
            confidence_score -= 0.3
        
        confidence_score = max(0.0, confidence_score)
        
        return {
            'hallucination_risk': 1.0 - confidence_score,
            'confidence_score': confidence_score,
            'issues': issues,
            'risk_level': self._get_risk_level(confidence_score)
        }
    
    def _find_contradictions(self, text: str) -> List[str]:
        """Поиск противоречий в тексте"""
        sentences = nltk.sent_tokenize(text)
        contradictions = []
        
        # Простая проверка на противоречивые утверждения
        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                similarity = difflib.SequenceMatcher(None, sent1.lower(), sent2.lower()).ratio()
                if 0.3 < similarity < 0.8:  # Похожие, но не идентичные предложения
                    # Проверяем на противоположные значения
                    if self._are_contradictory(sent1, sent2):
                        contradictions.append(f"{sent1[:50]}... vs {sent2[:50]}...")
        
        return contradictions[:3]  # Ограничиваем количество
    
    def _are_contradictory(self, sent1: str, sent2: str) -> bool:
        """Проверка на противоречивость двух предложений"""
        # Простая эвристика для обнаружения противоречий
        negative_words = ['не', 'нет', 'никогда', 'невозможно', 'отсутствует']
        positive_words = ['да', 'есть', 'всегда', 'возможно', 'присутствует']
        
        sent1_negative = any(word in sent1.lower() for word in negative_words)
        sent2_negative = any(word in sent2.lower() for word in negative_words)
        
        sent1_positive = any(word in sent1.lower() for word in positive_words)
        sent2_positive = any(word in sent2.lower() for word in positive_words)
        
        return (sent1_negative and sent2_positive) or (sent1_positive and sent2_negative)
    
    def _check_excessive_specificity(self, text: str) -> float:
        """Проверка на избыточную конкретность"""
        # Подсчет конкретных деталей
        specific_patterns = [
            r'\d+\.\d+%',  # Точные проценты
            r'\d{1,2}:\d{2}',  # Время
            r'\$\d+\,\d+',  # Точные суммы денег
            r'\d+ человек',  # Точное количество людей
        ]
        
        total_matches = 0
        for pattern in specific_patterns:
            total_matches += len(re.findall(pattern, text))
        
        # Нормализуем по длине текста
        words_count = len(text.split())
        if words_count == 0:
            return 0.0
        
        return min(1.0, total_matches / (words_count / 100))
    
    def _detect_fake_sources(self, text: str) -> List[str]:
        """Обнаружение поддельных источников"""
        fake_sources = []
        
        # Паттерны для поддельных источников
        fake_patterns = [
            r'исследование университета [А-Я][а-я]+',
            r'по данным компании [А-Я][а-я]+',
            r'согласно отчету [А-Я][а-я]+ \d{4}',
        ]
        
        for pattern in fake_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Простая проверка - если источник слишком общий
                if len(match.split()) < 4:
                    fake_sources.append(match)
        
        return fake_sources
    
    def _get_risk_level(self, confidence_score: float) -> str:
        """Определение уровня риска"""
        if confidence_score >= 0.8:
            return "low"
        elif confidence_score >= 0.6:
            return "medium"
        elif confidence_score >= 0.4:
            return "high"
        else:
            return "critical"

class ContentFilter:
    """Фильтр контента для обеспечения безопасности"""
    
    def __init__(self):
        # Загружаем модель для классификации токсичности
        try:
            self.toxicity_classifier = pipeline(
                "text-classification",
                model="martin-ha/toxic-comment-model",
                device=0 if torch.cuda.is_available() else -1
            )
        except:
            self.toxicity_classifier = None
            logger.warning("Toxicity classifier not available")
        
        # Списки запрещенных слов и фраз
        self.banned_words = [
            # Добавьте сюда запрещенные слова на русском языке
        ]
        
        self.sensitive_topics = [
            'политика', 'религия', 'экстремизм', 'насилие',
            'дискриминация', 'наркотики', 'оружие'
        ]
        
        # Паттерны для обнаружения проблемного контента
        self.harmful_patterns = [
            r'как сделать.*взрывчатку',
            r'инструкция.*изготовлению',
            r'способы.*навредить',
            r'методы.*обмана',
        ]
    
    def filter_content(self, text: str) -> Dict[str, Any]:
        """Фильтрация контента"""
        issues = []
        safety_score = 1.0
        flags = []
        
        # Проверка на токсичность
        if self.toxicity_classifier:
            try:
                toxicity_result = self.toxicity_classifier(text[:512])  # Ограничиваем длину
                if toxicity_result[0]['label'] == 'TOXIC' and toxicity_result[0]['score'] > 0.7:
                    issues.append("Обнаружен токсичный контент")
                    safety_score -= 0.5
                    flags.append("toxicity")
            except Exception as e:
                logger.warning(f"Toxicity check failed: {e}")
        
        # Проверка на запрещенные слова
        banned_found = [word for word in self.banned_words if word.lower() in text.lower()]
        if banned_found:
            issues.append(f"Найдены запрещенные слова: {', '.join(banned_found[:3])}")
            safety_score -= 0.3
            flags.append("banned_words")
        
        # Проверка на вредоносные паттерны
        for pattern in self.harmful_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Обнаружен вредоносный паттерн: {pattern}")
                safety_score -= 0.4
                flags.append("harmful_content")
        
        # Проверка на чувствительные темы
        sensitive_found = [topic for topic in self.sensitive_topics if topic in text.lower()]
        if sensitive_found:
            issues.append(f"Затронуты чувствительные темы: {', '.join(sensitive_found)}")
            safety_score -= 0.2
            flags.append("sensitive_topics")
        
        safety_score = max(0.0, safety_score)
        
        return {
            'safety_score': safety_score,
            'issues': issues,
            'flags': flags,
            'is_safe': safety_score >= 0.7,
            'risk_level': self._get_safety_risk_level(safety_score)
        }
    
    def _get_safety_risk_level(self, safety_score: float) -> str:
        """Определение уровня риска безопасности"""
        if safety_score >= 0.9:
            return "safe"
        elif safety_score >= 0.7:
            return "low_risk"
        elif safety_score >= 0.5:
            return "medium_risk"
        else:
            return "high_risk"

class QualityAssessment:
    """Система оценки качества контента"""
    
    def __init__(self):
        self.min_word_count = 100
        self.max_word_count = 5000
        self.ideal_sentence_length = 15
        self.max_sentence_length = 40
    
    def assess_quality(self, text: str) -> Dict[str, Any]:
        """Комплексная оценка качества контента"""
        metrics = {}
        issues = []
        suggestions = []
        
        # Базовые метрики
        word_count = len(text.split())
        sentence_count = len(nltk.sent_tokenize(text))
        
        metrics['word_count'] = word_count
        metrics['sentence_count'] = sentence_count
        metrics['avg_sentence_length'] = word_count / max(sentence_count, 1)
        
        # Проверка длины
        if word_count < self.min_word_count:
            issues.append(f"Текст слишком короткий ({word_count} слов)")
            suggestions.append(f"Добавьте больше содержания (минимум {self.min_word_count} слов)")
        elif word_count > self.max_word_count:
            issues.append(f"Текст слишком длинный ({word_count} слов)")
            suggestions.append(f"Сократите текст (максимум {self.max_word_count} слов)")
        
        # Читаемость
        try:
            readability_score = flesch_reading_ease(text)
            metrics['readability_score'] = readability_score
            
            if readability_score < 30:
                issues.append("Текст слишком сложен для чтения")
                suggestions.append("Упростите предложения и используйте более простые слова")
            elif readability_score > 90:
                issues.append("Текст может быть слишком простым")
                suggestions.append("Добавьте более сложные концепции и детали")
        except:
            metrics['readability_score'] = 50  # Средняя оценка
        
        # Структура
        structure_score = self._assess_structure(text)
        metrics['structure_score'] = structure_score
        
        if structure_score < 0.6:
            issues.append("Плохая структура текста")
            suggestions.append("Добавьте заголовки, списки и логические разделы")
        
        # Разнообразие лексики
        lexical_diversity = self._calculate_lexical_diversity(text)
        metrics['lexical_diversity'] = lexical_diversity
        
        if lexical_diversity < 0.4:
            issues.append("Низкое разнообразие лексики")
            suggestions.append("Используйте более разнообразные слова и синонимы")
        
        # Грамматические ошибки (упрощенная проверка)
        grammar_score = self._check_basic_grammar(text)
        metrics['grammar_score'] = grammar_score
        
        if grammar_score < 0.8:
            issues.append("Обнаружены возможные грамматические ошибки")
            suggestions.append("Проверьте грамматику и пунктуацию")
        
        # Общая оценка качества
        overall_quality = (
            min(1.0, word_count / 500) * 0.2 +  # Длина
            (metrics['readability_score'] / 100) * 0.3 +  # Читаемость
            structure_score * 0.2 +  # Структура
            lexical_diversity * 0.15 +  # Разнообразие
            grammar_score * 0.15  # Грамматика
        )
        
        metrics['overall_quality'] = overall_quality
        
        return {
            'quality_score': overall_quality,
            'metrics': metrics,
            'issues': issues,
            'suggestions': suggestions,
            'grade': self._get_quality_grade(overall_quality)
        }
    
    def _assess_structure(self, text: str) -> float:
        """Оценка структуры текста"""
        score = 0.0
        
        # Проверка на наличие заголовков
        if re.search(r'^#{1,6}\s+', text, re.MULTILINE):
            score += 0.3
        
        # Проверка на наличие списков
        if re.search(r'^\s*[-*+]\s+', text, re.MULTILINE) or re.search(r'^\s*\d+\.\s+', text, re.MULTILINE):
            score += 0.2
        
        # Проверка на абзацы
        paragraphs = text.split('\n\n')
        if len(paragraphs) >= 3:
            score += 0.3
        
        # Проверка на выделения
        if re.search(r'\*\*.*?\*\*', text) or re.search(r'\*.*?\*', text):
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_lexical_diversity(self, text: str) -> float:
        """Вычисление разнообразия лексики"""
        words = [word.lower() for word in re.findall(r'\b\w+\b', text) if len(word) > 3]
        if not words:
            return 0.0
        
        unique_words = set(words)
        return len(unique_words) / len(words)
    
    def _check_basic_grammar(self, text: str) -> float:
        """Базовая проверка грамматики"""
        issues = 0
        total_checks = 0
        
        # Проверка на повторяющиеся слова
        words = text.split()
        for i in range(len(words) - 1):
            if words[i].lower() == words[i + 1].lower():
                issues += 1
            total_checks += 1
        
        # Проверка на слишком длинные предложения
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            if len(sentence.split()) > self.max_sentence_length:
                issues += 1
            total_checks += 1
        
        if total_checks == 0:
            return 1.0
        
        return max(0.0, 1.0 - (issues / total_checks))
    
    def _get_quality_grade(self, score: float) -> str:
        """Получение оценки качества"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "satisfactory"
        elif score >= 0.6:
            return "needs_improvement"
        else:
            return "poor"

class AIContentValidator:
    """Основная система валидации ИИ-контента"""
    
    def __init__(self):
        self.fact_checker = FactChecker()
        self.hallucination_detector = HallucinationDetector()
        self.content_filter = ContentFilter()
        self.quality_assessor = QualityAssessment()
        
        # Пороговые значения для принятия решений
        self.thresholds = {
            'min_quality_score': 0.6,
            'max_hallucination_risk': 0.4,
            'min_safety_score': 0.7,
            'min_credibility_score': 0.5
        }
    
    def validate_content(self, text: str, title: str = "", category: str = "") -> ValidationReport:
        """Комплексная валидация контента"""
        start_time = time.time()
        
        # Проверка качества
        quality_result = self.quality_assessor.assess_quality(text)
        
        # Проверка на галлюцинации
        hallucination_result = self.hallucination_detector.detect_hallucinations(text)
        
        # Проверка безопасности
        safety_result = self.content_filter.filter_content(text)
        
        # Проверка фактов
        fact_check_result = self.fact_checker.check_facts(text)
        
        # Сбор всех проблем и предложений
        all_issues = []
        all_suggestions = []
        all_safety_flags = []
        
        all_issues.extend(quality_result.get('issues', []))
        all_issues.extend(hallucination_result.get('issues', []))
        all_issues.extend(safety_result.get('issues', []))
        
        all_suggestions.extend(quality_result.get('suggestions', []))
        all_safety_flags.extend(safety_result.get('flags', []))
        
        # Определение итогового результата
        result = self._determine_validation_result(
            quality_result, hallucination_result, safety_result, fact_check_result
        )
        
        # Вычисление общего показателя уверенности
        confidence_score = self._calculate_confidence_score(
            quality_result, hallucination_result, safety_result, fact_check_result
        )
        
        # Метрики качества
        quality_metrics = {
            'overall_quality': quality_result['quality_score'],
            'safety_score': safety_result['safety_score'],
            'hallucination_risk': hallucination_result['hallucination_risk'],
            'credibility_score': fact_check_result['credibility_score'],
            'processing_time': time.time() - start_time
        }
        
        return ValidationReport(
            result=result,
            confidence_score=confidence_score,
            issues=all_issues,
            suggestions=all_suggestions,
            quality_metrics=quality_metrics,
            safety_flags=all_safety_flags,
            fact_check_results=fact_check_result,
            timestamp=datetime.now()
        )
    
    def _determine_validation_result(self, quality_result, hallucination_result, 
                                   safety_result, fact_check_result) -> ValidationResult:
        """Определение итогового результата валидации"""
        
        # Критические проблемы безопасности
        if not safety_result['is_safe']:
            return ValidationResult.REJECTED
        
        # Высокий риск галлюцинаций
        if hallucination_result['hallucination_risk'] > self.thresholds['max_hallucination_risk']:
            return ValidationResult.NEEDS_CORRECTION
        
        # Низкое качество
        if quality_result['quality_score'] < self.thresholds['min_quality_score']:
            return ValidationResult.NEEDS_CORRECTION
        
        # Низкая достоверность фактов
        if fact_check_result['credibility_score'] < self.thresholds['min_credibility_score']:
            return ValidationResult.NEEDS_REVIEW
        
        # Если есть незначительные проблемы
        total_issues = len(quality_result.get('issues', [])) + len(hallucination_result.get('issues', []))
        if total_issues > 3:
            return ValidationResult.NEEDS_REVIEW
        
        return ValidationResult.APPROVED
    
    def _calculate_confidence_score(self, quality_result, hallucination_result, 
                                  safety_result, fact_check_result) -> float:
        """Вычисление общего показателя уверенности"""
        scores = [
            quality_result['quality_score'] * 0.3,
            safety_result['safety_score'] * 0.25,
            (1.0 - hallucination_result['hallucination_risk']) * 0.25,
            fact_check_result['credibility_score'] * 0.2
        ]
        
        return sum(scores)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Получение статистики валидации"""
        return {
            'thresholds': self.thresholds,
            'fact_checker_cache_size': len(self.fact_checker.cache),
            'validation_components': [
                'quality_assessment',
                'hallucination_detection', 
                'content_filtering',
                'fact_checking'
            ]
        }

# Глобальный экземпляр валидатора
ai_content_validator = AIContentValidator()