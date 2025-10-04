"""
Расширенная SEO система для блога
Включает продвинутые возможности: A/B тестирование, конкурентный анализ, техническое SEO
"""

import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
import math
import sqlite3
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

from blog.models import Post, Category, Tag, User, View
from blog import db

class TechnicalSEOChecker:
    """Техническое SEO - проверка производительности и структуры"""
    
    def __init__(self):
        self.critical_issues = []
        self.warnings = []
        self.suggestions = []
    
    def check_page_speed(self, url: str) -> Dict:
        """Проверка скорости загрузки страницы"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            load_time = time.time() - start_time
            
            speed_score = 100
            if load_time > 3:
                speed_score = 20
                self.critical_issues.append(f"Страница загружается слишком медленно: {load_time:.2f}с")
            elif load_time > 2:
                speed_score = 50
                self.warnings.append(f"Страница загружается медленно: {load_time:.2f}с")
            elif load_time > 1:
                speed_score = 80
                self.suggestions.append(f"Можно улучшить скорость загрузки: {load_time:.2f}с")
            
            return {
                'load_time': load_time,
                'speed_score': speed_score,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'headers': dict(response.headers)
            }
        except Exception as e:
            self.critical_issues.append(f"Ошибка проверки скорости: {str(e)}")
            return {'error': str(e)}
    
    def check_mobile_friendliness(self, url: str) -> Dict:
        """Проверка мобильной адаптивности"""
        try:
            response = requests.get(url, timeout=10)
            content = response.text
            
            # Проверка viewport
            viewport_meta = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', content, re.IGNORECASE)
            has_viewport = bool(viewport_meta)
            
            # Проверка адаптивных элементов
            responsive_elements = {
                'flexbox': 'flex' in content.lower(),
                'grid': 'grid' in content.lower(),
                'bootstrap': 'bootstrap' in content.lower(),
                'media_queries': '@media' in content.lower()
            }
            
            mobile_score = 0
            if has_viewport:
                mobile_score += 40
            else:
                self.critical_issues.append("Отсутствует viewport meta тег")
            
            responsive_count = sum(responsive_elements.values())
            mobile_score += min(responsive_count * 15, 60)
            
            if responsive_count < 2:
                self.warnings.append("Мало адаптивных элементов")
            
            return {
                'mobile_score': mobile_score,
                'has_viewport': has_viewport,
                'responsive_elements': responsive_elements,
                'responsive_count': responsive_count
            }
        except Exception as e:
            self.critical_issues.append(f"Ошибка проверки мобильности: {str(e)}")
            return {'error': str(e)}
    
    def check_ssl_certificate(self, url: str) -> Dict:
        """Проверка SSL сертификата"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme == 'https':
                response = requests.get(url, timeout=10, verify=True)
                return {
                    'ssl_enabled': True,
                    'ssl_valid': True,
                    'ssl_score': 100
                }
            else:
                self.critical_issues.append("Сайт не использует HTTPS")
                return {
                    'ssl_enabled': False,
                    'ssl_valid': False,
                    'ssl_score': 0
                }
        except requests.exceptions.SSLError:
            self.critical_issues.append("Проблемы с SSL сертификатом")
            return {
                'ssl_enabled': True,
                'ssl_valid': False,
                'ssl_score': 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def check_structured_data(self, url: str) -> Dict:
        """Проверка структурированных данных"""
        try:
            response = requests.get(url, timeout=10)
            content = response.text
            
            # Поиск JSON-LD
            json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            json_ld_matches = re.findall(json_ld_pattern, content, re.DOTALL | re.IGNORECASE)
            
            # Поиск микроданных
            microdata_pattern = r'itemscope|itemtype|itemprop'
            microdata_matches = re.findall(microdata_pattern, content, re.IGNORECASE)
            
            # Поиск RDFa
            rdfa_pattern = r'typeof|property|vocab'
            rdfa_matches = re.findall(rdfa_pattern, content, re.IGNORECASE)
            
            structured_data_score = 0
            structured_types = []
            
            if json_ld_matches:
                structured_data_score += 50
                structured_types.append('JSON-LD')
            
            if microdata_matches:
                structured_data_score += 30
                structured_types.append('Microdata')
            
            if rdfa_matches:
                structured_data_score += 20
                structured_types.append('RDFa')
            
            if structured_data_score == 0:
                self.warnings.append("Отсутствуют структурированные данные")
            
            return {
                'structured_data_score': structured_data_score,
                'json_ld_count': len(json_ld_matches),
                'microdata_count': len(microdata_matches),
                'rdfa_count': len(rdfa_matches),
                'structured_types': structured_types
            }
        except Exception as e:
            return {'error': str(e)}

class CompetitorAnalyzer:
    """Анализ конкурентов и ключевых слов"""
    
    def __init__(self):
        self.competitor_data = {}
        self.keyword_rankings = {}
    
    def analyze_competitor_keywords(self, competitor_url: str) -> Dict:
        """Анализ ключевых слов конкурента"""
        try:
            response = requests.get(competitor_url, timeout=10)
            content = response.text
            
            # Извлечение мета-тегов
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            description_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\'][^>]*>', content, re.IGNORECASE)
            keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\'][^>]*>', content, re.IGNORECASE)
            
            # Извлечение заголовков
            headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', content, re.IGNORECASE | re.DOTALL)
            
            # Анализ контента
            content_text = re.sub(r'<[^>]+>', '', content)
            words = re.findall(r'\b[а-яё]{3,}\b', content_text.lower())
            word_freq = Counter(words)
            
            return {
                'title': title_match.group(1).strip() if title_match else '',
                'description': description_match.group(1) if description_match else '',
                'keywords': keywords_match.group(1) if keywords_match else '',
                'headings': [h.strip() for h in headings],
                'top_keywords': word_freq.most_common(20),
                'word_count': len(words),
                'analysis_date': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def find_keyword_gaps(self, our_keywords: List[str], competitor_keywords: List[str]) -> Dict:
        """Поиск пробелов в ключевых словах"""
        our_set = set(our_keywords)
        competitor_set = set(competitor_keywords)
        
        gaps = competitor_set - our_set
        opportunities = our_set - competitor_set
        
        return {
            'keyword_gaps': list(gaps),
            'our_opportunities': list(opportunities),
            'common_keywords': list(our_set & competitor_set),
            'gap_count': len(gaps),
            'opportunity_count': len(opportunities)
        }

class ABTestingManager:
    """A/B тестирование для SEO"""
    
    def __init__(self):
        self.tests = {}
        self.results = {}
    
    def create_title_test(self, post_id: int, variant_a: str, variant_b: str) -> str:
        """Создание A/B теста для заголовков"""
        test_id = f"title_test_{post_id}_{int(time.time())}"
        
        self.tests[test_id] = {
            'type': 'title',
            'post_id': post_id,
            'variant_a': variant_a,
            'variant_b': variant_b,
            'created_at': datetime.now(),
            'status': 'active',
            'visitors_a': 0,
            'visitors_b': 0,
            'clicks_a': 0,
            'clicks_b': 0
        }
        
        return test_id
    
    def create_description_test(self, post_id: int, variant_a: str, variant_b: str) -> str:
        """Создание A/B теста для описаний"""
        test_id = f"description_test_{post_id}_{int(time.time())}"
        
        self.tests[test_id] = {
            'type': 'description',
            'post_id': post_id,
            'variant_a': variant_a,
            'variant_b': variant_b,
            'created_at': datetime.now(),
            'status': 'active',
            'visitors_a': 0,
            'visitors_b': 0,
            'clicks_a': 0,
            'clicks_b': 0
        }
        
        return test_id
    
    def get_test_variant(self, test_id: str, user_id: str = None) -> str:
        """Получение варианта для пользователя"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # Простое разделение 50/50 на основе хеша
        if user_id:
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        else:
            hash_value = int(hashlib.md5(str(time.time()).encode()).hexdigest(), 16)
        
        variant = 'a' if hash_value % 2 == 0 else 'b'
        
        # Увеличиваем счетчик посетителей
        if variant == 'a':
            test['visitors_a'] += 1
        else:
            test['visitors_b'] += 1
        
        return test[f'variant_{variant}']
    
    def record_click(self, test_id: str, variant: str):
        """Запись клика по варианту"""
        if test_id in self.tests:
            if variant == 'a':
                self.tests[test_id]['clicks_a'] += 1
            else:
                self.tests[test_id]['clicks_b'] += 1
    
    def get_test_results(self, test_id: str) -> Dict:
        """Получение результатов теста"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        ctr_a = (test['clicks_a'] / test['visitors_a']) * 100 if test['visitors_a'] > 0 else 0
        ctr_b = (test['clicks_b'] / test['visitors_b']) * 100 if test['visitors_b'] > 0 else 0
        
        winner = 'a' if ctr_a > ctr_b else 'b' if ctr_b > ctr_a else 'tie'
        
        return {
            'test_id': test_id,
            'type': test['type'],
            'visitors_a': test['visitors_a'],
            'visitors_b': test['visitors_b'],
            'clicks_a': test['clicks_a'],
            'clicks_b': test['clicks_b'],
            'ctr_a': round(ctr_a, 2),
            'ctr_b': round(ctr_b, 2),
            'winner': winner,
            'confidence': self._calculate_confidence(test),
            'status': test['status']
        }
    
    def _calculate_confidence(self, test: Dict) -> float:
        """Расчет статистической значимости"""
        # Упрощенный расчет доверительного интервала
        total_visitors = test['visitors_a'] + test['visitors_b']
        if total_visitors < 100:
            return 0.0
        
        # Более точный расчет требует статистических библиотек
        return min(95.0, (total_visitors / 1000) * 100)

class SEOMonitoring:
    """Мониторинг SEO показателей"""
    
    def __init__(self):
        self.metrics_history = defaultdict(list)
        self.alerts = []
    
    def track_keyword_ranking(self, keyword: str, position: int, url: str):
        """Отслеживание позиций ключевых слов"""
        self.metrics_history[f'keyword_{keyword}'].append({
            'position': position,
            'url': url,
            'date': datetime.now(),
            'change': self._calculate_position_change(keyword, position)
        })
        
        # Алерт при значительном изменении
        if position > 20:
            self.alerts.append({
                'type': 'warning',
                'message': f'Ключевое слово "{keyword}" выпало из ТОП-20 (позиция {position})',
                'date': datetime.now()
            })
    
    def track_page_speed(self, url: str, load_time: float):
        """Отслеживание скорости загрузки"""
        self.metrics_history[f'speed_{url}'].append({
            'load_time': load_time,
            'date': datetime.now(),
            'score': 100 - (load_time * 20)  # Простая формула оценки
        })
        
        if load_time > 3:
            self.alerts.append({
                'type': 'critical',
                'message': f'Критически медленная загрузка: {url} ({load_time:.2f}с)',
                'date': datetime.now()
            })
    
    def track_crawl_errors(self, url: str, error_type: str, error_message: str):
        """Отслеживание ошибок индексации"""
        self.metrics_history[f'crawl_{url}'].append({
            'error_type': error_type,
            'error_message': error_message,
            'date': datetime.now()
        })
        
        self.alerts.append({
            'type': 'error',
            'message': f'Ошибка индексации {url}: {error_message}',
            'date': datetime.now()
        })
    
    def _calculate_position_change(self, keyword: str, current_position: int) -> int:
        """Расчет изменения позиции"""
        history = self.metrics_history[f'keyword_{keyword}']
        if len(history) < 2:
            return 0
        
        previous_position = history[-2]['position']
        return current_position - previous_position
    
    def get_seo_dashboard_data(self) -> Dict:
        """Получение данных для SEO дашборда"""
        total_keywords = len([k for k in self.metrics_history.keys() if k.startswith('keyword_')])
        total_pages = len([k for k in self.metrics_history.keys() if k.startswith('speed_')])
        
        recent_alerts = [alert for alert in self.alerts if (datetime.now() - alert['date']).days <= 7]
        
        return {
            'total_keywords_tracked': total_keywords,
            'total_pages_monitored': total_pages,
            'recent_alerts': recent_alerts,
            'alert_count': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a['type'] == 'critical']),
            'warning_alerts': len([a for a in recent_alerts if a['type'] == 'warning']),
            'error_alerts': len([a for a in recent_alerts if a['type'] == 'error'])
        }

