"""
Система снижения предвзятости в ИИ-контенте
Обнаружение и устранение различных видов предвзятости в генерируемом тексте
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter
import numpy as np

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class BiasType(Enum):
    """Типы предвзятости"""
    GENDER = "gender"
    RACIAL = "racial"
    RELIGIOUS = "religious"
    POLITICAL = "political"
    AGEISM = "ageism"
    CULTURAL = "cultural"
    SOCIOECONOMIC = "socioeconomic"
    CONFIRMATION = "confirmation"
    SELECTION = "selection"
    LINGUISTIC = "linguistic"

class BiasSeverity(Enum):
    """Уровень серьезности предвзятости"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BiasDetection:
    """Обнаруженная предвзятость"""
    bias_type: BiasType
    severity: BiasSeverity
    position: Tuple[int, int]
    original_text: str
    problematic_terms: List[str]
    suggested_alternatives: List[str]
    description: str
    confidence: float
    context: str

class GenderBiasDetector:
    """Детектор гендерной предвзятости"""
    
    def __init__(self):
        # Гендерно-специфичные слова и их нейтральные альтернативы
        self.gendered_terms = {
            # Профессии
            'программист': 'разработчик ПО',
            'врач': 'медицинский работник',
            'учитель': 'педагог',
            'секретарша': 'секретарь',
            'медсестра': 'медицинский работник',
            'стюардесса': 'бортпроводник',
            'официантка': 'официант',
            'уборщица': 'уборщик',
            
            # Описательные термины
            'мужественный': 'решительный',
            'женственный': 'элегантный',
            'мужской характер': 'сильный характер',
            'женская логика': 'интуитивное мышление',
            'мужская работа': 'физически сложная работа',
            'женская работа': 'работа, требующая внимания к деталям'
        }
        
        # Стереотипные ассоциации
        self.gender_stereotypes = {
            'мужчины': {
                'positive': ['сильные', 'решительные', 'логичные', 'лидеры'],
                'negative': ['агрессивные', 'бесчувственные', 'доминирующие'],
                'activities': ['работают', 'зарабатывают', 'руководят', 'принимают решения']
            },
            'женщины': {
                'positive': ['заботливые', 'эмоциональные', 'интуитивные'],
                'negative': ['слабые', 'нелогичные', 'истеричные', 'зависимые'],
                'activities': ['готовят', 'убирают', 'воспитывают', 'ухаживают']
            }
        }
        
        # Паттерны для обнаружения гендерных стереотипов
        self.stereotype_patterns = [
            (r'все мужчины\s+(\w+)', 'Обобщение о всех мужчинах'),
            (r'все женщины\s+(\w+)', 'Обобщение о всех женщинах'),
            (r'мужчины лучше\s+(\w+)', 'Утверждение о превосходстве мужчин'),
            (r'женщины лучше\s+(\w+)', 'Утверждение о превосходстве женщин'),
            (r'типично мужское\s+(\w+)', 'Гендерная типизация'),
            (r'типично женское\s+(\w+)', 'Гендерная типизация'),
        ]
    
    def detect_gender_bias(self, text: str) -> List[BiasDetection]:
        """Обнаружение гендерной предвзятости"""
        detections = []
        
        # Проверяем гендерно-специфичные термины
        for term, alternative in self.gendered_terms.items():
            for match in re.finditer(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
                detections.append(BiasDetection(
                    bias_type=BiasType.GENDER,
                    severity=BiasSeverity.MEDIUM,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    problematic_terms=[term],
                    suggested_alternatives=[alternative],
                    description=f"Гендерно-специфичный термин: '{term}'",
                    confidence=0.7,
                    context=self._get_context(text, match.start(), len(term))
                ))
        
        # Проверяем стереотипные паттерны
        for pattern, description in self.stereotype_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                detections.append(BiasDetection(
                    bias_type=BiasType.GENDER,
                    severity=BiasSeverity.HIGH,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    problematic_terms=[match.group(0)],
                    suggested_alternatives=["Избегайте обобщений"],
                    description=description,
                    confidence=0.8,
                    context=self._get_context(text, match.start(), match.end() - match.start())
                ))
        
        # Проверяем стереотипные ассоциации
        detections.extend(self._check_stereotype_associations(text))
        
        return detections
    
    def _check_stereotype_associations(self, text: str) -> List[BiasDetection]:
        """Проверка стереотипных ассоциаций"""
        detections = []
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            for gender, stereotypes in self.gender_stereotypes.items():
                if gender in sentence_lower:
                    # Проверяем наличие стереотипных характеристик
                    for category, traits in stereotypes.items():
                        for trait in traits:
                            if trait in sentence_lower:
                                position = text.find(sentence)
                                if position != -1:
                                    detections.append(BiasDetection(
                                        bias_type=BiasType.GENDER,
                                        severity=BiasSeverity.MEDIUM,
                                        position=(position, position + len(sentence)),
                                        original_text=sentence,
                                        problematic_terms=[f"{gender} + {trait}"],
                                        suggested_alternatives=["Используйте более нейтральные формулировки"],
                                        description=f"Стереотипная ассоциация: {gender} - {trait}",
                                        confidence=0.6,
                                        context=sentence
                                    ))
                                break
        
        return detections
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста"""
        start = max(0, position - 50)
        end = min(len(text), position + length + 50)
        return text[start:end]

class CulturalBiasDetector:
    """Детектор культурной предвзятости"""
    
    def __init__(self):
        # Культурно-специфичные термины и стереотипы
        self.cultural_stereotypes = {
            'западная культура': ['развитая', 'цивилизованная', 'прогрессивная'],
            'восточная культура': ['традиционная', 'консервативная', 'отсталая'],
            'европейцы': ['культурные', 'образованные', 'развитые'],
            'азиаты': ['трудолюбивые', 'дисциплинированные', 'закрытые'],
            'африканцы': ['примитивные', 'неразвитые', 'дикие'],
            'американцы': ['свободные', 'индивидуалистичные', 'материалистичные']
        }
        
        # Проблематичные обобщения
        self.problematic_generalizations = [
            r'все\s+(\w+цы|народы|нации)\s+(\w+)',
            r'(\w+цы|народы|нации)\s+всегда\s+(\w+)',
            r'типичный\s+(\w+ец|представитель)\s+(\w+)',
            r'(\w+)\s+по\s+природе\s+(\w+)'
        ]
    
    def detect_cultural_bias(self, text: str) -> List[BiasDetection]:
        """Обнаружение культурной предвзятости"""
        detections = []
        
        # Проверяем культурные стереотипы
        for culture, stereotypes in self.cultural_stereotypes.items():
            if culture in text.lower():
                for stereotype in stereotypes:
                    pattern = f"{culture}.*{stereotype}"
                    for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                        if match.end() - match.start() < 200:  # Ограничиваем длину совпадения
                            detections.append(BiasDetection(
                                bias_type=BiasType.CULTURAL,
                                severity=BiasSeverity.HIGH,
                                position=(match.start(), match.end()),
                                original_text=match.group(0),
                                problematic_terms=[f"{culture} - {stereotype}"],
                                suggested_alternatives=["Избегайте культурных стереотипов"],
                                description=f"Культурный стереотип: {culture} - {stereotype}",
                                confidence=0.7,
                                context=self._get_context(text, match.start(), match.end() - match.start())
                            ))
        
        # Проверяем проблематичные обобщения
        for pattern in self.problematic_generalizations:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                detections.append(BiasDetection(
                    bias_type=BiasType.CULTURAL,
                    severity=BiasSeverity.HIGH,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    problematic_terms=[match.group(0)],
                    suggested_alternatives=["Используйте более конкретные формулировки"],
                    description="Проблематичное обобщение о культуре/народе",
                    confidence=0.8,
                    context=self._get_context(text, match.start(), match.end() - match.start())
                ))
        
        return detections
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста"""
        start = max(0, position - 100)
        end = min(len(text), position + length + 100)
        return text[start:end]

class ConfirmationBiasDetector:
    """Детектор предвзятости подтверждения"""
    
    def __init__(self):
        # Индикаторы предвзятости подтверждения
        self.confirmation_indicators = [
            'очевидно, что',
            'всем известно, что',
            'не может быть сомнений',
            'безусловно',
            'несомненно',
            'само собой разумеется',
            'естественно, что',
            'логично предположить'
        ]
        
        # Паттерны односторонней подачи информации
        self.one_sided_patterns = [
            r'только\s+(\w+)\s+может',
            r'единственный\s+способ',
            r'нет\s+альтернативы',
            r'невозможно\s+иначе',
            r'все\s+эксперты\s+согласны'
        ]
    
    def detect_confirmation_bias(self, text: str) -> List[BiasDetection]:
        """Обнаружение предвзятости подтверждения"""
        detections = []
        
        # Проверяем индикаторы предвзятости
        for indicator in self.confirmation_indicators:
            for match in re.finditer(r'\b' + re.escape(indicator) + r'\b', text, re.IGNORECASE):
                detections.append(BiasDetection(
                    bias_type=BiasType.CONFIRMATION,
                    severity=BiasSeverity.MEDIUM,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    problematic_terms=[indicator],
                    suggested_alternatives=["Представьте доказательства", "Рассмотрите альтернативы"],
                    description=f"Индикатор предвзятости подтверждения: '{indicator}'",
                    confidence=0.6,
                    context=self._get_context(text, match.start(), len(indicator))
                ))
        
        # Проверяем односторонние утверждения
        for pattern in self.one_sided_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                detections.append(BiasDetection(
                    bias_type=BiasType.CONFIRMATION,
                    severity=BiasSeverity.HIGH,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    problematic_terms=[match.group(0)],
                    suggested_alternatives=["Рассмотрите альтернативные точки зрения"],
                    description="Одностороннее утверждение без рассмотрения альтернатив",
                    confidence=0.7,
                    context=self._get_context(text, match.start(), match.end() - match.start())
                ))
        
        # Проверяем баланс аргументов
        detections.extend(self._check_argument_balance(text))
        
        return detections
    
    def _check_argument_balance(self, text: str) -> List[BiasDetection]:
        """Проверка баланса аргументов"""
        detections = []
        
        # Ищем позитивные и негативные утверждения
        positive_indicators = ['преимущества', 'плюсы', 'польза', 'выгода', 'достоинства']
        negative_indicators = ['недостатки', 'минусы', 'вред', 'проблемы', 'недочеты']
        
        positive_count = sum(len(re.findall(r'\b' + indicator + r'\b', text, re.IGNORECASE)) 
                           for indicator in positive_indicators)
        negative_count = sum(len(re.findall(r'\b' + indicator + r'\b', text, re.IGNORECASE)) 
                           for indicator in negative_indicators)
        
        if positive_count > 0 and negative_count == 0:
            detections.append(BiasDetection(
                bias_type=BiasType.CONFIRMATION,
                severity=BiasSeverity.MEDIUM,
                position=(0, len(text)),
                original_text="Весь текст",
                problematic_terms=["односторонняя подача"],
                suggested_alternatives=["Рассмотрите также недостатки или ограничения"],
                description="Представлены только положительные аспекты",
                confidence=0.5,
                context="Анализ всего текста"
            ))
        elif negative_count > 0 and positive_count == 0:
            detections.append(BiasDetection(
                bias_type=BiasType.CONFIRMATION,
                severity=BiasSeverity.MEDIUM,
                position=(0, len(text)),
                original_text="Весь текст",
                problematic_terms=["односторонняя подача"],
                suggested_alternatives=["Рассмотрите также преимущества или возможности"],
                description="Представлены только отрицательные аспекты",
                confidence=0.5,
                context="Анализ всего текста"
            ))
        
        return detections
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста"""
        start = max(0, position - 50)
        end = min(len(text), position + length + 50)
        return text[start:end]

class LinguisticBiasDetector:
    """Детектор лингвистической предвзятости"""
    
    def __init__(self):
        # Эмоционально окрашенные слова
        self.emotional_words = {
            'positive': [
                'великолепный', 'потрясающий', 'невероятный', 'фантастический',
                'блестящий', 'превосходный', 'замечательный', 'удивительный'
            ],
            'negative': [
                'ужасный', 'отвратительный', 'кошмарный', 'катастрофический',
                'чудовищный', 'безобразный', 'омерзительный', 'жуткий'
            ]
        }
        
        # Слова, усиливающие категоричность
        self.intensifiers = [
            'абсолютно', 'совершенно', 'полностью', 'крайне',
            'чрезвычайно', 'исключительно', 'невероятно', 'чрезмерно'
        ]
        
        # Слова, указывающие на неопределенность
        self.hedging_words = [
            'возможно', 'вероятно', 'может быть', 'предположительно',
            'по-видимому', 'кажется', 'похоже', 'вероятно'
        ]
    
    def detect_linguistic_bias(self, text: str) -> List[BiasDetection]:
        """Обнаружение лингвистической предвзятости"""
        detections = []
        
        # Проверяем эмоционально окрашенные слова
        for emotion, words in self.emotional_words.items():
            for word in words:
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                    severity = BiasSeverity.HIGH if emotion == 'negative' else BiasSeverity.MEDIUM
                    detections.append(BiasDetection(
                        bias_type=BiasType.LINGUISTIC,
                        severity=severity,
                        position=(match.start(), match.end()),
                        original_text=match.group(0),
                        problematic_terms=[word],
                        suggested_alternatives=["Используйте более нейтральные термины"],
                        description=f"Эмоционально окрашенное слово ({emotion}): '{word}'",
                        confidence=0.7,
                        context=self._get_context(text, match.start(), len(word))
                    ))
        
        # Проверяем избыточные усилители
        intensifier_count = 0
        for intensifier in self.intensifiers:
            matches = list(re.finditer(r'\b' + re.escape(intensifier) + r'\b', text, re.IGNORECASE))
            intensifier_count += len(matches)
            
            for match in matches:
                if intensifier_count > 3:  # Слишком много усилителей
                    detections.append(BiasDetection(
                        bias_type=BiasType.LINGUISTIC,
                        severity=BiasSeverity.MEDIUM,
                        position=(match.start(), match.end()),
                        original_text=match.group(0),
                        problematic_terms=[intensifier],
                        suggested_alternatives=["Уменьшите количество усилителей"],
                        description=f"Избыточное использование усилителей: '{intensifier}'",
                        confidence=0.6,
                        context=self._get_context(text, match.start(), len(intensifier))
                    ))
        
        # Проверяем баланс определенности/неопределенности
        detections.extend(self._check_certainty_balance(text))
        
        return detections
    
    def _check_certainty_balance(self, text: str) -> List[BiasDetection]:
        """Проверка баланса определенности"""
        detections = []
        
        # Подсчитываем слова определенности и неопределенности
        hedging_count = sum(len(re.findall(r'\b' + word + r'\b', text, re.IGNORECASE)) 
                           for word in self.hedging_words)
        intensifier_count = sum(len(re.findall(r'\b' + word + r'\b', text, re.IGNORECASE)) 
                               for word in self.intensifiers)
        
        total_words = len(text.split())
        
        if total_words > 100:  # Анализируем только достаточно длинные тексты
            hedging_ratio = hedging_count / total_words
            intensifier_ratio = intensifier_count / total_words
            
            if intensifier_ratio > 0.02 and hedging_ratio < 0.005:  # Слишком категорично
                detections.append(BiasDetection(
                    bias_type=BiasType.LINGUISTIC,
                    severity=BiasSeverity.MEDIUM,
                    position=(0, len(text)),
                    original_text="Весь текст",
                    problematic_terms=["избыточная категоричность"],
                    suggested_alternatives=["Добавьте элементы неопределенности где уместно"],
                    description="Текст слишком категоричен, недостаточно нюансов",
                    confidence=0.5,
                    context="Анализ всего текста"
                ))
            elif hedging_ratio > 0.03 and intensifier_ratio < 0.005:  # Слишком неопределенно
                detections.append(BiasDetection(
                    bias_type=BiasType.LINGUISTIC,
                    severity=BiasSeverity.LOW,
                    position=(0, len(text)),
                    original_text="Весь текст",
                    problematic_terms=["избыточная неопределенность"],
                    suggested_alternatives=["Будьте более уверенными в утверждениях где это оправдано"],
                    description="Текст слишком неопределенный, недостаточно уверенности",
                    confidence=0.4,
                    context="Анализ всего текста"
                ))
        
        return detections
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста"""
        start = max(0, position - 50)
        end = min(len(text), position + length + 50)
        return text[start:end]

class BiasCorrector:
    """Система исправления предвзятости"""
    
    def __init__(self):
        # Словарь замен для устранения предвзятости
        self.bias_corrections = {
            # Гендерные замены
            'программист': 'разработчик',
            'секретарша': 'секретарь',
            'медсестра': 'медицинский работник',
            'все мужчины': 'многие мужчины',
            'все женщины': 'многие женщины',
            
            # Культурные замены
            'все американцы': 'многие американцы',
            'типичный русский': 'некоторые русские',
            
            # Лингвистические замены
            'абсолютно точно': 'весьма вероятно',
            'совершенно очевидно': 'представляется вероятным',
            'невозможно отрицать': 'трудно оспорить'
        }
    
    def correct_bias(self, text: str, detections: List[BiasDetection], 
                    min_confidence: float = 0.7) -> Tuple[str, List[BiasDetection]]:
        """Автоматическое исправление предвзятости"""
        corrected_text = text
        applied_corrections = []
        
        # Сортируем обнаружения по позиции (с конца, чтобы не сбить индексы)
        high_confidence_detections = [d for d in detections if d.confidence >= min_confidence]
        high_confidence_detections.sort(key=lambda x: x.position[0], reverse=True)
        
        for detection in high_confidence_detections:
            start, end = detection.position
            
            if start < len(corrected_text) and end <= len(corrected_text):
                original = corrected_text[start:end]
                
                # Ищем подходящую замену
                correction = self._find_correction(original, detection)
                
                if correction and correction != original:
                    corrected_text = (
                        corrected_text[:start] + 
                        correction + 
                        corrected_text[end:]
                    )
                    applied_corrections.append(detection)
        
        return corrected_text, applied_corrections
    
    def _find_correction(self, original_text: str, detection: BiasDetection) -> Optional[str]:
        """Поиск подходящего исправления"""
        # Проверяем прямые замены
        original_lower = original_text.lower()
        for biased_term, correction in self.bias_corrections.items():
            if biased_term.lower() in original_lower:
                return original_text.replace(biased_term, correction)
        
        # Используем предложенные альтернативы
        if detection.suggested_alternatives:
            return detection.suggested_alternatives[0]
        
        return None

class ComprehensiveBiasDetector:
    """Комплексная система обнаружения предвзятости"""
    
    def __init__(self):
        self.gender_detector = GenderBiasDetector()
        self.cultural_detector = CulturalBiasDetector()
        self.confirmation_detector = ConfirmationBiasDetector()
        self.linguistic_detector = LinguisticBiasDetector()
        self.bias_corrector = BiasCorrector()
        
        # Статистика обнаружения
        self.detection_stats = defaultdict(int)
    
    def detect_all_bias(self, text: str) -> List[BiasDetection]:
        """Комплексное обнаружение всех типов предвзятости"""
        all_detections = []
        
        try:
            # Гендерная предвзятость
            gender_detections = self.gender_detector.detect_gender_bias(text)
            all_detections.extend(gender_detections)
            self.detection_stats[BiasType.GENDER] += len(gender_detections)
            
            # Культурная предвзятость
            cultural_detections = self.cultural_detector.detect_cultural_bias(text)
            all_detections.extend(cultural_detections)
            self.detection_stats[BiasType.CULTURAL] += len(cultural_detections)
            
            # Предвзятость подтверждения
            confirmation_detections = self.confirmation_detector.detect_confirmation_bias(text)
            all_detections.extend(confirmation_detections)
            self.detection_stats[BiasType.CONFIRMATION] += len(confirmation_detections)
            
            # Лингвистическая предвзятость
            linguistic_detections = self.linguistic_detector.detect_linguistic_bias(text)
            all_detections.extend(linguistic_detections)
            self.detection_stats[BiasType.LINGUISTIC] += len(linguistic_detections)
            
        except Exception as e:
            logger.error(f"Ошибка при обнаружении предвзятости: {e}")
        
        # Сортируем по позиции
        all_detections.sort(key=lambda x: x.position[0])
        
        return all_detections
    
    def get_bias_report(self, text: str) -> Dict[str, Any]:
        """Генерация отчета о предвзятости"""
        detections = self.detect_all_bias(text)
        
        # Группируем по типам
        detections_by_type = defaultdict(list)
        for detection in detections:
            detections_by_type[detection.bias_type.value].append({
                'position': detection.position,
                'original': detection.original_text,
                'alternatives': detection.suggested_alternatives,
                'description': detection.description,
                'confidence': detection.confidence,
                'severity': detection.severity.value
            })
        
        # Вычисляем общий индекс предвзятости
        bias_score = self._calculate_bias_score(detections, len(text.split()))
        
        return {
            'bias_score': bias_score,
            'total_detections': len(detections),
            'detections_by_type': dict(detections_by_type),
            'severity_distribution': self._get_severity_distribution(detections),
            'recommendations': self._generate_bias_recommendations(detections, bias_score),
            'text_stats': {
                'word_count': len(text.split()),
                'sentence_count': len(sent_tokenize(text))
            }
        }
    
    def _calculate_bias_score(self, detections: List[BiasDetection], word_count: int) -> float:
        """Вычисление общего индекса предвзятости"""
        if not detections or word_count == 0:
            return 0.0
        
        # Взвешиваем по серьезности
        severity_weights = {
            BiasSeverity.LOW: 0.25,
            BiasSeverity.MEDIUM: 0.5,
            BiasSeverity.HIGH: 0.75,
            BiasSeverity.CRITICAL: 1.0
        }
        
        total_weight = sum(severity_weights[d.severity] * d.confidence for d in detections)
        
        # Нормализуем по количеству слов
        bias_score = min(1.0, total_weight / (word_count / 100))
        
        return bias_score
    
    def _get_severity_distribution(self, detections: List[BiasDetection]) -> Dict[str, int]:
        """Распределение по серьезности"""
        distribution = defaultdict(int)
        for detection in detections:
            distribution[detection.severity.value] += 1
        return dict(distribution)
    
    def _generate_bias_recommendations(self, detections: List[BiasDetection], 
                                     bias_score: float) -> List[str]:
        """Генерация рекомендаций по устранению предвзятости"""
        recommendations = []
        
        if bias_score > 0.7:
            recommendations.append("Высокий уровень предвзятости - требуется серьезная переработка текста")
        elif bias_score > 0.4:
            recommendations.append("Умеренный уровень предвзятости - рекомендуется исправление")
        elif bias_score > 0.2:
            recommendations.append("Низкий уровень предвзятости - незначительные улучшения")
        else:
            recommendations.append("Предвзятость практически отсутствует")
        
        # Специфичные рекомендации по типам
        bias_types = set(d.bias_type for d in detections)
        
        if BiasType.GENDER in bias_types:
            recommendations.append("Используйте гендерно-нейтральные формулировки")
        
        if BiasType.CULTURAL in bias_types:
            recommendations.append("Избегайте культурных стереотипов и обобщений")
        
        if BiasType.CONFIRMATION in bias_types:
            recommendations.append("Представьте альтернативные точки зрения")
        
        if BiasType.LINGUISTIC in bias_types:
            recommendations.append("Сбалансируйте эмоциональную окраску текста")
        
        return recommendations
    
    def auto_correct_bias(self, text: str, min_confidence: float = 0.7) -> Tuple[str, List[BiasDetection]]:
        """Автоматическое исправление предвзятости"""
        detections = self.detect_all_bias(text)
        return self.bias_corrector.correct_bias(text, detections, min_confidence)
    
    def get_detection_stats(self) -> Dict[str, int]:
        """Получение статистики обнаружения"""
        return dict(self.detection_stats)

# Глобальный экземпляр детектора предвзятости
bias_detector = ComprehensiveBiasDetector()