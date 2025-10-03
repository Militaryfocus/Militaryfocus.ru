"""
Автоматическая SEO оптимизация для блога
Генерирует метатеги, структурированные данные, sitemap и оптимизирует контент
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from collections import Counter
import math

from blog.models import Post, Category, Tag, User
from blog import db

class SEOAnalyzer:
    """Анализатор SEO контента"""
    
    def __init__(self):
        # Стоп-слова для русского языка
        self.stop_words = {
            'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так',
            'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было',
            'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг',
            'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж',
            'вам', 'сказал', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где',
            'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто',
            'человек', 'чего', 'раз', 'тоже', 'себе', 'под', 'жизнь', 'будет', 'ж', 'тогда', 'кто', 'этот',
            'говорил', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти',
            'мой', 'тем', 'чтобы', 'нее', 'кажется', 'сейчас', 'были', 'куда', 'зачем', 'сказать', 'всех',
            'никогда', 'сегодня', 'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над',
            'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве', 'сказала',
            'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том',
            'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между'
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[Tuple[str, int]]:
        """Извлечение ключевых слов из текста"""
        # Очистка текста от HTML и специальных символов
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text.lower())
        
        # Разбиение на слова
        words = clean_text.split()
        
        # Фильтрация стоп-слов и коротких слов
        filtered_words = [
            word for word in words 
            if len(word) > 3 and word not in self.stop_words
        ]
        
        # Подсчет частоты
        word_freq = Counter(filtered_words)
        
        # Возврат топ ключевых слов
        return word_freq.most_common(max_keywords)
    
    def calculate_keyword_density(self, text: str, keyword: str) -> float:
        """Расчет плотности ключевого слова"""
        clean_text = re.sub(r'<[^>]+>', '', text.lower())
        words = clean_text.split()
        
        if not words:
            return 0.0
        
        keyword_count = clean_text.count(keyword.lower())
        return (keyword_count / len(words)) * 100
    
    def analyze_readability(self, text: str) -> Dict:
        """Анализ читаемости текста"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Подсчет предложений
        sentences = re.split(r'[.!?]+', clean_text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Подсчет слов
        words = clean_text.split()
        word_count = len(words)
        
        # Подсчет слогов (упрощенный алгоритм для русского языка)
        syllable_count = sum(self._count_syllables(word) for word in words)
        
        if sentence_count == 0 or word_count == 0:
            return {'score': 0, 'level': 'Неопределенный'}
        
        # Индекс читаемости Флеша (адаптированный для русского)
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count
        
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Определение уровня читаемости
        if flesch_score >= 90:
            level = 'Очень легкий'
        elif flesch_score >= 80:
            level = 'Легкий'
        elif flesch_score >= 70:
            level = 'Довольно легкий'
        elif flesch_score >= 60:
            level = 'Стандартный'
        elif flesch_score >= 50:
            level = 'Довольно сложный'
        elif flesch_score >= 30:
            level = 'Сложный'
        else:
            level = 'Очень сложный'
        
        return {
            'score': round(flesch_score, 1),
            'level': level,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 1)
        }
    
    def _count_syllables(self, word: str) -> int:
        """Подсчет слогов в слове (упрощенный алгоритм)"""
        vowels = 'аеёиоуыэюя'
        word = word.lower()
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        return max(1, syllable_count)
    
    def check_seo_issues(self, post: Post) -> List[Dict]:
        """Проверка SEO проблем поста"""
        issues = []
        
        # Проверка длины заголовка
        title_length = len(post.title)
        if title_length < 30:
            issues.append({
                'type': 'warning',
                'category': 'title',
                'message': f'Заголовок слишком короткий ({title_length} символов). Рекомендуется 30-60 символов.'
            })
        elif title_length > 60:
            issues.append({
                'type': 'warning',
                'category': 'title',
                'message': f'Заголовок слишком длинный ({title_length} символов). Рекомендуется 30-60 символов.'
            })
        
        # Проверка мета-описания
        if not post.excerpt or len(post.excerpt) < 120:
            issues.append({
                'type': 'error',
                'category': 'meta_description',
                'message': 'Отсутствует или слишком короткое мета-описание. Рекомендуется 120-160 символов.'
            })
        elif len(post.excerpt) > 160:
            issues.append({
                'type': 'warning',
                'category': 'meta_description',
                'message': f'Мета-описание слишком длинное ({len(post.excerpt)} символов).'
            })
        
        # Проверка длины контента
        word_count = len(post.content.split())
        if word_count < 300:
            issues.append({
                'type': 'warning',
                'category': 'content_length',
                'message': f'Контент слишком короткий ({word_count} слов). Рекомендуется минимум 300 слов.'
            })
        
        # Проверка заголовков H1-H6
        h_tags = re.findall(r'<h[1-6][^>]*>.*?</h[1-6]>', post.content_html or post.content, re.IGNORECASE)
        if not h_tags:
            issues.append({
                'type': 'warning',
                'category': 'headings',
                'message': 'В контенте отсутствуют заголовки (H1-H6).'
            })
        
        # Проверка изображений без alt
        img_tags = re.findall(r'<img[^>]*>', post.content_html or post.content, re.IGNORECASE)
        images_without_alt = [img for img in img_tags if 'alt=' not in img.lower()]
        if images_without_alt:
            issues.append({
                'type': 'warning',
                'category': 'images',
                'message': f'Найдено {len(images_without_alt)} изображений без alt-атрибута.'
            })
        
        # Проверка внутренних ссылок
        internal_links = re.findall(r'<a[^>]*href=["\'][^"\']*["\'][^>]*>', post.content_html or post.content, re.IGNORECASE)
        if len(internal_links) < 2:
            issues.append({
                'type': 'info',
                'category': 'internal_links',
                'message': 'Мало внутренних ссылок. Рекомендуется добавить ссылки на другие статьи.'
            })
        
        return issues

