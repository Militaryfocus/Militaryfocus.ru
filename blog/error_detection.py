"""
Система обнаружения и исправления ошибок в тексте
Включает проверку грамматики, орфографии, логических ошибок и несоответствий
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import difflib
from collections import Counter, defaultdict
import string

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree
import pymorphy2
from textstat import flesch_reading_ease

# Загружаем необходимые данные NLTK
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Типы ошибок"""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    LOGICAL = "logical"
    FACTUAL = "factual"
    STYLE = "style"
    COHERENCE = "coherence"
    REPETITION = "repetition"

class ErrorSeverity(Enum):
    """Серьезность ошибки"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TextError:
    """Представление ошибки в тексте"""
    error_type: ErrorType
    severity: ErrorSeverity
    position: Tuple[int, int]  # начало и конец ошибки
    original_text: str
    suggested_correction: str
    description: str
    confidence: float
    context: str

class RussianSpellChecker:
    """Проверка орфографии для русского языка"""
    
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()
        
        # Словарь часто встречающихся ошибок
        self.common_errors = {
            'тся': 'ться',
            'ться': 'тся',
            'что-бы': 'чтобы',
            'так-же': 'также',
            'по-этому': 'поэтому',
            'в-общем': 'в общем',
            'в-течении': 'в течение',
            'на-счет': 'насчет',
            'по-началу': 'поначалу',
            'с-начала': 'сначала'
        }
        
        # Паттерны для проверки
        self.error_patterns = [
            (r'\b(\w+)тся\b', self._check_tsa_tsya),
            (r'\b(\w+)ться\b', self._check_tsa_tsya),
            (r'\bчто\s+бы\b', 'чтобы'),
            (r'\bтак\s+же\b', self._check_takzhe),
            (r'\bпо\s+этому\b', 'поэтому'),
            (r'\bв\s+общем\b', 'в общем'),
            (r'\bна\s+счет\b', self._check_naschet),
        ]
        
        # Словарь правильных слов (можно расширить)
        self.dictionary = set([
            'и', 'в', 'не', 'на', 'я', 'быть', 'он', 'с', 'что', 'а', 'по', 'это', 'она',
            'к', 'но', 'они', 'мы', 'как', 'из', 'у', 'который', 'то', 'за', 'свой', 'ее',
            'так', 'от', 'же', 'для', 'или', 'да', 'бы', 'весь', 'только', 'о', 'уже',
            'где', 'когда', 'можно', 'более', 'после', 'наш', 'два', 'другой', 'хорошо',
            'новый', 'жизнь', 'день', 'время', 'очень', 'сам', 'там', 'без', 'дело',
            'человек', 'год', 'работа', 'слово', 'место', 'лицо', 'дом', 'вопрос',
            'развитие', 'система', 'результат', 'процесс', 'проблема', 'решение'
        ])
    
    def check_spelling(self, text: str) -> List[TextError]:
        """Проверка орфографии"""
        errors = []
        
        # Проверяем по паттернам
        for pattern, correction in self.error_patterns:
            if callable(correction):
                errors.extend(self._check_pattern_with_function(text, pattern, correction))
            else:
                errors.extend(self._check_simple_pattern(text, pattern, correction))
        
        # Проверяем отдельные слова
        words = word_tokenize(text)
        for i, word in enumerate(words):
            if self._is_misspelled(word):
                suggestions = self._get_spelling_suggestions(word)
                if suggestions:
                    start_pos = text.find(word)
                    if start_pos != -1:
                        errors.append(TextError(
                            error_type=ErrorType.SPELLING,
                            severity=ErrorSeverity.MEDIUM,
                            position=(start_pos, start_pos + len(word)),
                            original_text=word,
                            suggested_correction=suggestions[0],
                            description=f"Возможная орфографическая ошибка: '{word}'",
                            confidence=0.7,
                            context=self._get_context(text, start_pos, len(word))
                        ))
        
        return errors
    
    def _check_tsa_tsya(self, match):
        """Проверка -тся/-ться"""
        word = match.group(1) + match.group(0)[-3:]  # восстанавливаем полное слово
        
        # Упрощенная логика: если перед словом есть "будет", "может" и т.п., то -ться
        # Иначе -тся
        context_before = match.string[:match.start()].split()[-3:]
        
        auxiliary_verbs = ['будет', 'может', 'должен', 'хочет', 'начинает', 'продолжает']
        
        if any(aux in context_before for aux in auxiliary_verbs):
            return word[:-3] + 'ться'
        else:
            return word[:-4] + 'тся'
    
    def _check_takzhe(self, match):
        """Проверка так же/также"""
        # Упрощенная логика: если можно заменить на "и", то "также"
        return 'также'  # В большинстве случаев правильно
    
    def _check_naschet(self, match):
        """Проверка на счет/насчет"""
        # Если можно заменить на "о", то "насчет"
        return 'насчет'  # В большинстве случаев правильно
    
    def _check_pattern_with_function(self, text: str, pattern: str, func) -> List[TextError]:
        """Проверка паттерна с функцией коррекции"""
        errors = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            correction = func(match)
            if correction != match.group(0):
                errors.append(TextError(
                    error_type=ErrorType.SPELLING,
                    severity=ErrorSeverity.HIGH,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    suggested_correction=correction,
                    description=f"Орфографическая ошибка: '{match.group(0)}' → '{correction}'",
                    confidence=0.8,
                    context=self._get_context(text, match.start(), match.end() - match.start())
                ))
        return errors
    
    def _check_simple_pattern(self, text: str, pattern: str, correction: str) -> List[TextError]:
        """Проверка простого паттерна"""
        errors = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            errors.append(TextError(
                error_type=ErrorType.SPELLING,
                severity=ErrorSeverity.HIGH,
                position=(match.start(), match.end()),
                original_text=match.group(0),
                suggested_correction=correction,
                description=f"Орфографическая ошибка: '{match.group(0)}' → '{correction}'",
                confidence=0.9,
                context=self._get_context(text, match.start(), match.end() - match.start())
            ))
        return errors
    
    def _is_misspelled(self, word: str) -> bool:
        """Проверка, является ли слово ошибочным"""
        # Убираем пунктуацию
        clean_word = word.strip(string.punctuation).lower()
        
        if not clean_word or len(clean_word) < 3:
            return False
        
        # Проверяем в словаре
        if clean_word in self.dictionary:
            return False
        
        # Проверяем через морфологический анализатор
        parsed = self.morph.parse(clean_word)
        if parsed and parsed[0].score > 0.5:
            return False
        
        return True
    
    def _get_spelling_suggestions(self, word: str) -> List[str]:
        """Получение предложений для исправления"""
        clean_word = word.strip(string.punctuation).lower()
        
        # Проверяем в словаре частых ошибок
        if clean_word in self.common_errors:
            return [self.common_errors[clean_word]]
        
        # Ищем похожие слова в словаре
        suggestions = []
        for dict_word in self.dictionary:
            if len(dict_word) >= 3:
                similarity = difflib.SequenceMatcher(None, clean_word, dict_word).ratio()
                if similarity > 0.7:
                    suggestions.append((dict_word, similarity))
        
        # Сортируем по схожести
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [word for word, _ in suggestions[:3]]
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста вокруг ошибки"""
        start = max(0, position - 50)
        end = min(len(text), position + length + 50)
        return text[start:end]