class AdvancedSEOOptimizer:
    """Расширенный SEO оптимизатор"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.technical_checker = TechnicalSEOChecker()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.ab_testing = ABTestingManager()
        self.monitoring = SEOMonitoring()
        
        # Импорт базовых компонентов
        # from blog.seo_optimizer import SEOAnalyzer, MetaTagGenerator, StructuredDataGenerator  # Циклический импорт
        
        # Создаем заглушки для избежания циклического импорта
        class SEOAnalyzer:
            def analyze_post(self, post): return {}
            def analyze_page(self, url): return {}
        
        class MetaTagGenerator:
            def __init__(self, base_url): self.base_url = base_url
            def generate_post_meta(self, post): return {}
            def generate_category_meta(self, category): return {}
            def generate_home_meta(self): return {}
        
        class StructuredDataGenerator:
            def __init__(self, base_url): self.base_url = base_url
            def generate_post_schema(self, post): return {}
            def generate_category_schema(self, category): return {}
        
        self.analyzer = SEOAnalyzer()
        self.meta_generator = MetaTagGenerator(base_url)
        self.schema_generator = StructuredDataGenerator(base_url)
    
    def comprehensive_seo_audit(self, post: Post) -> Dict:
        """Комплексный SEO аудит поста"""
        post_url = f"{self.base_url}/blog/post/{post.slug}"
        
        # Базовый SEO анализ
        basic_seo = self.analyzer.check_seo_issues(post)
        
        # Техническое SEO
        technical_seo = {
            'page_speed': self.technical_checker.check_page_speed(post_url),
            'mobile_friendliness': self.technical_checker.check_mobile_friendliness(post_url),
            'ssl_certificate': self.technical_checker.check_ssl_certificate(post_url),
            'structured_data': self.technical_checker.check_structured_data(post_url)
        }
        
        # Контентный анализ
        content_analysis = {
            'readability': self.analyzer.analyze_readability(post.content),
            'keywords': self.analyzer.extract_keywords(post.content),
            'keyword_density': self._calculate_keyword_density(post),
            'content_structure': self._analyze_content_structure(post)
        }
        
        # Общий SEO рейтинг
        overall_score = self._calculate_comprehensive_score(basic_seo, technical_seo, content_analysis)
        
        return {
            'post_id': post.id,
            'post_title': post.title,
            'post_url': post_url,
            'basic_seo': basic_seo,
            'technical_seo': technical_seo,
            'content_analysis': content_analysis,
            'overall_score': overall_score,
            'recommendations': self._generate_recommendations(basic_seo, technical_seo, content_analysis),
            'audit_date': datetime.now().isoformat()
        }
    
    def _calculate_keyword_density(self, post: Post) -> Dict:
        """Расчет плотности ключевых слов"""
        keywords = self.analyzer.extract_keywords(post.content, max_keywords=10)
        densities = {}
        
        for keyword, count in keywords:
            density = self.analyzer.calculate_keyword_density(post.content, keyword)
            densities[keyword] = {
                'count': count,
                'density': round(density, 2),
                'status': 'optimal' if 1 <= density <= 3 else 'low' if density < 1 else 'high'
            }
        
        return densities
    
    def _analyze_content_structure(self, post: Post) -> Dict:
        """Анализ структуры контента"""
        content = post.content
        
        # Подсчет заголовков
        h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
        
        # Подсчет изображений
        img_count = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
        img_with_alt = len(re.findall(r'<img[^>]*alt=["\'][^"\']*["\'][^>]*>', content, re.IGNORECASE))
        
        # Подсчет ссылок
        link_count = len(re.findall(r'<a[^>]*href=["\'][^"\']*["\'][^>]*>', content, re.IGNORECASE))
        internal_links = len(re.findall(r'<a[^>]*href=["\'][^"\']*blog/post/[^"\']*["\'][^>]*>', content, re.IGNORECASE))
        
        return {
            'headings': {
                'h1': h1_count,
                'h2': h2_count,
                'h3': h3_count,
                'total': h1_count + h2_count + h3_count
            },
            'images': {
                'total': img_count,
                'with_alt': img_with_alt,
                'alt_coverage': (img_with_alt / img_count * 100) if img_count > 0 else 0
            },
            'links': {
                'total': link_count,
                'internal': internal_links,
                'external': link_count - internal_links,
                'internal_ratio': (internal_links / link_count * 100) if link_count > 0 else 0
            }
        }
    
    def _calculate_comprehensive_score(self, basic_seo: List, technical_seo: Dict, content_analysis: Dict) -> int:
        """Расчет комплексного SEO рейтинга"""
        score = 100
        
        # Штрафы за базовые проблемы
        for issue in basic_seo:
            if issue['type'] == 'error':
                score -= 20
            elif issue['type'] == 'warning':
                score -= 10
            elif issue['type'] == 'info':
                score -= 5
        
        # Техническое SEO
        if 'page_speed' in technical_seo and 'speed_score' in technical_seo['page_speed']:
            score += (technical_seo['page_speed']['speed_score'] - 50) / 2
        
        if 'mobile_friendliness' in technical_seo and 'mobile_score' in technical_seo['mobile_friendliness']:
            score += (technical_seo['mobile_friendliness']['mobile_score'] - 50) / 2
        
        # Контентный анализ
        readability_score = content_analysis['readability']['score']
        if readability_score < 30:
            score -= 15
        elif readability_score < 50:
            score -= 10
        
        return max(0, min(100, int(score)))
    
    def _generate_recommendations(self, basic_seo: List, technical_seo: Dict, content_analysis: Dict) -> List[str]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []
        
        # Рекомендации на основе базового SEO
        for issue in basic_seo:
            if issue['type'] == 'error':
                recommendations.append(f"КРИТИЧНО: {issue['message']}")
            elif issue['type'] == 'warning':
                recommendations.append(f"ВАЖНО: {issue['message']}")
        
        # Технические рекомендации
        if 'page_speed' in technical_seo and technical_seo['page_speed'].get('speed_score', 100) < 80:
            recommendations.append("Оптимизируйте скорость загрузки страницы")
        
        if 'mobile_friendliness' in technical_seo and technical_seo['mobile_friendliness'].get('mobile_score', 100) < 80:
            recommendations.append("Улучшите мобильную адаптивность")
        
        # Контентные рекомендации
        readability = content_analysis['readability']['score']
        if readability < 50:
            recommendations.append("Упростите текст для лучшей читаемости")
        
        keyword_count = len(content_analysis['keywords'])
        if keyword_count < 5:
            recommendations.append("Добавьте больше релевантных ключевых слов")
        
        return recommendations
    
    def create_seo_test(self, post: Post, test_type: str, variant_a: str, variant_b: str) -> str:
        """Создание SEO A/B теста"""
        if test_type == 'title':
            return self.ab_testing.create_title_test(post.id, variant_a, variant_b)
        elif test_type == 'description':
            return self.ab_testing.create_description_test(post.id, variant_a, variant_b)
        else:
            raise ValueError(f"Неподдерживаемый тип теста: {test_type}")
    
    def get_seo_analytics(self) -> Dict:
        """Получение SEO аналитики"""
        # Анализ всех постов
        posts = Post.query.filter_by(is_published=True).all()
        
        total_posts = len(posts)
        posts_with_good_seo = 0
        posts_with_issues = 0
        
        for post in posts:
            issues = self.analyzer.check_seo_issues(post)
            if len(issues) == 0:
                posts_with_good_seo += 1
            else:
                posts_with_issues += 1
        
        # Данные мониторинга
        dashboard_data = self.monitoring.get_seo_dashboard_data()
        
        return {
            'total_posts': total_posts,
            'posts_with_good_seo': posts_with_good_seo,
            'posts_with_issues': posts_with_issues,
            'seo_health_percentage': (posts_with_good_seo / total_posts * 100) if total_posts > 0 else 0,
            'monitoring': dashboard_data,
            'active_tests': len([t for t in self.ab_testing.tests.values() if t['status'] == 'active']),
            'last_audit': datetime.now().isoformat()
        }

# Глобальный экземпляр расширенного SEO оптимизатора
advanced_seo_optimizer = AdvancedSEOOptimizer()