class MetaTagGenerator:
    """Генератор мета-тегов"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url.rstrip('/')
    
    def generate_post_meta(self, post: Post) -> Dict:
        """Генерация мета-тегов для поста"""
        # Извлечение ключевых слов
        analyzer = SEOAnalyzer()
        keywords = analyzer.extract_keywords(post.content, max_keywords=5)
        keyword_list = [kw[0] for kw in keywords]
        
        # URL поста
        post_url = f"{self.base_url}/blog/post/{post.slug}"
        
        # Изображение поста
        image_url = f"{self.base_url}{post.get_featured_image_url()}"
        
        meta_tags = {
            # Основные мета-теги
            'title': post.title,
            'description': post.excerpt or post.content[:160] + '...',
            'keywords': ', '.join(keyword_list),
            'author': post.author.get_full_name(),
            'robots': 'index, follow',
            'canonical': post_url,
            
            # Open Graph (Facebook)
            'og:title': post.title,
            'og:description': post.excerpt or post.content[:160] + '...',
            'og:url': post_url,
            'og:type': 'article',
            'og:image': image_url,
            'og:site_name': 'МойБлог',
            'og:locale': 'ru_RU',
            
            # Twitter Card
            'twitter:card': 'summary_large_image',
            'twitter:title': post.title,
            'twitter:description': post.excerpt or post.content[:160] + '...',
            'twitter:image': image_url,
            
            # Article specific
            'article:author': post.author.get_full_name(),
            'article:published_time': post.created_at.isoformat() if post.created_at else '',
            'article:modified_time': post.updated_at.isoformat() if post.updated_at else '',
            'article:section': post.category.name if post.category else '',
            'article:tag': ', '.join([tag.name for tag in post.tags])
        }
        
        return meta_tags
    
    def generate_category_meta(self, category: Category) -> Dict:
        """Генерация мета-тегов для категории"""
        category_url = f"{self.base_url}/blog/category/{category.slug}"
        
        return {
            'title': f"{category.name} - МойБлог",
            'description': category.description or f"Статьи по теме {category.name}",
            'canonical': category_url,
            'robots': 'index, follow',
            'og:title': f"{category.name} - МойБлог",
            'og:description': category.description or f"Статьи по теме {category.name}",
            'og:url': category_url,
            'og:type': 'website'
        }
    
    def generate_home_meta(self) -> Dict:
        """Генерация мета-тегов для главной страницы"""
        return {
            'title': 'МойБлог - Современный блог с ИИ контентом',
            'description': 'Современный блог на Python Flask с автоматическим наполнением контентом с помощью искусственного интеллекта',
            'keywords': 'блог, python, flask, искусственный интеллект, контент, статьи',
            'robots': 'index, follow',
            'canonical': self.base_url,
            'og:title': 'МойБлог - Современный блог с ИИ контентом',
            'og:description': 'Современный блог на Python Flask с автоматическим наполнением контентом',
            'og:url': self.base_url,
            'og:type': 'website',
            'og:site_name': 'МойБлог'
        }

class StructuredDataGenerator:
    """Генератор структурированных данных (JSON-LD)"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url.rstrip('/')
    
    def generate_article_schema(self, post: Post) -> Dict:
        """Генерация схемы статьи"""
        post_url = f"{self.base_url}/blog/post/{post.slug}"
        image_url = f"{self.base_url}{post.get_featured_image_url()}"
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": post.title,
            "description": post.excerpt or post.content[:160] + '...',
            "url": post_url,
            "datePublished": post.created_at.isoformat() if post.created_at else '',
            "dateModified": post.updated_at.isoformat() if post.updated_at else '',
            "author": {
                "@type": "Person",
                "name": post.author.get_full_name(),
                "url": f"{self.base_url}/author/{post.author.username}"
            },
            "publisher": {
                "@type": "Organization",
                "name": "МойБлог",
                "url": self.base_url,
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{self.base_url}/static/images/logo.png"
                }
            },
            "image": {
                "@type": "ImageObject",
                "url": image_url,
                "width": 800,
                "height": 400
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": post_url
            }
        }
        
        # Добавление категории
        if post.category:
            schema["articleSection"] = post.category.name
        
        # Добавление тегов
        if post.tags:
            schema["keywords"] = [tag.name for tag in post.tags]
        
        # Добавление рейтинга (если есть система оценок)
        if hasattr(post, 'rating') and post.rating:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": post.rating,
                "ratingCount": post.rating_count or 1
            }
        
        return schema
    
    def generate_website_schema(self) -> Dict:
        """Генерация схемы веб-сайта"""
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "МойБлог",
            "url": self.base_url,
            "description": "Современный блог с ИИ контентом",
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{self.base_url}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        }
    
    def generate_breadcrumb_schema(self, items: List[Dict]) -> Dict:
        """Генерация схемы хлебных крошек"""
        list_items = []
        
        for i, item in enumerate(items, 1):
            list_items.append({
                "@type": "ListItem",
                "position": i,
                "name": item['name'],
                "item": item['url']
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": list_items
        }

class SitemapGenerator:
    """Генератор sitemap.xml"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url.rstrip('/')
    
    def generate_sitemap(self) -> str:
        """Генерация sitemap.xml"""
        # Создание корневого элемента
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:news', 'http://www.google.com/schemas/sitemap-news/0.9')
        urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        
        # Главная страница
        self._add_url(urlset, self.base_url, priority='1.0', changefreq='daily')
        
        # Страницы категорий
        categories = Category.query.all()
        for category in categories:
            url = f"{self.base_url}/blog/category/{category.slug}"
            self._add_url(urlset, url, priority='0.8', changefreq='weekly')
        
        # Посты
        posts = Post.query.filter_by(is_published=True).all()
        for post in posts:
            url = f"{self.base_url}/blog/post/{post.slug}"
            lastmod = post.updated_at or post.created_at
            
            url_elem = self._add_url(urlset, url, priority='0.9', changefreq='monthly', lastmod=lastmod)
            
            # Добавление изображений
            if post.featured_image:
                image_elem = ET.SubElement(url_elem, 'image:image')
                ET.SubElement(image_elem, 'image:loc').text = f"{self.base_url}{post.get_featured_image_url()}"
                ET.SubElement(image_elem, 'image:title').text = post.title
                ET.SubElement(image_elem, 'image:caption').text = post.excerpt or post.title
        
        # Статические страницы
        static_pages = [
            ('/about', '0.5', 'monthly'),
            ('/contact', '0.5', 'monthly'),
            ('/search', '0.3', 'monthly')
        ]
        
        for page, priority, changefreq in static_pages:
            self._add_url(urlset, f"{self.base_url}{page}", priority=priority, changefreq=changefreq)
        
        # Преобразование в строку
        return ET.tostring(urlset, encoding='unicode', method='xml')
    
    def _add_url(self, parent, loc, priority=None, changefreq=None, lastmod=None):
        """Добавление URL в sitemap"""
        url_elem = ET.SubElement(parent, 'url')
        ET.SubElement(url_elem, 'loc').text = loc
        
        if lastmod:
            if hasattr(lastmod, 'strftime'):
                lastmod_str = lastmod.strftime('%Y-%m-%d')
            else:
                lastmod_str = str(lastmod)
            ET.SubElement(url_elem, 'lastmod').text = lastmod_str
        
        if changefreq:
            ET.SubElement(url_elem, 'changefreq').text = changefreq
        
        if priority:
            ET.SubElement(url_elem, 'priority').text = priority
        
        return url_elem
    
    def save_sitemap(self, filepath: str = 'static/sitemap.xml'):
        """Сохранение sitemap в файл"""
        sitemap_content = self.generate_sitemap()
        
        # Добавление XML декларации
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        full_content = xml_declaration + sitemap_content
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

class SEOOptimizer:
    """Основной класс SEO оптимизатора"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.analyzer = SEOAnalyzer()
        self.meta_generator = MetaTagGenerator(base_url)
        self.schema_generator = StructuredDataGenerator(base_url)
        self.sitemap_generator = SitemapGenerator(base_url)
    
    def generate_meta_tags(self, title: str, description: str, keywords: List[str], 
                          url: str = "", image: str = "", author: str = "") -> Dict[str, str]:
        """Генерация мета-тегов для страницы"""
        meta_tags = {
            'title': title[:60] if len(title) > 60 else title,
            'description': description[:160] if len(description) > 160 else description,
            'keywords': ', '.join(keywords[:10]) if keywords else '',
            'og:title': title,
            'og:description': description,
            'og:type': 'article',
            'og:url': url,
            'og:image': image,
            'twitter:card': 'summary_large_image',
            'twitter:title': title,
            'twitter:description': description,
            'twitter:image': image
        }
        
        if author:
            meta_tags['author'] = author
            meta_tags['og:author'] = author
        
        return meta_tags

    def optimize_post(self, post: Post) -> Dict:
        """Полная SEO оптимизация поста"""
        # Анализ SEO проблем
        seo_issues = self.analyzer.check_seo_issues(post)
        
        # Генерация мета-тегов
        meta_tags = self.meta_generator.generate_post_meta(post)
        
        # Генерация структурированных данных
        structured_data = self.schema_generator.generate_article_schema(post)
        
        # Анализ читаемости
        readability = self.analyzer.analyze_readability(post.content)
        
        # Извлечение ключевых слов
        keywords = self.analyzer.extract_keywords(post.content)
        
        return {
            'seo_issues': seo_issues,
            'meta_tags': meta_tags,
            'structured_data': structured_data,
            'readability': readability,
            'keywords': keywords,
            'seo_score': self._calculate_seo_score(seo_issues, readability, keywords)
        }
    
    def _calculate_seo_score(self, issues: List[Dict], readability: Dict, keywords: List) -> int:
        """Расчет SEO рейтинга (0-100)"""
        score = 100
        
        # Вычитаем баллы за проблемы
        for issue in issues:
            if issue['type'] == 'error':
                score -= 15
            elif issue['type'] == 'warning':
                score -= 10
            elif issue['type'] == 'info':
                score -= 5
        
        # Учитываем читаемость
        if readability['score'] < 30:
            score -= 20
        elif readability['score'] < 50:
            score -= 10
        
        # Учитываем количество ключевых слов
        if len(keywords) < 3:
            score -= 10
        
        return max(0, min(100, score))
    
    def generate_robots_txt(self) -> str:
        """Генерация robots.txt"""
        return f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {self.base_url}/static/sitemap.xml

# Запрещенные директории
Disallow: /admin/
Disallow: /ai/
Disallow: /auth/login
Disallow: /auth/register
Disallow: /static/uploads/

# Разрешенные для индексации
Allow: /blog/
Allow: /static/css/
Allow: /static/js/
Allow: /static/images/

# Задержка между запросами (в секундах)
Crawl-delay: 1
"""
    
    def update_all_seo(self):
        """Обновление SEO для всего сайта"""
        # Обновление sitemap
        self.sitemap_generator.save_sitemap()
        
        # Сохранение robots.txt
        with open('static/robots.txt', 'w', encoding='utf-8') as f:
            f.write(self.generate_robots_txt())
        
        print("SEO файлы обновлены: sitemap.xml, robots.txt")

# Глобальный экземпляр SEO оптимизатора
seo_optimizer = SEOOptimizer()