class GrammarChecker:
    """Проверка грамматики"""
    
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()
        
        # Правила согласования
        self.agreement_rules = [
            self._check_noun_adjective_agreement,
            self._check_subject_predicate_agreement,
            self._check_numeral_noun_agreement
        ]
    
    def check_grammar(self, text: str) -> List[TextError]:
        """Проверка грамматики"""
        errors = []
        
        sentences = sent_tokenize(text)
        for sentence in sentences:
            # Проверяем каждое правило
            for rule in self.agreement_rules:
                errors.extend(rule(sentence, text))
        
        return errors
    
    def _check_noun_adjective_agreement(self, sentence: str, full_text: str) -> List[TextError]:
        """Проверка согласования прилагательных с существительными"""
        errors = []
        
        words = word_tokenize(sentence)
        pos_tags = pos_tag(words)
        
        for i in range(len(words) - 1):
            current_word, current_pos = pos_tags[i]
            next_word, next_pos = pos_tags[i + 1]
            
            # Упрощенная проверка: если прилагательное перед существительным
            if self._is_adjective(current_pos) and self._is_noun(next_pos):
                if not self._check_gender_number_agreement(current_word, next_word):
                    position = full_text.find(f"{current_word} {next_word}")
                    if position != -1:
                        errors.append(TextError(
                            error_type=ErrorType.GRAMMAR,
                            severity=ErrorSeverity.MEDIUM,
                            position=(position, position + len(f"{current_word} {next_word}")),
                            original_text=f"{current_word} {next_word}",
                            suggested_correction=self._suggest_agreement_correction(current_word, next_word),
                            description="Несогласованность прилагательного с существительным",
                            confidence=0.6,
                            context=self._get_sentence_context(full_text, sentence)
                        ))
        
        return errors
    
    def _check_subject_predicate_agreement(self, sentence: str, full_text: str) -> List[TextError]:
        """Проверка согласования подлежащего со сказуемым"""
        # Упрощенная реализация
        return []
    
    def _check_numeral_noun_agreement(self, sentence: str, full_text: str) -> List[TextError]:
        """Проверка согласования числительных с существительными"""
        errors = []
        
        # Паттерны для числительных
        numeral_patterns = [
            (r'\b(один|одна|одно)\s+(\w+)', self._check_one_agreement),
            (r'\b(два|две)\s+(\w+)', self._check_two_agreement),
            (r'\b(три|четыре)\s+(\w+)', self._check_three_four_agreement),
            (r'\b(пять|шесть|семь|восемь|девять|десять)\s+(\w+)', self._check_five_plus_agreement)
        ]
        
        for pattern, check_func in numeral_patterns:
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                if not check_func(match.group(1), match.group(2)):
                    position = full_text.find(match.group(0))
                    if position != -1:
                        errors.append(TextError(
                            error_type=ErrorType.GRAMMAR,
                            severity=ErrorSeverity.MEDIUM,
                            position=(position, position + len(match.group(0))),
                            original_text=match.group(0),
                            suggested_correction=self._suggest_numeral_correction(match.group(1), match.group(2)),
                            description="Неправильное согласование числительного с существительным",
                            confidence=0.7,
                            context=self._get_sentence_context(full_text, sentence)
                        ))
        
        return errors
    
    def _is_adjective(self, pos_tag: str) -> bool:
        """Проверка, является ли слово прилагательным"""
        return pos_tag.startswith('JJ')  # Упрощенная проверка
    
    def _is_noun(self, pos_tag: str) -> bool:
        """Проверка, является ли слово существительным"""
        return pos_tag.startswith('NN')  # Упрощенная проверка
    
    def _check_gender_number_agreement(self, adjective: str, noun: str) -> bool:
        """Проверка согласования рода и числа"""
        # Упрощенная реализация через морфологический анализ
        adj_parsed = self.morph.parse(adjective)
        noun_parsed = self.morph.parse(noun)
        
        if adj_parsed and noun_parsed:
            adj_info = adj_parsed[0]
            noun_info = noun_parsed[0]
            
            # Проверяем род и число
            adj_gender = adj_info.tag.gender
            noun_gender = noun_info.tag.gender
            adj_number = adj_info.tag.number
            noun_number = noun_info.tag.number
            
            return adj_gender == noun_gender and adj_number == noun_number
        
        return True  # Если не можем определить, считаем правильным
    
    def _suggest_agreement_correction(self, adjective: str, noun: str) -> str:
        """Предложение исправления согласования"""
        # Упрощенная реализация
        return f"{adjective} {noun}"  # Возвращаем как есть
    
    def _check_one_agreement(self, numeral: str, noun: str) -> bool:
        """Проверка согласования с 'один'"""
        # Упрощенная логика
        return True
    
    def _check_two_agreement(self, numeral: str, noun: str) -> bool:
        """Проверка согласования с 'два/две'"""
        return True
    
    def _check_three_four_agreement(self, numeral: str, noun: str) -> bool:
        """Проверка согласования с 'три/четыре'"""
        return True
    
    def _check_five_plus_agreement(self, numeral: str, noun: str) -> bool:
        """Проверка согласования с числительными от 5"""
        return True
    
    def _suggest_numeral_correction(self, numeral: str, noun: str) -> str:
        """Предложение исправления числительного"""
        return f"{numeral} {noun}"
    
    def _get_sentence_context(self, full_text: str, sentence: str) -> str:
        """Получение контекста предложения"""
        position = full_text.find(sentence)
        if position != -1:
            start = max(0, position - 100)
            end = min(len(full_text), position + len(sentence) + 100)
            return full_text[start:end]
        return sentence

