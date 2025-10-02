"""
Система ИИ для автоматического наполнения блога контентом
"""

import os
import random
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from faker import Faker
import openai
from textstat import flesch_reading_ease, automated_readability_index
import nltk
from transformers import pipeline
import re

from blog.models import Post, Category, Tag, Comment, User
from blog import db

# Инициализация
fake = Faker('ru_RU')

class AIContentGenerator:
    """Генератор контента с помощью ИИ"""
    
    def __init__(self):
        self.openai_client = None
        self.local_generator = None
        self.init_ai_services()
        
        # Темы для генерации контента
        self.content_topics = {
            'технологии': [
                'искусственный интеллект', 'машинное обучение', 'блокчейн',
                'веб-разработка', 'мобильные приложения', 'кибербезопасность',
                'облачные технологии', 'интернет вещей', 'большие данные',
                'виртуальная реальность', 'квантовые вычисления', 'роботика'
            ],
            'наука': [
                'космос и астрономия', 'биология и медицина', 'физика',
                'химия', 'экология', 'генетика', 'нейронауки',
                'математика', 'археология', 'геология'
            ],
            'общество': [
                'образование', 'культура', 'искусство', 'история',
                'философия', 'психология', 'социология', 'политика',
                'экономика', 'спорт', 'путешествия', 'кулинария'
            ],
            'бизнес': [
                'стартапы', 'маркетинг', 'менеджмент', 'финансы',
                'инвестиции', 'предпринимательство', 'инновации',
                'лидерство', 'продуктивность', 'карьера'
            ]
        }
        
        # Стили написания
        self.writing_styles = [
            'информативный', 'разговорный', 'научно-популярный',
            'аналитический', 'повествовательный', 'мотивационный',
            'критический', 'обзорный', 'практический', 'философский'
        ]
        
        # Шаблоны для генерации заголовков
        self.title_templates = [
            "Как {} изменит наше будущее",
            "10 фактов о {}, которые вас удивят",
            "Почему {} важно для каждого",
            "Революция в {}: что нас ждет",
            "Секреты {}: полное руководство",
            "Будущее {}: тенденции и прогнозы",
            "Мифы и реальность о {}",
            "Практическое применение {} в жизни",
            "История развития {}: от истоков до наших дней",
            "Этические аспекты {}: за и против"
        ]

    def init_ai_services(self):
        """Инициализация ИИ сервисов"""
        try:
            # OpenAI API
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                openai.api_key = openai_key
                self.openai_client = openai
                print("✅ OpenAI API инициализирован")
            
            # Локальная модель для генерации текста
            try:
                self.local_generator = pipeline(
                    "text-generation",
                    model="microsoft/DialoGPT-medium",
                    tokenizer="microsoft/DialoGPT-medium"
                )
                print("✅ Локальная модель инициализирована")
            except Exception as e:
                print(f"⚠️ Локальная модель недоступна: {e}")
                
        except Exception as e:
            print(f"⚠️ Ошибка инициализации ИИ: {e}")

    def generate_human_like_post(self, category_name: str = None, topic: str = None) -> Dict:
        """Генерация поста, неотличимого от человеческого"""
        
        # Выбираем категорию и тему
        if not category_name:
            category_name = random.choice(list(self.content_topics.keys()))
        
        if not topic:
            topic = random.choice(self.content_topics.get(category_name, ['общие вопросы']))
        
        # Генерируем заголовок
        title = self.generate_title(topic)
        
        # Генерируем контент
        content = self.generate_content(title, topic, category_name)
        
        # Генерируем краткое описание
        excerpt = self.generate_excerpt(content)
        
        # Генерируем теги
        tags = self.generate_tags(topic, content)
        
        # Добавляем человеческие элементы
        content = self.humanize_content(content)
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'category': category_name,
            'tags': tags,
            'reading_time': self.calculate_reading_time(content),
            'quality_score': self.assess_content_quality(content)
        }

    def generate_title(self, topic: str) -> str:
        """Генерация привлекательного заголовка"""
        template = random.choice(self.title_templates)
        title = template.format(topic)
        
        # Добавляем вариативность
        variations = [
            title,
            f"{title}: подробный анализ",
            f"Все о {topic}: {title.lower()}",
            f"{title} в 2024 году",
            f"Экспертное мнение: {title.lower()}"
        ]
        
        return random.choice(variations)

    def generate_content(self, title: str, topic: str, category: str) -> str:
        """Генерация основного контента"""
        
        # Структура статьи
        sections = [
            self.generate_introduction(title, topic),
            self.generate_main_content(topic, category),
            self.generate_practical_examples(topic),
            self.generate_conclusion(topic)
        ]
        
        # Объединяем секции
        content = "\n\n".join(sections)
        
        # Добавляем форматирование Markdown
        content = self.add_markdown_formatting(content)
        
        return content

    def generate_introduction(self, title: str, topic: str) -> str:
        """Генерация введения"""
        intros = [
            f"В современном мире {topic} играет все более важную роль. Давайте разберемся, почему это так важно и как это влияет на нашу жизнь.",
            f"Многие задаются вопросом о {topic}. В этой статье мы подробно рассмотрим все аспекты этой темы.",
            f"Тема {topic} становится все более актуальной. Сегодня мы поговорим о том, что нужно знать каждому.",
            f"Развитие {topic} происходит стремительными темпами. Важно понимать основные тенденции и перспективы.",
            f"Интерес к {topic} растет с каждым днем. Давайте разберемся в деталях и выясним, что это означает для нас."
        ]
        
        return random.choice(intros)

    def generate_main_content(self, topic: str, category: str) -> str:
        """Генерация основного содержания"""
        
        # Базовые факты и информация
        main_points = [
            f"## Основные аспекты {topic}\n\n{self.generate_factual_content(topic)}",
            f"## Современное состояние\n\n{self.generate_current_state(topic)}",
            f"## Влияние на общество\n\n{self.generate_impact_analysis(topic)}",
            f"## Перспективы развития\n\n{self.generate_future_outlook(topic)}"
        ]
        
        # Выбираем 2-3 секции
        selected_points = random.sample(main_points, random.randint(2, 3))
        
        return "\n\n".join(selected_points)

    def generate_factual_content(self, topic: str) -> str:
        """Генерация фактического контента"""
        facts = [
            f"Исследования показывают, что {topic} имеет значительное влияние на различные сферы жизни.",
            f"Эксперты отмечают растущую важность {topic} в современном обществе.",
            f"Статистика демонстрирует устойчивый рост интереса к {topic} среди специалистов.",
            f"Анализ тенденций показывает, что {topic} будет играть ключевую роль в ближайшие годы.",
            f"Практическое применение {topic} уже показало впечатляющие результаты в различных областях."
        ]
        
        selected_facts = random.sample(facts, random.randint(2, 3))
        
        # Добавляем детали
        detailed_content = []
        for fact in selected_facts:
            details = [
                "Это подтверждается многочисленными исследованиями ведущих университетов.",
                "Крупные компании уже внедряют соответствующие решения.",
                "Государственные программы поддерживают развитие этого направления.",
                "Международные организации признают важность данной области."
            ]
            detailed_content.append(f"{fact} {random.choice(details)}")
        
        return "\n\n".join(detailed_content)

    def generate_current_state(self, topic: str) -> str:
        """Генерация описания текущего состояния"""
        current_state = f"""
На сегодняшний день {topic} находится в стадии активного развития. Основные тенденции включают:

- **Технологический прогресс**: Новые решения появляются регулярно
- **Рост инвестиций**: Увеличение финансирования исследований
- **Международное сотрудничество**: Обмен опытом между странами
- **Образовательные программы**: Подготовка специалистов в области

Эксперты прогнозируют дальнейший рост и развитие этой сферы.
        """
        return current_state.strip()

    def generate_impact_analysis(self, topic: str) -> str:
        """Генерация анализа влияния"""
        impacts = [
            f"Влияние {topic} на экономику трудно переоценить. Новые рабочие места, инновационные продукты и услуги создают дополнительную стоимость.",
            f"Социальные аспекты {topic} также заслуживают внимания. Изменения в образе жизни людей становятся все более заметными.",
            f"Экологические последствия развития {topic} требуют тщательного анализа и контроля.",
            f"Культурное влияние {topic} проявляется в изменении ценностей и приоритетов общества."
        ]
        
        return random.choice(impacts)

    def generate_future_outlook(self, topic: str) -> str:
        """Генерация прогноза на будущее"""
        outlooks = [
            f"Будущее {topic} выглядит многообещающим. Ожидается значительный прогресс в ближайшие 5-10 лет.",
            f"Перспективы развития {topic} включают новые технологии, методы и подходы.",
            f"Эксперты предсказывают революционные изменения в области {topic} в следующем десятилетии.",
            f"Инновации в сфере {topic} могут кардинально изменить наш образ жизни."
        ]
        
        return random.choice(outlooks)

    def generate_practical_examples(self, topic: str) -> str:
        """Генерация практических примеров"""
        examples = f"""
## Практические примеры

Рассмотрим несколько конкретных случаев применения {topic}:

### Пример 1: Повседневная жизнь
В обычной жизни мы сталкиваемся с {topic} чаще, чем думаем. Это может проявляться в различных формах и ситуациях.

### Пример 2: Профессиональная деятельность
Специалисты активно используют принципы {topic} в своей работе, что приводит к повышению эффективности.

### Пример 3: Образование
Образовательные учреждения интегрируют {topic} в учебные программы, готовя студентов к будущему.
        """
        return examples.strip()

    def generate_conclusion(self, topic: str) -> str:
        """Генерация заключения"""
        conclusions = [
            f"В заключение можно сказать, что {topic} представляет собой важную область для изучения и развития. Понимание основных принципов поможет каждому быть готовым к изменениям.",
            f"Подводя итоги, стоит отметить растущую значимость {topic} в современном мире. Инвестиции в изучение и развитие этой области окупятся в будущем.",
            f"Таким образом, {topic} является не просто трендом, а фундаментальным направлением развития. Важно следить за новостями и тенденциями в этой сфере.",
            f"В итоге, {topic} открывает новые возможности и перспективы. Главное - быть готовым к изменениям и активно участвовать в процессе развития."
        ]
        
        conclusion = random.choice(conclusions)
        
        # Добавляем призыв к действию
        call_to_action = [
            "\n\nЧто вы думаете об этой теме? Поделитесь своим мнением в комментариях!",
            "\n\nЕсли статья была полезной, не забудьте поделиться ей с друзьями.",
            "\n\nПодписывайтесь на наш блог, чтобы не пропустить новые интересные материалы.",
            "\n\nОставляйте вопросы в комментариях - мы обязательно на них ответим!"
        ]
        
        return conclusion + random.choice(call_to_action)

    def generate_excerpt(self, content: str) -> str:
        """Генерация краткого описания"""
        # Берем первое предложение или первые 150 символов
        sentences = content.split('.')
        first_sentence = sentences[0].strip()
        
        if len(first_sentence) > 150:
            excerpt = first_sentence[:150] + "..."
        else:
            excerpt = first_sentence + "."
        
        # Убираем Markdown разметку
        excerpt = re.sub(r'[#*`]', '', excerpt)
        
        return excerpt

    def generate_tags(self, topic: str, content: str) -> List[str]:
        """Генерация тегов"""
        base_tags = [topic]
        
        # Дополнительные теги на основе контента
        additional_tags = [
            'технологии', 'инновации', 'будущее', 'развитие',
            'наука', 'исследования', 'анализ', 'тренды',
            'общество', 'культура', 'образование', 'прогресс'
        ]
        
        # Выбираем случайные теги
        selected_tags = random.sample(additional_tags, random.randint(3, 6))
        
        return base_tags + selected_tags

    def humanize_content(self, content: str) -> str:
        """Добавление человеческих элементов в контент"""
        
        # Добавляем личные мнения и эмоции
        personal_touches = [
            "По моему мнению, ",
            "Интересно отметить, что ",
            "Удивительно, но ",
            "Стоит признать, что ",
            "Нельзя не согласиться с тем, что "
        ]
        
        # Добавляем разговорные элементы
        conversational_elements = [
            "Согласитесь, это довольно интересно.",
            "Не правда ли, это заставляет задуматься?",
            "Думаю, многие с этим согласятся.",
            "Возможно, вы уже сталкивались с подобным.",
            "Наверняка вы задавались похожими вопросами."
        ]
        
        # Случайно вставляем элементы
        paragraphs = content.split('\n\n')
        for i in range(len(paragraphs)):
            if random.random() < 0.3:  # 30% вероятность
                if random.random() < 0.5:
                    paragraphs[i] = random.choice(personal_touches) + paragraphs[i].lower()
                else:
                    paragraphs[i] += " " + random.choice(conversational_elements)
        
        return '\n\n'.join(paragraphs)

    def add_markdown_formatting(self, content: str) -> str:
        """Добавление Markdown форматирования"""
        
        # Добавляем выделения
        words_to_emphasize = ['важно', 'ключевой', 'основной', 'главный', 'существенный']
        for word in words_to_emphasize:
            content = re.sub(f'\\b{word}\\b', f'**{word}**', content, flags=re.IGNORECASE)
        
        # Добавляем списки
        if random.random() < 0.4:  # 40% вероятность добавить список
            list_items = [
                "- Первый важный пункт",
                "- Второй значимый аспект", 
                "- Третий ключевой момент"
            ]
            content += "\n\n" + "\n".join(list_items)
        
        return content

    def calculate_reading_time(self, content: str) -> int:
        """Расчет времени чтения"""
        words = len(content.split())
        return max(1, words // 200)  # 200 слов в минуту

    def assess_content_quality(self, content: str) -> float:
        """Оценка качества контента"""
        try:
            # Читаемость по Флешу
            readability = flesch_reading_ease(content)
            
            # Длина контента
            word_count = len(content.split())
            length_score = min(1.0, word_count / 1000)
            
            # Разнообразие предложений
            sentences = content.split('.')
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            variety_score = 1.0 if 10 <= avg_sentence_length <= 20 else 0.7
            
            # Общая оценка
            quality = (readability / 100 + length_score + variety_score) / 3
            return min(1.0, max(0.0, quality))
            
        except:
            return 0.8  # Средняя оценка по умолчанию

    def generate_realistic_comment(self, post_title: str, post_content: str) -> str:
        """Генерация реалистичного комментария"""
        
        comment_types = [
            'positive', 'question', 'experience', 'addition', 'neutral'
        ]
        
        comment_type = random.choice(comment_types)
        
        if comment_type == 'positive':
            comments = [
                "Отличная статья! Очень познавательно и интересно написано.",
                "Спасибо за подробный разбор темы. Многое стало понятнее.",
                "Качественный материал, сохраню себе в закладки.",
                "Автор молодец, тема раскрыта полностью и доступно.",
                "Именно такой информации мне и не хватало. Благодарю!"
            ]
        elif comment_type == 'question':
            comments = [
                "А можете подробнее рассказать про практическое применение?",
                "Интересно, а как это работает в реальных условиях?",
                "У меня вопрос по поводу одного момента в статье...",
                "А есть ли какие-то ограничения или недостатки?",
                "Можете посоветовать дополнительную литературу по теме?"
            ]
        elif comment_type == 'experience':
            comments = [
                "У меня был похожий опыт, могу подтвердить ваши слова.",
                "В нашей компании мы тоже сталкивались с подобным.",
                "Из личного опыта могу добавить, что...",
                "Работаю в этой сфере уже несколько лет, статья очень точная.",
                "Недавно сам изучал эту тему, ваш материал очень помог."
            ]
        elif comment_type == 'addition':
            comments = [
                "Хотел бы добавить еще один важный аспект к вашей статье.",
                "Также стоит упомянуть о последних исследованиях в этой области.",
                "Интересно было бы рассмотреть и альтернативную точку зрения.",
                "Можно еще добавить информацию о международном опыте.",
                "Думаю, стоит также учесть экономические аспекты вопроса."
            ]
        else:  # neutral
            comments = [
                "Интересная тема, буду следить за развитием.",
                "Познавательно, спасибо за информацию.",
                "Хорошо структурированный материал.",
                "Тема актуальная, важно о ней говорить.",
                "Полезная статья для общего развития."
            ]
        
        return random.choice(comments)

class ContentScheduler:
    """Планировщик автоматической публикации контента"""
    
    def __init__(self):
        self.generator = AIContentGenerator()
    
    def create_scheduled_post(self, category_name: str = None) -> bool:
        """Создание запланированного поста"""
        try:
            # Генерируем контент
            post_data = self.generator.generate_human_like_post(category_name)
            
            # Получаем или создаем категорию
            category = Category.query.filter_by(name=post_data['category']).first()
            if not category:
                category = Category(
                    name=post_data['category'],
                    description=f"Статьи о {post_data['category']}"
                )
                db.session.add(category)
                db.session.flush()
            
            # Получаем случайного автора (админа)
            author = User.query.filter_by(is_admin=True).first()
            if not author:
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
            
            db.session.commit()
            
            # Генерируем комментарии через некоторое время
            self.schedule_comments(post.id)
            
            print(f"✅ Создан пост: {post.title}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка создания поста: {e}")
            return False
    
    def schedule_comments(self, post_id: int):
        """Планирование комментариев к посту"""
        try:
            post = Post.query.get(post_id)
            if not post:
                return
            
            # Генерируем 1-5 комментариев
            num_comments = random.randint(1, 5)
            
            for i in range(num_comments):
                # Случайная задержка от 1 до 24 часов
                delay_hours = random.randint(1, 24)
                
                # Создаем фейкового пользователя для комментария
                fake_user = self.create_fake_user()
                
                # Генерируем комментарий
                comment_text = self.generator.generate_realistic_comment(
                    post.title, post.content
                )
                
                comment = Comment(
                    content=comment_text,
                    author_id=fake_user.id,
                    post_id=post.id,
                    is_approved=True,
                    created_at=datetime.utcnow() + timedelta(hours=delay_hours)
                )
                
                db.session.add(comment)
            
            db.session.commit()
            print(f"✅ Запланированы комментарии для поста: {post.title}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка планирования комментариев: {e}")
    
    def create_fake_user(self) -> User:
        """Создание фейкового пользователя для комментариев"""
        try:
            # Проверяем, есть ли уже такой пользователь
            username = fake.user_name()
            existing_user = User.query.filter_by(username=username).first()
            
            if existing_user:
                return existing_user
            
            user = User(
                username=username,
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                bio=fake.text(max_nb_chars=100),
                is_admin=False,
                created_at=fake.date_time_between(start_date='-1y', end_date='now')
            )
            user.set_password('fake_password_123')
            
            db.session.add(user)
            db.session.commit()
            
            return user
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка создания фейкового пользователя: {e}")
            return User.query.filter_by(is_admin=True).first()

def populate_blog_with_ai_content(num_posts: int = 10):
    """Наполнение блога ИИ контентом"""
    scheduler = ContentScheduler()
    
    print(f"🤖 Начинаем генерацию {num_posts} постов...")
    
    success_count = 0
    for i in range(num_posts):
        if scheduler.create_scheduled_post():
            success_count += 1
        
        # Небольшая задержка между постами
        time.sleep(1)
    
    print(f"✅ Успешно создано {success_count} из {num_posts} постов")
    return success_count

def start_ai_content_generation():
    """Запуск автоматической генерации контента"""
    import schedule
    
    # Планируем создание постов
    schedule.every(6).hours.do(lambda: ContentScheduler().create_scheduled_post())
    schedule.every().day.at("09:00").do(lambda: ContentScheduler().create_scheduled_post())
    schedule.every().day.at("15:00").do(lambda: ContentScheduler().create_scheduled_post())
    schedule.every().day.at("21:00").do(lambda: ContentScheduler().create_scheduled_post())
    
    print("🤖 Планировщик ИИ контента запущен")
    print("📅 Посты будут создаваться каждые 6 часов и в 9:00, 15:00, 21:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту