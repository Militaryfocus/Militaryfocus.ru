"""
Автономная ИИ система управления контентом
ИИ самостоятельно создает категории, теги, планирует контент и управляет структурой блога
"""

import os
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from collections import Counter, defaultdict
import re
import logging

from blog.models import Post, Category, Tag, User, Comment
from blog import db
from blog.ai_content import AIContentGenerator
from blog.security import log_security_event

logger = logging.getLogger(__name__)

class AutonomousContentManager:
    """Автономный менеджер контента с ИИ"""
    
    def __init__(self):
        self.ai_generator = AIContentGenerator()
        self.content_planner = ContentPlanner()
        self.category_manager = CategoryManager()
        self.tag_manager = TagManager()
        self.trend_analyzer = TrendAnalyzer()
        
        # Статистика работы системы
        self.stats = {
            'categories_created': 0,
            'tags_created': 0,
            'posts_generated': 0,
            'trends_analyzed': 0,
            'last_analysis': None
        }
    
    def run_autonomous_cycle(self) -> Dict:
        """Запуск полного автономного цикла управления контентом"""
        logger.info("🤖 Запуск автономного цикла ИИ управления контентом")
        
        results = {
            'timestamp': datetime.now(),
            'categories_created': 0,
            'tags_created': 0,
            'posts_generated': 0,
            'trends_analyzed': 0,
            'errors': []
        }
        
        try:
            # 1. Анализ трендов и популярных тем
            logger.info("📊 Анализ трендов...")
            trends = self.trend_analyzer.analyze_current_trends()
            results['trends_analyzed'] = len(trends)
            
            # 2. Создание новых категорий на основе трендов
            logger.info("📂 Создание категорий...")
            new_categories = self.category_manager.create_trending_categories(trends)
            results['categories_created'] = len(new_categories)
            
            # 3. Генерация тегов для новых категорий
            logger.info("🏷️ Генерация тегов...")
            new_tags = self.tag_manager.generate_tags_for_categories(new_categories)
            results['tags_created'] = len(new_tags)
            
            # 4. Планирование контента
            logger.info("📅 Планирование контента...")
            content_plan = self.content_planner.create_content_plan(trends, new_categories)
            
            # 5. Генерация контента
            logger.info("✍️ Генерация контента...")
            generated_posts = self.generate_content_batch(content_plan)
            results['posts_generated'] = len(generated_posts)
            
            # 6. Обновление статистики
            self.stats.update({
                'categories_created': self.stats['categories_created'] + results['categories_created'],
                'tags_created': self.stats['tags_created'] + results['tags_created'],
                'posts_generated': self.stats['posts_generated'] + results['posts_generated'],
                'trends_analyzed': self.stats['trends_analyzed'] + results['trends_analyzed'],
                'last_analysis': datetime.now()
            })
            
            logger.info(f"✅ Автономный цикл завершен: {results}")
            
        except Exception as e:
            error_msg = f"Ошибка в автономном цикле: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            log_security_event('ai_autonomous_error', {'error': str(e)})
        
        return results
    
    def generate_content_batch(self, content_plan: List[Dict]) -> List[Post]:
        """Генерация пакета контента по плану"""
        generated_posts = []
        
        for plan_item in content_plan:
            try:
                # Генерируем пост
                post_data = self.ai_generator.generate_human_like_post(
                    category_name=plan_item['category'],
                    topic=plan_item['topic'],
                    style=plan_item.get('style', 'balanced'),
                    length=plan_item.get('length', 'medium')
                )
                
                # Создаем пост в базе данных
                post = self.create_post_from_data(post_data, plan_item)
                if post:
                    generated_posts.append(post)
                    
            except Exception as e:
                logger.error(f"Ошибка генерации поста для {plan_item}: {e}")
        
        return generated_posts
    
    def create_post_from_data(self, post_data: Dict, plan_item: Dict) -> Optional[Post]:
        """Создание поста в базе данных из сгенерированных данных"""
        try:
            # Находим или создаем категорию
            category = Category.query.filter_by(name=post_data['category']).first()
            if not category:
                category = Category(
                    name=post_data['category'],
                    description=f"Категория для тем: {', '.join(post_data['tags'][:3])}",
                    color=self.get_category_color(post_data['category'])
                )
                db.session.add(category)
                db.session.commit()
            
            # Находим автора (используем первого админа или создаем ИИ автора)
            author = User.query.filter_by(is_admin=True).first()
            if not author:
                author = self.create_ai_author()
            
            # Создаем пост
            post = Post(
                title=post_data['title'],
                content=post_data['content'],
                excerpt=post_data.get('excerpt', post_data['content'][:200] + '...'),
                category_id=category.id,
                author_id=author.id,
                is_published=True,
                is_featured=plan_item.get('featured', False),
                published_at=datetime.utcnow()
            )
            
            db.session.add(post)
            db.session.commit()
            
            # Добавляем теги
            self.add_tags_to_post(post, post_data['tags'])
            
            logger.info(f"✅ Создан пост: {post.title}")
            return post
            
        except Exception as e:
            logger.error(f"Ошибка создания поста: {e}")
            db.session.rollback()
            return None
    
    def create_ai_author(self) -> User:
        """Создание ИИ автора"""
        import secrets
        import string
        
        # Генерируем случайный пароль для безопасности
        ai_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
        
        ai_author = User(
            username='ai_author',
            email='ai@blog.com',
            first_name='ИИ',
            last_name='Автор',
            bio='Автоматически созданный ИИ автор для генерации контента',
            is_admin=False
        )
        ai_author.set_password(ai_password)
        db.session.add(ai_author)
        db.session.commit()
        
        logger.info("✅ Создан ИИ автор с безопасным паролем")
        return ai_author
    
    def add_tags_to_post(self, post: Post, tag_names: List[str]):
        """Добавление тегов к посту"""
        for tag_name in tag_names[:5]:  # Максимум 5 тегов
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
                db.session.flush()  # Получаем ID
            
            post.tags.append(tag)
        
        db.session.commit()
    
    def get_category_color(self, category_name: str) -> str:
        """Получение цвета для категории"""
        colors = {
            'технологии': '#007bff',
            'наука': '#28a745',
            'общество': '#ffc107',
            'бизнес': '#dc3545',
            'здоровье': '#17a2b8',
            'спорт': '#6f42c1',
            'искусство': '#fd7e14',
            'путешествия': '#20c997',
            'образование': '#6c757d',
            'развлечения': '#e83e8c'
        }
        return colors.get(category_name.lower(), '#6c757d')

class TrendAnalyzer:
    """Анализатор трендов для определения популярных тем"""
    
    def __init__(self):
        self.trend_sources = [
            'https://trends.google.com/trends/api/dailytrends',
            'https://api.github.com/search/repositories',
            'https://newsapi.org/v2/top-headlines'
        ]
    
    def analyze_current_trends(self) -> List[Dict]:
        """Анализ текущих трендов"""
        trends = []
        
        # Анализируем существующий контент
        existing_trends = self.analyze_existing_content()
        trends.extend(existing_trends)
        
        # Анализируем внешние источники
        external_trends = self.analyze_external_sources()
        trends.extend(external_trends)
        
        # Генерируем тренды на основе времени года и событий
        seasonal_trends = self.generate_seasonal_trends()
        trends.extend(seasonal_trends)
        
        return trends[:10]  # Возвращаем топ-10 трендов
    
    def analyze_existing_content(self) -> List[Dict]:
        """Анализ существующего контента для выявления трендов"""
        trends = []
        
        # Анализируем популярные теги
        popular_tags = db.session.query(Tag.name, db.func.count(Tag.id)).join(
            Tag.posts
        ).group_by(Tag.name).order_by(db.func.count(Tag.id).desc()).limit(5).all()
        
        for tag_name, count in popular_tags:
            trends.append({
                'topic': tag_name,
                'category': self.categorize_topic(tag_name),
                'popularity': count,
                'source': 'existing_content',
                'confidence': min(count / 10, 1.0)
            })
        
        # Анализируем популярные категории
        popular_categories = db.session.query(Category.name, db.func.count(Post.id)).join(
            Category.posts
        ).group_by(Category.name).order_by(db.func.count(Post.id).desc()).limit(3).all()
        
        for cat_name, count in popular_categories:
            trends.append({
                'topic': f"новости в {cat_name}",
                'category': cat_name,
                'popularity': count,
                'source': 'existing_categories',
                'confidence': min(count / 5, 1.0)
            })
        
        return trends
    
    def analyze_external_sources(self) -> List[Dict]:
        """Анализ внешних источников трендов"""
        trends = []
        
        # Генерируем тренды на основе текущих событий
        current_trends = [
            {'topic': 'искусственный интеллект', 'category': 'технологии', 'confidence': 0.9},
            {'topic': 'устойчивое развитие', 'category': 'общество', 'confidence': 0.8},
            {'topic': 'цифровая трансформация', 'category': 'бизнес', 'confidence': 0.7},
            {'topic': 'здоровый образ жизни', 'category': 'здоровье', 'confidence': 0.8},
            {'topic': 'удаленная работа', 'category': 'бизнес', 'confidence': 0.7},
            {'topic': 'кибербезопасность', 'category': 'технологии', 'confidence': 0.8},
            {'topic': 'возобновляемая энергия', 'category': 'наука', 'confidence': 0.7},
            {'topic': 'виртуальная реальность', 'category': 'технологии', 'confidence': 0.6},
            {'topic': 'персонализация', 'category': 'технологии', 'confidence': 0.6},
            {'topic': 'социальные сети', 'category': 'общество', 'confidence': 0.7}
        ]
        
        for trend in current_trends:
            trend['source'] = 'external_analysis'
            trend['popularity'] = int(trend['confidence'] * 100)
            trends.append(trend)
        
        return trends
    
    def generate_seasonal_trends(self) -> List[Dict]:
        """Генерация сезонных трендов"""
        trends = []
        current_month = datetime.now().month
        
        seasonal_topics = {
            1: [{'topic': 'новогодние планы', 'category': 'общество'}, {'topic': 'зимние виды спорта', 'category': 'спорт'}],
            2: [{'topic': 'день святого валентина', 'category': 'общество'}, {'topic': 'зимние каникулы', 'category': 'путешествия'}],
            3: [{'topic': 'весенняя мода', 'category': 'искусство'}, {'topic': 'весенняя уборка', 'category': 'общество'}],
            4: [{'topic': 'пасхальные традиции', 'category': 'общество'}, {'topic': 'весенние сады', 'category': 'здоровье'}],
            5: [{'topic': 'майские праздники', 'category': 'путешествия'}, {'topic': 'весенние цветы', 'category': 'искусство'}],
            6: [{'topic': 'летние каникулы', 'category': 'путешествия'}, {'topic': 'летние виды спорта', 'category': 'спорт'}],
            7: [{'topic': 'летний отдых', 'category': 'путешествия'}, {'topic': 'летние фестивали', 'category': 'развлечения'}],
            8: [{'topic': 'летние фрукты', 'category': 'здоровье'}, {'topic': 'летние путешествия', 'category': 'путешествия'}],
            9: [{'topic': 'начало учебного года', 'category': 'образование'}, {'topic': 'осенняя мода', 'category': 'искусство'}],
            10: [{'topic': 'осенние листья', 'category': 'искусство'}, {'topic': 'хэллоуин', 'category': 'развлечения'}],
            11: [{'topic': 'осенние овощи', 'category': 'здоровье'}, {'topic': 'подготовка к зиме', 'category': 'общество'}],
            12: [{'topic': 'новогодние праздники', 'category': 'развлечения'}, {'topic': 'зимние рецепты', 'category': 'здоровье'}]
        }
        
        month_trends = seasonal_topics.get(current_month, [])
        for trend in month_trends:
            trend['source'] = 'seasonal'
            trend['popularity'] = 50
            trend['confidence'] = 0.6
            trends.append(trend)
        
        return trends
    
    def categorize_topic(self, topic: str) -> str:
        """Категоризация темы"""
        topic_lower = topic.lower()
        
        tech_keywords = ['технология', 'ии', 'искусственный интеллект', 'программирование', 'компьютер', 'интернет', 'цифровой']
        science_keywords = ['наука', 'исследование', 'открытие', 'эксперимент', 'ученый', 'лаборатория']
        society_keywords = ['общество', 'социальный', 'культура', 'традиция', 'обычай', 'сообщество']
        business_keywords = ['бизнес', 'экономика', 'финансы', 'предпринимательство', 'компания', 'рынок']
        health_keywords = ['здоровье', 'медицина', 'лечение', 'диета', 'фитнес', 'спорт']
        
        if any(keyword in topic_lower for keyword in tech_keywords):
            return 'технологии'
        elif any(keyword in topic_lower for keyword in science_keywords):
            return 'наука'
        elif any(keyword in topic_lower for keyword in society_keywords):
            return 'общество'
        elif any(keyword in topic_lower for keyword in business_keywords):
            return 'бизнес'
        elif any(keyword in topic_lower for keyword in health_keywords):
            return 'здоровье'
        else:
            return 'общество'  # По умолчанию

class CategoryManager:
    """Менеджер категорий с ИИ"""
    
    def create_trending_categories(self, trends: List[Dict]) -> List[Category]:
        """Создание категорий на основе трендов"""
        created_categories = []
        
        # Группируем тренды по категориям
        category_trends = defaultdict(list)
        for trend in trends:
            category_trends[trend['category']].append(trend)
        
        # Создаем категории
        for category_name, trend_list in category_trends.items():
            # Проверяем, существует ли категория
            existing_category = Category.query.filter_by(name=category_name).first()
            if existing_category:
                continue
            
            # Создаем новую категорию
            category = Category(
                name=category_name,
                description=self.generate_category_description(category_name, trend_list),
                color=self.get_category_color(category_name)
            )
            
            db.session.add(category)
            created_categories.append(category)
            
            logger.info(f"✅ Создана категория: {category_name}")
        
        db.session.commit()
        return created_categories
    
    def generate_category_description(self, category_name: str, trends: List[Dict]) -> str:
        """Генерация описания категории на основе трендов"""
        trend_topics = [trend['topic'] for trend in trends[:3]]
        
        descriptions = {
            'технологии': f"Современные технологии и инновации. Популярные темы: {', '.join(trend_topics)}",
            'наука': f"Научные открытия и исследования. Актуальные направления: {', '.join(trend_topics)}",
            'общество': f"Социальные вопросы и культура. Текущие обсуждения: {', '.join(trend_topics)}",
            'бизнес': f"Предпринимательство и экономика. Тренды рынка: {', '.join(trend_topics)}",
            'здоровье': f"Здоровый образ жизни и медицина. Популярные темы: {', '.join(trend_topics)}",
            'спорт': f"Спорт и физическая активность. Актуальные события: {', '.join(trend_topics)}",
            'искусство': f"Культура и творчество. Современные тенденции: {', '.join(trend_topics)}",
            'путешествия': f"Туризм и путешествия. Популярные направления: {', '.join(trend_topics)}",
            'образование': f"Обучение и развитие. Современные подходы: {', '.join(trend_topics)}",
            'развлечения': f"Досуг и развлечения. Популярные активности: {', '.join(trend_topics)}"
        }
        
        return descriptions.get(category_name, f"Категория {category_name}. Популярные темы: {', '.join(trend_topics)}")
    
    def get_category_color(self, category_name: str) -> str:
        """Получение цвета для категории"""
        colors = {
            'технологии': '#007bff',
            'наука': '#28a745',
            'общество': '#ffc107',
            'бизнес': '#dc3545',
            'здоровье': '#17a2b8',
            'спорт': '#6f42c1',
            'искусство': '#fd7e14',
            'путешествия': '#20c997',
            'образование': '#6c757d',
            'развлечения': '#e83e8c'
        }
        return colors.get(category_name.lower(), '#6c757d')

