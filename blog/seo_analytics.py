"""
SEO аналитика и отчеты
"""

import json
import csv
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import io
import base64

from blog.models import Post, Category, Tag, View, Comment
from blog import db
from blog.advanced_seo import advanced_seo_optimizer

class SEOAnalytics:
    """SEO аналитика и отчеты"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_duration = 3600  # 1 час
    
    def get_comprehensive_analytics(self) -> Dict:
        """Комплексная SEO аналитика"""
        return {
            'overview': self._get_overview_metrics(),
            'content_analysis': self._get_content_analysis(),
            'performance_metrics': self._get_performance_metrics(),
            'keyword_analysis': self._get_keyword_analysis(),
            'technical_seo': self._get_technical_seo_metrics(),
            'competitor_analysis': self._get_competitor_analysis(),
            'trends': self._get_trend_analysis(),
            'recommendations': self._get_recommendations()
        }
    
    def _get_overview_metrics(self) -> Dict:
        """Общие метрики"""
        posts = Post.query.filter_by(is_published=True).all()
        
        total_posts = len(posts)
        total_views = sum(post.views_count for post in posts)
        total_comments = Comment.query.count()
        
        # SEO здоровье
        seo_health = 0
        posts_with_issues = 0
        
        for post in posts:
            issues = advanced_seo_optimizer.analyzer.check_seo_issues(post)
            if len(issues) == 0:
                seo_health += 1
            else:
                posts_with_issues += 1
        
        seo_health_percentage = (seo_health / total_posts * 100) if total_posts > 0 else 0
        
        return {
            'total_posts': total_posts,
            'total_views': total_views,
            'total_comments': total_comments,
            'seo_health_percentage': round(seo_health_percentage, 1),
            'posts_with_issues': posts_with_issues,
            'avg_views_per_post': round(total_views / total_posts, 1) if total_posts > 0 else 0,
            'avg_comments_per_post': round(total_comments / total_posts, 1) if total_posts > 0 else 0
        }
    
    def _get_content_analysis(self) -> Dict:
        """Анализ контента"""
        posts = Post.query.filter_by(is_published=True).all()
        
        content_stats = {
            'total_word_count': 0,
            'avg_word_count': 0,
            'posts_with_images': 0,
            'posts_with_headings': 0,
            'posts_with_tags': 0,
            'content_length_distribution': {
                'short': 0,    # < 500 слов
                'medium': 0,   # 500-1500 слов
                'long': 0      # > 1500 слов
            }
        }
        
        for post in posts:
            # Подсчет слов
            content_text = post.content.replace('<', ' <').replace('>', '> ')
            words = len(content_text.split())
            content_stats['total_word_count'] += words
            
            # Распределение по длине
            if words < 500:
                content_stats['content_length_distribution']['short'] += 1
            elif words < 1500:
                content_stats['content_length_distribution']['medium'] += 1
            else:
                content_stats['content_length_distribution']['long'] += 1
            
            # Проверка наличия элементов
            if '<img' in post.content.lower():
                content_stats['posts_with_images'] += 1
            
            if re.search(r'<h[1-6][^>]*>', post.content, re.IGNORECASE):
                content_stats['posts_with_headings'] += 1
            
            if post.tags:
                content_stats['posts_with_tags'] += 1
        
        content_stats['avg_word_count'] = round(content_stats['total_word_count'] / len(posts), 1) if posts else 0
        
        return content_stats
    
    def _get_performance_metrics(self) -> Dict:
        """Метрики производительности"""
        posts = Post.query.filter_by(is_published=True).all()
        
        performance = {
            'top_performing_posts': [],
            'low_performing_posts': [],
            'engagement_rate': 0,
            'bounce_rate': 0  # Имитация
        }
        
        # Топ посты по просмотрам
        sorted_posts = sorted(posts, key=lambda x: x.views_count, reverse=True)
        
        for post in sorted_posts[:5]:
            comments_count = Comment.query.filter_by(post_id=post.id).count()
            performance['top_performing_posts'].append({
                'id': post.id,
                'title': post.title,
                'views': post.views_count,
                'comments': comments_count,
                'engagement': post.views_count + comments_count * 2
            })
        
        # Худшие посты
        for post in sorted_posts[-3:]:
            comments_count = Comment.query.filter_by(post_id=post.id).count()
            performance['low_performing_posts'].append({
                'id': post.id,
                'title': post.title,
                'views': post.views_count,
                'comments': comments_count,
                'engagement': post.views_count + comments_count * 2
            })
        
        # Расчет engagement rate
        total_engagement = sum(p.views_count + Comment.query.filter_by(post_id=p.id).count() * 2 for p in posts)
        total_posts = len(posts)
        performance['engagement_rate'] = round(total_engagement / total_posts, 1) if total_posts > 0 else 0
        
        return performance
    
    def _get_keyword_analysis(self) -> Dict:
        """Анализ ключевых слов"""
        posts = Post.query.filter_by(is_published=True).all()
        
        all_keywords = []
        keyword_frequency = Counter()
        
        for post in posts:
            keywords = advanced_seo_optimizer.analyzer.extract_keywords(post.content, max_keywords=10)
            for keyword, count in keywords:
                all_keywords.append(keyword)
                keyword_frequency[keyword] += count
        
        # Топ ключевых слов
        top_keywords = keyword_frequency.most_common(20)
        
        # Анализ плотности ключевых слов
        keyword_density_analysis = {}
        for keyword, total_count in top_keywords[:10]:
            posts_with_keyword = sum(1 for post in posts if keyword.lower() in post.content.lower())
            density = (posts_with_keyword / len(posts) * 100) if posts else 0
            
            keyword_density_analysis[keyword] = {
                'total_count': total_count,
                'posts_count': posts_with_keyword,
                'density_percentage': round(density, 1)
            }
        
        return {
            'total_unique_keywords': len(set(all_keywords)),
            'top_keywords': top_keywords,
            'keyword_density_analysis': keyword_density_analysis,
            'keyword_trends': self._get_keyword_trends(posts)
        }
    
    def _get_keyword_trends(self, posts: List[Post]) -> Dict:
        """Тренды ключевых слов"""
        # Группировка постов по месяцам
        monthly_keywords = defaultdict(Counter)
        
        for post in posts:
            month_key = post.created_at.strftime('%Y-%m')
            keywords = advanced_seo_optimizer.analyzer.extract_keywords(post.content, max_keywords=5)
            
            for keyword, count in keywords:
                monthly_keywords[month_key][keyword] += count
        
        # Топ ключевые слова по месяцам
        trends = {}
        for month, keywords in monthly_keywords.items():
            trends[month] = keywords.most_common(5)
        
        return trends
    
    def _get_technical_seo_metrics(self) -> Dict:
        """Технические SEO метрики"""
        posts = Post.query.filter_by(is_published=True).all()
        
        technical_metrics = {
            'meta_tags_coverage': {
                'title_tags': 0,
                'description_tags': 0,
                'keyword_tags': 0
            },
            'content_structure': {
                'posts_with_h1': 0,
                'posts_with_h2': 0,
                'posts_with_images': 0,
                'posts_with_internal_links': 0
            },
            'url_structure': {
                'seo_friendly_urls': 0,
                'url_length_issues': 0
            }
        }
        
        for post in posts:
            # Мета-теги
            if post.title:
                technical_metrics['meta_tags_coverage']['title_tags'] += 1
            
            if post.excerpt:
                technical_metrics['meta_tags_coverage']['description_tags'] += 1
            
            # Структура контента
            if re.search(r'<h1[^>]*>', post.content, re.IGNORECASE):
                technical_metrics['content_structure']['posts_with_h1'] += 1
            
            if re.search(r'<h2[^>]*>', post.content, re.IGNORECASE):
                technical_metrics['content_structure']['posts_with_h2'] += 1
            
            if '<img' in post.content.lower():
                technical_metrics['content_structure']['posts_with_images'] += 1
            
            if re.search(r'href=["\'][^"\']*blog/post/', post.content, re.IGNORECASE):
                technical_metrics['content_structure']['posts_with_internal_links'] += 1
            
            # URL структура
            if len(post.slug) <= 60:
                technical_metrics['url_structure']['seo_friendly_urls'] += 1
            else:
                technical_metrics['url_structure']['url_length_issues'] += 1
        
        # Конвертация в проценты
        total_posts = len(posts)
        if total_posts > 0:
            for category in technical_metrics.values():
                for key in category:
                    category[key] = round(category[key] / total_posts * 100, 1)
        
        return technical_metrics
    
    def _get_competitor_analysis(self) -> Dict:
        """Анализ конкурентов (заглушка)"""
        return {
            'competitors_tracked': 0,
            'keyword_gaps': [],
            'content_gaps': [],
            'technical_gaps': [],
            'last_analysis': datetime.now().isoformat()
        }
    
    def _get_trend_analysis(self) -> Dict:
        """Анализ трендов"""
        posts = Post.query.filter_by(is_published=True).all()
        
        # Группировка по месяцам
        monthly_stats = defaultdict(lambda: {
            'posts_count': 0,
            'views_count': 0,
            'comments_count': 0
        })
        
        for post in posts:
            month_key = post.created_at.strftime('%Y-%m')
            comments_count = Comment.query.filter_by(post_id=post.id).count()
            monthly_stats[month_key]['posts_count'] += 1
            monthly_stats[month_key]['views_count'] += post.views_count
            monthly_stats[month_key]['comments_count'] += comments_count
        
        # Конвертация в список для графиков
        trends = {
            'monthly_posts': [],
            'monthly_views': [],
            'monthly_comments': []
        }
        
        for month in sorted(monthly_stats.keys()):
            stats = monthly_stats[month]
            trends['monthly_posts'].append({'month': month, 'count': stats['posts_count']})
            trends['monthly_views'].append({'month': month, 'count': stats['views_count']})
            trends['monthly_comments'].append({'month': month, 'count': stats['comments_count']})
        
        return trends
    
    def _get_recommendations(self) -> List[str]:
        """SEO рекомендации"""
        recommendations = []
        
        posts = Post.query.filter_by(is_published=True).all()
        
        # Анализ проблем
        posts_without_meta = sum(1 for p in posts if not p.excerpt)
        posts_without_headings = sum(1 for p in posts if not re.search(r'<h[1-6][^>]*>', p.content, re.IGNORECASE))
        posts_without_images = sum(1 for p in posts if '<img' not in p.content.lower())
        
        if posts_without_meta > len(posts) * 0.3:
            recommendations.append(f"Добавьте мета-описания к {posts_without_meta} постам")
        
        if posts_without_headings > len(posts) * 0.2:
            recommendations.append(f"Добавьте заголовки к {posts_without_headings} постам")
        
        if posts_without_images > len(posts) * 0.5:
            recommendations.append(f"Добавьте изображения к {posts_without_images} постам")
        
        # Общие рекомендации
        recommendations.extend([
            "Регулярно обновляйте контент для поддержания актуальности",
            "Используйте внутренние ссылки для улучшения навигации",
            "Оптимизируйте изображения для ускорения загрузки",
            "Создавайте качественный контент длиной от 1000 слов",
            "Используйте релевантные ключевые слова естественным образом"
        ])
        
        return recommendations
    
    def generate_seo_report(self, format: str = 'json') -> str:
        """Генерация SEO отчета"""
        analytics = self.get_comprehensive_analytics()
        
        if format == 'json':
            return json.dumps(analytics, indent=2, ensure_ascii=False)
        elif format == 'csv':
            return self._generate_csv_report(analytics)
        else:
            return str(analytics)
    
    def _generate_csv_report(self, analytics: Dict) -> str:
        """Генерация CSV отчета"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['Метрика', 'Значение', 'Описание'])
        
        # Общие метрики
        overview = analytics['overview']
        writer.writerow(['Всего постов', overview['total_posts'], 'Общее количество опубликованных постов'])
        writer.writerow(['Всего просмотров', overview['total_views'], 'Общее количество просмотров'])
        writer.writerow(['SEO здоровье', f"{overview['seo_health_percentage']}%", 'Процент постов с хорошим SEO'])
        
        # Контентные метрики
        content = analytics['content_analysis']
        writer.writerow(['Среднее количество слов', content['avg_word_count'], 'Средняя длина постов'])
        writer.writerow(['Посты с изображениями', f"{content['posts_with_images']}", 'Количество постов с изображениями'])
        
        return output.getvalue()
    
    def get_seo_score(self) -> int:
        """Общий SEO рейтинг сайта"""
        analytics = self.get_comprehensive_analytics()
        
        score = 0
        
        # Базовый рейтинг
        overview = analytics['overview']
        score += overview['seo_health_percentage'] * 0.4
        
        # Технические метрики
        technical = analytics['technical_seo']
        meta_coverage = (technical['meta_tags_coverage']['title_tags'] + 
                        technical['meta_tags_coverage']['description_tags']) / 2
        score += meta_coverage * 0.3
        
        # Контентные метрики
        content = analytics['content_analysis']
        structure_score = (content['posts_with_headings'] + content['posts_with_images']) / 2
        score += structure_score * 0.3
        
        return min(100, max(0, int(score)))

# Глобальный экземпляр SEO аналитики
seo_analytics = SEOAnalytics()