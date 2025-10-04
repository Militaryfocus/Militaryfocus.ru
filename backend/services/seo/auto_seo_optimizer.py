"""
Автоматическая SEO оптимизация
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import Post, Category, Tag
from config.database import db
from services.advanced_seo import advanced_seo_optimizer

class AutoSEOOptimizer:
    """Автоматическая SEO оптимизация"""
    
    def __init__(self):
        self.optimization_rules = {
            'title_length': {'min': 30, 'max': 60},
            'description_length': {'min': 120, 'max': 160},
            'content_length': {'min': 300},
            'heading_structure': True,
            'keyword_density': {'min': 1, 'max': 3},
            'image_alt_tags': True,
            'internal_linking': True
        }
    
    def optimize_post_automatically(self, post: Post) -> Dict:
        """Автоматическая оптимизация поста"""
        improvements = []
        changes_made = False
        
        # Оптимизация заголовка
        if self._needs_title_optimization(post):
            old_title = post.title
            post.title = self._optimize_title(post)
            if post.title != old_title:
                improvements.append(f"Оптимизирован заголовок: '{old_title}' → '{post.title}'")
                changes_made = True
        
        # Оптимизация описания
        if self._needs_description_optimization(post):
            old_excerpt = post.excerpt
            post.excerpt = self._optimize_description(post)
            if post.excerpt != old_excerpt:
                improvements.append(f"Оптимизировано описание: '{old_excerpt}' → '{post.excerpt}'")
                changes_made = True
        
        # Оптимизация контента
        if self._needs_content_optimization(post):
            old_content = post.content
            post.content = self._optimize_content(post)
            if post.content != old_content:
                improvements.append("Оптимизирован контент (добавлены заголовки, улучшена структура)")
                changes_made = True
        
        # Добавление тегов
        if not post.tags or len(post.tags) < 3:
            suggested_tags = self._suggest_tags(post)
            if suggested_tags:
                for tag_name in suggested_tags[:3]:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    if tag not in post.tags:
                        post.tags.append(tag)
                improvements.append(f"Добавлены теги: {', '.join(suggested_tags[:3])}")
                changes_made = True
        
        if changes_made:
            post.updated_at = datetime.utcnow()
            db.session.commit()
        
        return {
            'success': changes_made,
            'improvements': improvements,
            'optimization_date': datetime.now().isoformat()
        }
    
    def _needs_title_optimization(self, post: Post) -> bool:
        """Проверка необходимости оптимизации заголовка"""
        title_len = len(post.title)
        return (title_len < self.optimization_rules['title_length']['min'] or 
                title_len > self.optimization_rules['title_length']['max'])
    
    def _optimize_title(self, post: Post) -> str:
        """Оптимизация заголовка"""
        title = post.title.strip()
        
        # Если заголовок слишком короткий
        if len(title) < self.optimization_rules['title_length']['min']:
            # Добавляем ключевые слова из контента
            keywords = advanced_seo_optimizer.analyzer.extract_keywords(post.content, max_keywords=3)
            if keywords:
                keyword_text = ' | '.join([kw[0] for kw in keywords[:2]])
                title = f"{title} - {keyword_text}"
        
        # Если заголовок слишком длинный
        elif len(title) > self.optimization_rules['title_length']['max']:
            # Обрезаем до оптимальной длины
            title = title[:self.optimization_rules['title_length']['max']-3] + '...'
        
        return title
    
    def _needs_description_optimization(self, post: Post) -> bool:
        """Проверка необходимости оптимизации описания"""
        if not post.excerpt:
            return True
        
        desc_len = len(post.excerpt)
        return (desc_len < self.optimization_rules['description_length']['min'] or 
                desc_len > self.optimization_rules['description_length']['max'])
    
    def _optimize_description(self, post: Post) -> str:
        """Оптимизация описания"""
        if post.excerpt and len(post.excerpt) >= self.optimization_rules['description_length']['min']:
            return post.excerpt[:self.optimization_rules['description_length']['max']]
        
        # Создаем описание из контента
        content_text = re.sub(r'<[^>]+>', '', post.content)
        sentences = re.split(r'[.!?]+', content_text)
        
        description = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(description + sentence) <= self.optimization_rules['description_length']['max']:
                description += sentence + ". "
            else:
                break
        
        description = description.strip()
        
        # Если описание слишком короткое, добавляем ключевые слова
        if len(description) < self.optimization_rules['description_length']['min']:
            keywords = advanced_seo_optimizer.analyzer.extract_keywords(post.content, max_keywords=5)
            keyword_text = ', '.join([kw[0] for kw in keywords[:3]])
            description = f"{description} {keyword_text}."
        
        return description[:self.optimization_rules['description_length']['max']]
    
    def _needs_content_optimization(self, post: Post) -> bool:
        """Проверка необходимости оптимизации контента"""
        # Проверяем наличие заголовков
        has_headings = bool(re.search(r'<h[1-6][^>]*>', post.content, re.IGNORECASE))
        
        # Проверяем длину контента
        content_text = re.sub(r'<[^>]+>', '', post.content)
        content_length = len(content_text)
        
        return not has_headings or content_length < self.optimization_rules['content_length']['min']
    
    def _optimize_content(self, post: Post) -> str:
        """Оптимизация контента"""
        content = post.content
        
        # Если нет заголовков, добавляем их
        if not re.search(r'<h[1-6][^>]*>', content, re.IGNORECASE):
            content = self._add_headings_to_content(content)
        
        # Добавляем alt теги к изображениям
        content = self._add_alt_tags_to_images(content)
        
        return content
    
    def _add_headings_to_content(self, content: str) -> str:
        """Добавление заголовков к контенту"""
        paragraphs = content.split('\n')
        optimized_content = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                optimized_content.append(paragraph)
                continue
            
            # Если абзац длинный и не содержит HTML тегов, делаем его заголовком
            if (len(paragraph) > 50 and 
                not re.search(r'<[^>]+>', paragraph) and 
                i < 3):  # Только первые 3 абзаца
                
                # Определяем уровень заголовка
                heading_level = 2 if i == 0 else 3
                optimized_content.append(f"<h{heading_level}>{paragraph}</h{heading_level}>")
            else:
                optimized_content.append(paragraph)
        
        return '\n'.join(optimized_content)
    
    def _add_alt_tags_to_images(self, content: str) -> str:
        """Добавление alt тегов к изображениям"""
        def replace_img(match):
            img_tag = match.group(0)
            
            # Если уже есть alt тег, возвращаем как есть
            if 'alt=' in img_tag:
                return img_tag
            
            # Извлекаем src
            src_match = re.search(r'src=["\']([^"\']*)["\']', img_tag)
            if src_match:
                src = src_match.group(1)
                filename = src.split('/')[-1].split('.')[0]
                alt_text = filename.replace('-', ' ').replace('_', ' ').title()
                
                # Добавляем alt тег
                return img_tag.replace('>', f' alt="{alt_text}">')
            
            return img_tag
        
        return re.sub(r'<img[^>]*>', replace_img, content)
    
    def _suggest_tags(self, post: Post) -> List[str]:
        """Предложение тегов на основе контента"""
        keywords = advanced_seo_optimizer.analyzer.extract_keywords(post.content, max_keywords=10)
        
        # Фильтруем ключевые слова для тегов
        suggested_tags = []
        for keyword, count in keywords:
            if len(keyword) >= 3 and len(keyword) <= 20:
                suggested_tags.append(keyword)
        
        return suggested_tags[:5]
    
    def optimize_all_posts(self) -> Dict:
        """Оптимизация всех постов"""
        posts = Post.query.filter_by(is_published=True).all()
        
        results = {
            'total_posts': len(posts),
            'optimized_posts': 0,
            'total_improvements': 0,
            'posts_results': []
        }
        
        for post in posts:
            optimization_result = self.optimize_post_automatically(post)
            
            if optimization_result['success']:
                results['optimized_posts'] += 1
                results['total_improvements'] += len(optimization_result['improvements'])
            
            results['posts_results'].append({
                'post_id': post.id,
                'post_title': post.title,
                'success': optimization_result['success'],
                'improvements': optimization_result['improvements']
            })
        
        return results
    
    def schedule_optimization(self, post_id: int, delay_hours: int = 24):
        """Планирование оптимизации поста"""
        # В реальном приложении здесь была бы интеграция с Celery или другой системой очередей
        post = Post.query.get(post_id)
        if post:
            # Простая имитация планирования
            optimization_time = datetime.utcnow() + timedelta(hours=delay_hours)
            print(f"Оптимизация поста '{post.title}' запланирована на {optimization_time}")
            return optimization_time
        return None

# Глобальный экземпляр автоматического оптимизатора
auto_seo_optimizer = AutoSEOOptimizer()