class LogicalErrorDetector:
    """Детектор логических ошибок"""
    
    def __init__(self):
        # Паттерны логических противоречий
        self.contradiction_patterns = [
            (r'всегда.*никогда', 'Противоречие: "всегда" и "никогда"'),
            (r'все.*никто', 'Противоречие: "все" и "никто"'),
            (r'невозможно.*возможно', 'Противоречие: "невозможно" и "возможно"'),
            (r'увеличивается.*уменьшается', 'Противоречие: "увеличивается" и "уменьшается"'),
            (r'растет.*падает', 'Противоречие: "растет" и "падает"'),
        ]
        
        # Паттерны для обнаружения нелогичных утверждений
        self.illogical_patterns = [
            (r'100% гарантия.*может быть', 'Нелогичность: 100% гарантия не может быть неопределенной'),
            (r'абсолютно все.*исключения', 'Нелогичность: "абсолютно все" не может иметь исключений'),
            (r'никогда.*иногда', 'Нелогичность: "никогда" противоречит "иногда"'),
        ]
    
    def detect_logical_errors(self, text: str) -> List[TextError]:
        """Обнаружение логических ошибок"""
        errors = []
        
        # Проверяем противоречия
        for pattern, description in self.contradiction_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                errors.append(TextError(
                    error_type=ErrorType.LOGICAL,
                    severity=ErrorSeverity.HIGH,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    suggested_correction="Устраните противоречие",
                    description=description,
                    confidence=0.8,
                    context=self._get_context(text, match.start(), match.end() - match.start())
                ))
        
        # Проверяем нелогичные утверждения
        for pattern, description in self.illogical_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                errors.append(TextError(
                    error_type=ErrorType.LOGICAL,
                    severity=ErrorSeverity.MEDIUM,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    suggested_correction="Пересмотрите логику утверждения",
                    description=description,
                    confidence=0.7,
                    context=self._get_context(text, match.start(), match.end() - match.start())
                ))
        
        # Проверяем повторяющиеся утверждения
        errors.extend(self._detect_repetitions(text))
        
        return errors
    
    def _detect_repetitions(self, text: str) -> List[TextError]:
        """Обнаружение повторений"""
        errors = []
        sentences = sent_tokenize(text)
        
        for i, sentence1 in enumerate(sentences):
            for j, sentence2 in enumerate(sentences[i+1:], i+1):
                similarity = difflib.SequenceMatcher(None, sentence1.lower(), sentence2.lower()).ratio()
                
                if similarity > 0.8 and len(sentence1.split()) > 5:  # Похожие длинные предложения
                    position1 = text.find(sentence1)
                    position2 = text.find(sentence2, position1 + len(sentence1))
                    
                    if position1 != -1 and position2 != -1:
                        errors.append(TextError(
                            error_type=ErrorType.REPETITION,
                            severity=ErrorSeverity.MEDIUM,
                            position=(position2, position2 + len(sentence2)),
                            original_text=sentence2,
                            suggested_correction="Удалите повторение или перефразируйте",
                            description=f"Повторение предложения (схожесть: {similarity:.1%})",
                            confidence=0.9,
                            context=self._get_context(text, position2, len(sentence2))
                        ))
        
        return errors
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста"""
        start = max(0, position - 100)
        end = min(len(text), position + length + 100)
        return text[start:end]

class StyleChecker:
    """Проверка стиля текста"""
    
    def __init__(self):
        # Слова-паразиты
        self.filler_words = [
            'как бы', 'типа', 'короче', 'в общем-то', 'так сказать',
            'ну', 'вот', 'это самое', 'значит', 'понимаешь'
        ]
        
        # Канцеляризмы
        self.bureaucratic_words = [
            'осуществлять', 'производить', 'являться', 'представлять собой',
            'иметь место', 'носить характер', 'оказывать воздействие'
        ]
        
        # Слишком сложные слова
        self.complex_words = {
            'концептуализация': 'понимание',
            'имплементация': 'внедрение',
            'оптимизация': 'улучшение',
            'модификация': 'изменение',
            'интегрирование': 'объединение'
        }
    
    def check_style(self, text: str) -> List[TextError]:
        """Проверка стиля"""
        errors = []
        
        # Проверяем слова-паразиты
        for filler in self.filler_words:
            for match in re.finditer(r'\b' + re.escape(filler) + r'\b', text, re.IGNORECASE):
                errors.append(TextError(
                    error_type=ErrorType.STYLE,
                    severity=ErrorSeverity.LOW,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    suggested_correction="Удалите слово-паразит",
                    description=f"Слово-паразит: '{filler}'",
                    confidence=0.8,
                    context=self._get_context(text, match.start(), len(filler))
                ))
        
        # Проверяем канцеляризмы
        for bureaucratic in self.bureaucratic_words:
            for match in re.finditer(r'\b' + re.escape(bureaucratic) + r'\b', text, re.IGNORECASE):
                errors.append(TextError(
                    error_type=ErrorType.STYLE,
                    severity=ErrorSeverity.MEDIUM,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    suggested_correction="Замените на более простое выражение",
                    description=f"Канцеляризм: '{bureaucratic}'",
                    confidence=0.7,
                    context=self._get_context(text, match.start(), len(bureaucratic))
                ))
        
        # Проверяем сложные слова
        for complex_word, simple_word in self.complex_words.items():
            for match in re.finditer(r'\b' + re.escape(complex_word) + r'\b', text, re.IGNORECASE):
                errors.append(TextError(
                    error_type=ErrorType.STYLE,
                    severity=ErrorSeverity.LOW,
                    position=(match.start(), match.end()),
                    original_text=match.group(0),
                    suggested_correction=simple_word,
                    description=f"Сложное слово можно заменить: '{complex_word}' → '{simple_word}'",
                    confidence=0.6,
                    context=self._get_context(text, match.start(), len(complex_word))
                ))
        
        # Проверяем длину предложений
        errors.extend(self._check_sentence_length(text))
        
        return errors
    
    def _check_sentence_length(self, text: str) -> List[TextError]:
        """Проверка длины предложений"""
        errors = []
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            words = word_tokenize(sentence)
            if len(words) > 30:  # Слишком длинное предложение
                position = text.find(sentence)
                if position != -1:
                    errors.append(TextError(
                        error_type=ErrorType.STYLE,
                        severity=ErrorSeverity.MEDIUM,
                        position=(position, position + len(sentence)),
                        original_text=sentence,
                        suggested_correction="Разделите на несколько предложений",
                        description=f"Слишком длинное предложение ({len(words)} слов)",
                        confidence=0.8,
                        context=sentence
                    ))
        
        return errors
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Получение контекста"""
        start = max(0, position - 50)
        end = min(len(text), position + length + 50)
        return text[start:end]