class TagManager:
    """Менеджер тегов с ИИ"""
    
    def generate_tags_for_categories(self, categories: List[Category]) -> List[Tag]:
        """Генерация тегов для категорий"""
        created_tags = []
        
        for category in categories:
            # Генерируем теги для категории
            tags = self.generate_category_tags(category.name)
            
            for tag_name in tags:
                # Проверяем, существует ли тег
                existing_tag = Tag.query.filter_by(name=tag_name).first()
                if existing_tag:
                    continue
                
                # Создаем новый тег
                tag = Tag(name=tag_name)
                db.session.add(tag)
                created_tags.append(tag)
                
                logger.info(f"✅ Создан тег: {tag_name}")
        
        db.session.commit()
        return created_tags
    
    def generate_category_tags(self, category_name: str) -> List[str]:
        """Генерация тегов для конкретной категории"""
        tag_templates = {
            'технологии': ['ии', 'машинное обучение', 'блокчейн', 'веб-разработка', 'мобильные приложения', 'кибербезопасность', 'облачные технологии', 'интернет вещей', 'большие данные', 'виртуальная реальность'],
            'наука': ['космос', 'биология', 'физика', 'химия', 'экология', 'генетика', 'нейронауки', 'математика', 'археология', 'геология'],
            'общество': ['образование', 'культура', 'искусство', 'история', 'философия', 'психология', 'социология', 'политика', 'экономика', 'спорт'],
            'бизнес': ['предпринимательство', 'стартапы', 'инвестиции', 'маркетинг', 'продажи', 'менеджмент', 'финансы', 'консалтинг', 'лидерство', 'инновации'],
            'здоровье': ['медицина', 'фитнес', 'диета', 'психическое здоровье', 'профилактика', 'лечение', 'здоровый образ жизни', 'спорт', 'питание', 'релаксация'],
            'спорт': ['футбол', 'баскетбол', 'теннис', 'плавание', 'бег', 'йога', 'фитнес', 'олимпиада', 'чемпионат', 'тренировки'],
            'искусство': ['живопись', 'скульптура', 'музыка', 'театр', 'кино', 'литература', 'фотография', 'дизайн', 'архитектура', 'мода'],
            'путешествия': ['туризм', 'отдых', 'города', 'страны', 'культура', 'традиции', 'кухня', 'достопримечательности', 'приключения', 'открытия'],
            'образование': ['обучение', 'школа', 'университет', 'курсы', 'навыки', 'развитие', 'знания', 'методики', 'технологии обучения', 'самообразование'],
            'развлечения': ['игры', 'фильмы', 'сериалы', 'музыка', 'книги', 'хобби', 'события', 'фестивали', 'концерты', 'вечеринки']
        }
        
        base_tags = tag_templates.get(category_name.lower(), ['общее', 'интересное', 'популярное'])
        
        # Добавляем случайные вариации
        variations = ['новое', 'актуальное', 'тренд', '2024', 'современное', 'популярное']
        additional_tags = random.sample(variations, min(2, len(variations)))
        
        return base_tags[:5] + additional_tags

class ContentPlanner:
    """Планировщик контента с ИИ"""
    
    def create_content_plan(self, trends: List[Dict], categories: List[Category]) -> List[Dict]:
        """Создание плана контента"""
        content_plan = []
        
        # Планируем контент на основе трендов
        for trend in trends[:5]:  # Топ-5 трендов
            plan_item = {
                'topic': trend['topic'],
                'category': trend['category'],
                'style': self.choose_content_style(trend),
                'length': self.choose_content_length(trend),
                'featured': trend.get('confidence', 0) > 0.8,
                'priority': trend.get('popularity', 50)
            }
            content_plan.append(plan_item)
        
        # Планируем контент для новых категорий
        for category in categories:
            plan_item = {
                'topic': f"введение в {category.name}",
                'category': category.name,
                'style': 'educational',
                'length': 'medium',
                'featured': True,
                'priority': 80
            }
            content_plan.append(plan_item)
        
        # Сортируем по приоритету
        content_plan.sort(key=lambda x: x['priority'], reverse=True)
        
        return content_plan[:10]  # Максимум 10 постов за раз
    
    def choose_content_style(self, trend: Dict) -> str:
        """Выбор стиля контента на основе тренда"""
        styles = ['analytical', 'conversational', 'educational', 'news', 'opinion']
        
        # Выбираем стиль на основе источника тренда
        if trend.get('source') == 'external_analysis':
            return random.choice(['analytical', 'news'])
        elif trend.get('source') == 'seasonal':
            return random.choice(['conversational', 'educational'])
        else:
            return random.choice(styles)
    
    def choose_content_length(self, trend: Dict) -> str:
        """Выбор длины контента"""
        lengths = ['short', 'medium', 'long']
        
        # Более популярные тренды получают более длинный контент
        if trend.get('popularity', 50) > 70:
            return 'long'
        elif trend.get('popularity', 50) > 40:
            return 'medium'
        else:
            return 'short'

# Глобальный экземпляр автономного менеджера
autonomous_manager = AutonomousContentManager()

def start_autonomous_content_generation():
    """Запуск автономной генерации контента"""
    logger.info("🚀 Запуск автономной генерации контента")
    
    try:
        results = autonomous_manager.run_autonomous_cycle()
        
        logger.info(f"✅ Автономная генерация завершена: {results}")
        return results
        
    except Exception as e:
        logger.error(f"❌ Ошибка автономной генерации: {e}")
        return {'error': str(e)}

def get_autonomous_stats() -> Dict:
    """Получение статистики автономной системы"""
    return autonomous_manager.stats