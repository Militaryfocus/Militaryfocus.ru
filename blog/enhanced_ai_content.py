"""
Улучшенная система ИИ для генерации контента с защитными механизмами
Интеграция валидации, проверки фактов и обеспечения качества
"""

import os
import random
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import requests
from faker import Faker
import openai
import re
from collections import defaultdict

from blog.models import Post, Category, Tag, Comment, User
from blog import db
from blog.ai_validation import ai_content_validator, ValidationResult
from blog.fault_tolerance import ai_circuit_breaker, safe_db_operation
from blog.monitoring import monitoring_system

# Инициализация
fake = Faker('ru_RU')
logger = logging.getLogger(__name__)

class EnhancedAIContentGenerator:
    """Улучшенный генератор контента с защитными механизмами"""
    
    def __init__(self):
        self.openai_client = None
        self.init_ai_services()
        
        # Расширенные темы с проверенными фактами
        self.verified_topics = {
            'технологии': {
                'искусственный интеллект': {
                    'facts': [
                        'ИИ используется в медицине для диагностики',
                        'Машинное обучение помогает в анализе данных',
                        'Нейронные сети моделируют работу мозга'
                    ],
                    'sources': ['научные журналы', 'исследования университетов']
                },
                'блокчейн': {
                    'facts': [
                        'Блокчейн обеспечивает децентрализованное хранение данных',
                        'Криптография защищает транзакции в блокчейне',
                        'Смарт-контракты автоматизируют выполнение соглашений'
                    ],
                    'sources': ['технические документации', 'whitepaper проектов']
                }
            },
            'наука': {
                'космос и астрономия': {
                    'facts': [
                        'Вселенная расширяется с ускорением',
                        'Черные дыры искривляют пространство-время',
                        'Экзопланеты обнаруживаются различными методами'
                    ],
                    'sources': ['NASA', 'ESA', 'научные обсерватории']
                }
            }
        }
        
        # Шаблоны для безопасной генерации
        self.safe_templates = {
            'introduction': [
                "В современном мире тема {topic} привлекает все больше внимания исследователей и специалистов.",
                "Развитие {topic} открывает новые возможности для понимания окружающего мира.",
                "Изучение {topic} помогает нам лучше понять сложные процессы и явления."
            ],
            'evidence_based': [
                "Согласно исследованиям ведущих университетов, {fact}.",
                "Научные данные показывают, что {fact}.",
                "Эксперты в области отмечают, что {fact}."
            ],
            'conclusion': [
                "Таким образом, {topic} представляет важную область для дальнейшего изучения.",
                "Понимание {topic} поможет в решении многих современных задач.",
                "Развитие знаний о {topic} открывает новые перспективы."
            ]
        }
        
        # Система предотвращения повторов
        self.content_history = defaultdict(list)
        self.max_history_size = 100
        
        # Метрики генерации
        self.generation_stats = {
            'total_generated': 0,
            'approved': 0,
            'rejected': 0,
            'needs_review': 0,
            'avg_quality_score': 0.0
        }
    
    def init_ai_services(self):
        """Инициализация ИИ сервисов с обработкой ошибок"""
        try:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                openai.api_key = openai_key
                self.openai_client = openai
                logger.info("✅ OpenAI API инициализирован")
            else:
                logger.warning("⚠️ OpenAI API ключ не найден")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации OpenAI: {e}")
    
    @ai_circuit_breaker
    def generate_validated_post(self, category_name: str = None, topic: str = None, 
                              max_attempts: int = 3) -> Optional[Dict]:
        """Генерация поста с валидацией"""
        monitoring_system.metrics.increment_counter('ai_generation_attempts')
        
        for attempt in range(max_attempts):
            try:
                # Генерируем базовый контент
                post_data = self._generate_base_content(category_name, topic)
                
                # Валидируем контент
                validation_report = ai_content_validator.validate_content(
                    post_data['content'], 
                    post_data['title'], 
                    post_data['category']
                )
                
                # Обрабатываем результат валидации
                if validation_report.result == ValidationResult.APPROVED:
                    post_data['validation_report'] = validation_report
                    self._update_generation_stats('approved', validation_report.quality_metrics['overall_quality'])
                    monitoring_system.metrics.increment_counter('ai_posts_approved')
                    return post_data
                
                elif validation_report.result == ValidationResult.NEEDS_CORRECTION:
                    # Пытаемся исправить контент
                    corrected_data = self._correct_content(post_data, validation_report)
                    if corrected_data:
                        post_data = corrected_data
                        continue
                
                elif validation_report.result == ValidationResult.NEEDS_REVIEW:
                    # Помечаем для ручной проверки
                    post_data['validation_report'] = validation_report
                    post_data['requires_manual_review'] = True
                    self._update_generation_stats('needs_review', validation_report.quality_metrics['overall_quality'])
                    return post_data
                
                else:  # REJECTED
                    logger.warning(f"Контент отклонен на попытке {attempt + 1}: {validation_report.issues}")
                    self._update_generation_stats('rejected', validation_report.quality_metrics['overall_quality'])
                    
            except Exception as e:
                logger.error(f"Ошибка генерации на попытке {attempt + 1}: {e}")
                monitoring_system.error_tracker.record_error(e, {'attempt': attempt, 'function': 'generate_validated_post'})
        
        # Если все попытки неудачны
        monitoring_system.metrics.increment_counter('ai_generation_failures')
        return None
    
    def _generate_base_content(self, category_name: str = None, topic: str = None) -> Dict:
        """Генерация базового контента"""
        # Выбираем категорию и тему
        if not category_name:
            category_name = random.choice(list(self.verified_topics.keys()))
        
        if not topic:
            available_topics = list(self.verified_topics.get(category_name, {}).keys())
            if available_topics:
                topic = random.choice(available_topics)
            else:
                topic = 'общие вопросы'
        
        # Проверяем на повторы
        if self._is_duplicate_topic(category_name, topic):
            # Выбираем альтернативную тему
            all_topics = []
            for cat, topics in self.verified_topics.items():
                all_topics.extend([(cat, t) for t in topics.keys()])
            
            if all_topics:
                category_name, topic = random.choice(all_topics)
        
        # Генерируем заголовок
        title = self._generate_safe_title(topic)
        
        # Генерируем контент на основе проверенных фактов
        content = self._generate_fact_based_content(category_name, topic)
        
        # Генерируем краткое описание
        excerpt = self._generate_safe_excerpt(content)
        
        # Генерируем теги
        tags = self._generate_relevant_tags(topic, category_name)
        
        # Записываем в историю
        self._add_to_history(category_name, topic)
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'category': category_name,
            'tags': tags,
            'reading_time': self._calculate_reading_time(content),
            'generated_at': datetime.now(),
            'source_topic': topic
        }
    
    def _generate_safe_title(self, topic: str) -> str:
        """Генерация безопасного заголовка"""
        safe_templates = [
            "Введение в {topic}",
            "Основы {topic}: что нужно знать",
            "Современное состояние {topic}",
            "Перспективы развития {topic}",
            "Практическое применение {topic}",
            "{topic}: основные принципы",
            "Изучаем {topic}: пошаговое руководство",
            "Важность {topic} в современном мире"
        ]
        
        template = random.choice(safe_templates)
        return template.format(topic=topic)
    
    def _generate_fact_based_content(self, category_name: str, topic: str) -> str:
        """Генерация контента на основе проверенных фактов"""
        topic_data = self.verified_topics.get(category_name, {}).get(topic, {})
        facts = topic_data.get('facts', [])
        sources = topic_data.get('sources', [])
        
        # Введение
        intro_template = random.choice(self.safe_templates['introduction'])
        introduction = intro_template.format(topic=topic)
        
        # Основной контент на основе фактов
        main_sections = []
        
        if facts:
            main_sections.append("## Основные факты\n")
            for i, fact in enumerate(facts[:3], 1):
                evidence_template = random.choice(self.safe_templates['evidence_based'])
                main_sections.append(f"{i}. {evidence_template.format(fact=fact)}")
            
            main_sections.append("")  # Пустая строка для разделения
        
        # Практическое применение
        main_sections.append("## Практическое применение\n")
        main_sections.append(f"Знания о {topic} находят применение в различных областях:")
        main_sections.append(f"- Исследовательская деятельность")
        main_sections.append(f"- Образовательные программы")
        main_sections.append(f"- Практические решения")
        main_sections.append("")
        
        # Перспективы
        main_sections.append("## Перспективы развития\n")
        main_sections.append(f"Развитие {topic} открывает новые возможности для:")
        main_sections.append(f"- Углубления научных знаний")
        main_sections.append(f"- Создания инновационных решений")
        main_sections.append(f"- Междисциплинарного сотрудничества")
        main_sections.append("")
        
        # Заключение
        conclusion_template = random.choice(self.safe_templates['conclusion'])
        conclusion = conclusion_template.format(topic=topic)
        
        # Источники (если есть)
        sources_section = ""
        if sources:
            sources_section = f"\n\n## Источники информации\n"
            sources_section += f"Материал подготовлен на основе данных из: {', '.join(sources)}."
        
        # Объединяем все части
        content = f"{introduction}\n\n" + "\n".join(main_sections) + f"{conclusion}{sources_section}"
        
        return content
    
    def _generate_safe_excerpt(self, content: str) -> str:
        """Генерация безопасного краткого описания"""
        # Берем первое предложение, очищенное от Markdown
        sentences = content.split('.')
        first_sentence = sentences[0].strip()
        
        # Убираем Markdown разметку
        clean_sentence = re.sub(r'[#*`]', '', first_sentence)
        
        # Ограничиваем длину
        if len(clean_sentence) > 150:
            clean_sentence = clean_sentence[:147] + "..."
        
        return clean_sentence + "."
    
    def _generate_relevant_tags(self, topic: str, category: str) -> List[str]:
        """Генерация релевантных тегов"""
        base_tags = [topic, category]
        
        # Дополнительные теги в зависимости от категории
        category_tags = {
            'технологии': ['инновации', 'цифровизация', 'IT', 'прогресс'],
            'наука': ['исследования', 'открытия', 'эксперименты', 'знания'],
            'общество': ['культура', 'развитие', 'социум', 'образование'],
            'бизнес': ['экономика', 'управление', 'стратегия', 'развитие']
        }
        
        additional_tags = category_tags.get(category, ['развитие', 'знания', 'современность'])
        selected_additional = random.sample(additional_tags, min(3, len(additional_tags)))
        
        return base_tags + selected_additional
    
    def _is_duplicate_topic(self, category: str, topic: str) -> bool:
        """Проверка на дублирование темы"""
        key = f"{category}:{topic}"
        recent_history = self.content_history[key]
        
        # Проверяем, была ли эта тема использована недавно
        if recent_history:
            last_used = recent_history[-1]
            time_diff = datetime.now() - last_used
            return time_diff < timedelta(hours=24)  # Не повторяем тему в течение 24 часов
        
        return False
    
    def _add_to_history(self, category: str, topic: str):
        """Добавление в историю генерации"""
        key = f"{category}:{topic}"
        self.content_history[key].append(datetime.now())
        
        # Ограничиваем размер истории
        if len(self.content_history[key]) > self.max_history_size:
            self.content_history[key] = self.content_history[key][-self.max_history_size:]
    
    def _correct_content(self, post_data: Dict, validation_report) -> Optional[Dict]:
        """Исправление контента на основе отчета валидации"""
        try:
            content = post_data['content']
            issues = validation_report.issues
            suggestions = validation_report.suggestions
            
            # Применяем исправления на основе предложений
            for suggestion in suggestions:
                if 'слишком короткий' in suggestion:
                    content = self._expand_content(content, post_data['source_topic'])
                elif 'слишком сложен' in suggestion:
                    content = self._simplify_content(content)
                elif 'структура' in suggestion:
                    content = self._improve_structure(content)
                elif 'разнообразие' in suggestion:
                    content = self._improve_vocabulary(content)
            
            # Обновляем данные поста
            post_data['content'] = content
            post_data['excerpt'] = self._generate_safe_excerpt(content)
            post_data['reading_time'] = self._calculate_reading_time(content)
            
            return post_data
            
        except Exception as e:
            logger.error(f"Ошибка исправления контента: {e}")
            return None
    
    def _expand_content(self, content: str, topic: str) -> str:
        """Расширение контента"""
        additional_section = f"""
## Дополнительная информация

Изучение {topic} включает в себя множество аспектов, которые важно учитывать:

- **Теоретические основы**: Понимание базовых принципов и концепций
- **Практические навыки**: Применение знаний в реальных ситуациях  
- **Современные тенденции**: Отслеживание новых разработок и подходов
- **Междисциплинарные связи**: Взаимодействие с другими областями знаний

Эти аспекты помогают сформировать целостное представление о предмете изучения.
"""
        return content + additional_section
    
    def _simplify_content(self, content: str) -> str:
        """Упрощение контента"""
        # Заменяем сложные слова на простые
        simplifications = {
            'концептуализация': 'понимание',
            'имплементация': 'внедрение',
            'оптимизация': 'улучшение',
            'интеграция': 'объединение',
            'модификация': 'изменение'
        }
        
        for complex_word, simple_word in simplifications.items():
            content = content.replace(complex_word, simple_word)
        
        return content
    
    def _improve_structure(self, content: str) -> str:
        """Улучшение структуры контента"""
        # Добавляем заголовки, если их нет
        if '##' not in content:
            paragraphs = content.split('\n\n')
            if len(paragraphs) >= 3:
                # Добавляем заголовки к основным частям
                structured_content = paragraphs[0] + '\n\n'  # Введение
                structured_content += '## Основная часть\n\n' + paragraphs[1] + '\n\n'
                if len(paragraphs) > 2:
                    structured_content += '## Заключение\n\n' + '\n\n'.join(paragraphs[2:])
                return structured_content
        
        return content
    
    def _improve_vocabulary(self, content: str) -> str:
        """Улучшение разнообразия лексики"""
        # Простая замена повторяющихся слов синонимами
        synonyms = {
            'важный': ['значимый', 'существенный', 'ключевой'],
            'большой': ['значительный', 'крупный', 'масштабный'],
            'хороший': ['качественный', 'эффективный', 'успешный'],
            'новый': ['современный', 'актуальный', 'инновационный']
        }
        
        words = content.split()
        word_count = Counter(word.lower() for word in words)
        
        for word, count in word_count.items():
            if count > 3 and word in synonyms:
                # Заменяем некоторые вхождения синонимами
                replacements = synonyms[word]
                content = self._replace_word_instances(content, word, replacements, max_replacements=count//2)
        
        return content
    
    def _replace_word_instances(self, text: str, word: str, replacements: List[str], max_replacements: int) -> str:
        """Замена нескольких вхождений слова синонимами"""
        import re
        
        def replace_func(match):
            if hasattr(replace_func, 'count'):
                replace_func.count += 1
            else:
                replace_func.count = 1
            
            if replace_func.count <= max_replacements:
                return random.choice(replacements)
            return match.group(0)
        
        pattern = r'\b' + re.escape(word) + r'\b'
        return re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
    
    def _calculate_reading_time(self, content: str) -> int:
        """Расчет времени чтения"""
        words = len(content.split())
        return max(1, words // 200)  # 200 слов в минуту
    
    def _update_generation_stats(self, result_type: str, quality_score: float):
        """Обновление статистики генерации"""
        self.generation_stats['total_generated'] += 1
        self.generation_stats[result_type] += 1
        
        # Обновляем среднюю оценку качества
        total = self.generation_stats['total_generated']
        current_avg = self.generation_stats['avg_quality_score']
        self.generation_stats['avg_quality_score'] = (current_avg * (total - 1) + quality_score) / total
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Получение статистики генерации"""
        stats = self.generation_stats.copy()
        
        if stats['total_generated'] > 0:
            stats['approval_rate'] = stats['approved'] / stats['total_generated']
            stats['rejection_rate'] = stats['rejected'] / stats['total_generated']
            stats['review_rate'] = stats['needs_review'] / stats['total_generated']
        else:
            stats['approval_rate'] = 0.0
            stats['rejection_rate'] = 0.0
            stats['review_rate'] = 0.0
        
        return stats
    
    def clear_history(self, older_than_hours: int = 168):  # 7 дней по умолчанию
        """Очистка старой истории генерации"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        for key in list(self.content_history.keys()):
            self.content_history[key] = [
                timestamp for timestamp in self.content_history[key]
                if timestamp > cutoff_time
            ]
            
            # Удаляем пустые записи
            if not self.content_history[key]:
                del self.content_history[key]

class EnhancedContentScheduler:
    """Улучшенный планировщик контента с валидацией"""
    
    def __init__(self):
        self.generator = EnhancedAIContentGenerator()
        self.pending_review_posts = []
    
    def create_validated_post(self, category_name: str = None) -> bool:
        """Создание валидированного поста"""
        try:
            with safe_db_operation():
                # Генерируем контент с валидацией
                post_data = self.generator.generate_validated_post(category_name)
                
                if not post_data:
                    logger.error("Не удалось сгенерировать валидный контент")
                    return False
                
                # Проверяем, требуется ли ручная проверка
                if post_data.get('requires_manual_review', False):
                    self.pending_review_posts.append(post_data)
                    logger.info(f"Пост '{post_data['title']}' добавлен в очередь на проверку")
                    return True
                
                # Создаем пост в базе данных
                success = self._create_post_in_db(post_data)
                
                if success:
                    monitoring_system.metrics.increment_counter('validated_posts_created')
                    logger.info(f"✅ Создан валидированный пост: {post_data['title']}")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания валидированного поста: {e}")
            monitoring_system.error_tracker.record_error(e, {'function': 'create_validated_post'})
            return False
    
    def _create_post_in_db(self, post_data: Dict) -> bool:
        """Создание поста в базе данных"""
        try:
            # Получаем или создаем категорию
            category = Category.query.filter_by(name=post_data['category']).first()
            if not category:
                category = Category(
                    name=post_data['category'],
                    description=f"Статьи о {post_data['category']}"
                )
                db.session.add(category)
                db.session.flush()
            
            # Получаем автора (админа)
            author = User.query.filter_by(is_admin=True).first()
            if not author:
                logger.error("Не найден администратор для создания поста")
                return False
            
            # Создаем пост
            post = Post(
                title=post_data['title'],
                content=post_data['content'],
                excerpt=post_data['excerpt'],
                category_id=category.id,
                author_id=author.id,
                is_published=True,
                published_at=datetime.utcnow()
            )
            
            db.session.add(post)
            db.session.flush()
            
            # Добавляем теги
            for tag_name in post_data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                post.tags.append(tag)
            
            # Сохраняем отчет валидации как метаданные
            if 'validation_report' in post_data:
                validation_report = post_data['validation_report']
                post.meta_data = json.dumps({
                    'validation_score': validation_report.confidence_score,
                    'quality_metrics': validation_report.quality_metrics,
                    'generated_at': post_data['generated_at'].isoformat(),
                    'ai_generated': True
                })
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания поста в БД: {e}")
            return False
    
    def get_pending_review_posts(self) -> List[Dict]:
        """Получение постов, ожидающих проверки"""
        return self.pending_review_posts.copy()
    
    def approve_pending_post(self, post_index: int) -> bool:
        """Одобрение поста из очереди проверки"""
        try:
            if 0 <= post_index < len(self.pending_review_posts):
                post_data = self.pending_review_posts.pop(post_index)
                return self._create_post_in_db(post_data)
            return False
        except Exception as e:
            logger.error(f"Ошибка одобрения поста: {e}")
            return False
    
    def reject_pending_post(self, post_index: int) -> bool:
        """Отклонение поста из очереди проверки"""
        try:
            if 0 <= post_index < len(self.pending_review_posts):
                rejected_post = self.pending_review_posts.pop(post_index)
                logger.info(f"Пост '{rejected_post['title']}' отклонен")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка отклонения поста: {e}")
            return False

# Функции для совместимости с существующим кодом
def populate_blog_with_validated_content(num_posts: int = 10) -> int:
    """Наполнение блога валидированным контентом"""
    scheduler = EnhancedContentScheduler()
    
    logger.info(f"🤖 Начинаем генерацию {num_posts} валидированных постов...")
    
    success_count = 0
    for i in range(num_posts):
        if scheduler.create_validated_post():
            success_count += 1
        
        # Небольшая задержка между постами
        time.sleep(2)
    
    logger.info(f"✅ Успешно создано {success_count} из {num_posts} валидированных постов")
    
    # Выводим статистику
    stats = scheduler.generator.get_generation_stats()
    logger.info(f"📊 Статистика: одобрено {stats['approval_rate']:.1%}, "
               f"отклонено {stats['rejection_rate']:.1%}, "
               f"на проверке {stats['review_rate']:.1%}")
    
    return success_count

def start_enhanced_ai_content_generation():
    """Запуск улучшенной автоматической генерации контента"""
    import schedule
    
    scheduler = EnhancedContentScheduler()
    
    # Планируем создание постов с валидацией
    schedule.every(8).hours.do(lambda: scheduler.create_validated_post())
    schedule.every().day.at("10:00").do(lambda: scheduler.create_validated_post())
    schedule.every().day.at("16:00").do(lambda: scheduler.create_validated_post())
    schedule.every().day.at("22:00").do(lambda: scheduler.create_validated_post())
    
    # Очистка истории раз в неделю
    schedule.every().week.do(lambda: scheduler.generator.clear_history())
    
    logger.info("🤖 Улучшенный планировщик ИИ контента запущен")
    logger.info("📅 Валидированные посты будут создаваться каждые 8 часов")
    logger.info("🔍 Все посты проходят проверку на качество и безопасность")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Глобальные экземпляры
enhanced_generator = EnhancedAIContentGenerator()
enhanced_scheduler = EnhancedContentScheduler()