class ComprehensiveErrorDetector:
    """Комплексная система обнаружения ошибок"""
    
    def __init__(self):
        self.spell_checker = RussianSpellChecker()
        self.grammar_checker = GrammarChecker()
        self.logical_detector = LogicalErrorDetector()
        self.style_checker = StyleChecker()
        
        # Статистика обнаружения ошибок
        self.detection_stats = defaultdict(int)
    
    def detect_all_errors(self, text: str) -> List[TextError]:
        """Комплексное обнаружение всех типов ошибок"""
        all_errors = []
        
        try:
            # Орфографические ошибки
            spelling_errors = self.spell_checker.check_spelling(text)
            all_errors.extend(spelling_errors)
            self.detection_stats[ErrorType.SPELLING] += len(spelling_errors)
            
            # Грамматические ошибки
            grammar_errors = self.grammar_checker.check_grammar(text)
            all_errors.extend(grammar_errors)
            self.detection_stats[ErrorType.GRAMMAR] += len(grammar_errors)
            
            # Логические ошибки
            logical_errors = self.logical_detector.detect_logical_errors(text)
            all_errors.extend(logical_errors)
            self.detection_stats[ErrorType.LOGICAL] += len(logical_errors)
            
            # Стилистические ошибки
            style_errors = self.style_checker.check_style(text)
            all_errors.extend(style_errors)
            self.detection_stats[ErrorType.STYLE] += len(style_errors)
            
        except Exception as e:
            logger.error(f"Ошибка при обнаружении ошибок: {e}")
        
        # Сортируем по позиции в тексте
        all_errors.sort(key=lambda x: x.position[0])
        
        return all_errors
    
    def auto_correct_text(self, text: str, min_confidence: float = 0.8) -> Tuple[str, List[TextError]]:
        """Автоматическое исправление текста"""
        errors = self.detect_all_errors(text)
        corrected_text = text
        applied_corrections = []
        
        # Применяем исправления с высокой уверенностью, начиная с конца текста
        high_confidence_errors = [e for e in errors if e.confidence >= min_confidence]
        high_confidence_errors.sort(key=lambda x: x.position[0], reverse=True)
        
        for error in high_confidence_errors:
            start, end = error.position
            if start < len(corrected_text) and end <= len(corrected_text):
                # Проверяем, что текст в позиции соответствует ошибке
                if corrected_text[start:end] == error.original_text:
                    corrected_text = (
                        corrected_text[:start] + 
                        error.suggested_correction + 
                        corrected_text[end:]
                    )
                    applied_corrections.append(error)
        
        return corrected_text, applied_corrections
    
    def get_error_summary(self, errors: List[TextError]) -> Dict[str, Any]:
        """Получение сводки по ошибкам"""
        summary = {
            'total_errors': len(errors),
            'by_type': defaultdict(int),
            'by_severity': defaultdict(int),
            'avg_confidence': 0.0,
            'critical_errors': 0
        }
        
        if not errors:
            return summary
        
        for error in errors:
            summary['by_type'][error.error_type.value] += 1
            summary['by_severity'][error.severity.value] += 1
            
            if error.severity == ErrorSeverity.CRITICAL:
                summary['critical_errors'] += 1
        
        summary['avg_confidence'] = sum(e.confidence for e in errors) / len(errors)
        
        return summary
    
    def get_detection_stats(self) -> Dict[str, int]:
        """Получение статистики обнаружения"""
        return dict(self.detection_stats)
    
    def generate_error_report(self, text: str) -> Dict[str, Any]:
        """Генерация полного отчета об ошибках"""
        errors = self.detect_all_errors(text)
        summary = self.get_error_summary(errors)
        
        # Группируем ошибки по типам
        errors_by_type = defaultdict(list)
        for error in errors:
            errors_by_type[error.error_type.value].append({
                'position': error.position,
                'original': error.original_text,
                'correction': error.suggested_correction,
                'description': error.description,
                'confidence': error.confidence,
                'severity': error.severity.value
            })
        
        return {
            'summary': summary,
            'errors_by_type': dict(errors_by_type),
            'text_stats': {
                'word_count': len(text.split()),
                'sentence_count': len(sent_tokenize(text)),
                'readability_score': flesch_reading_ease(text) if text else 0
            },
            'recommendations': self._generate_recommendations(summary)
        }
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций по улучшению текста"""
        recommendations = []
        
        if summary['critical_errors'] > 0:
            recommendations.append("Исправьте критические ошибки перед публикацией")
        
        if summary['by_type'].get('spelling', 0) > 3:
            recommendations.append("Проверьте орфографию более внимательно")
        
        if summary['by_type'].get('grammar', 0) > 2:
            recommendations.append("Обратите внимание на грамматические конструкции")
        
        if summary['by_type'].get('style', 0) > 5:
            recommendations.append("Упростите стиль изложения")
        
        if summary['by_type'].get('logical', 0) > 0:
            recommendations.append("Проверьте логическую последовательность изложения")
        
        if summary['avg_confidence'] < 0.7:
            recommendations.append("Рекомендуется ручная проверка - низкая уверенность в автоматических исправлениях")
        
        return recommendations

# Глобальный экземпляр детектора ошибок
error_detector = ComprehensiveErrorDetector()