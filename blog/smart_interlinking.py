"""
Умная система перелинковки для блога
Автоматически создает релевантные внутренние ссылки между постами
"""

import re
import json
import math
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import difflib

from blog.models_perfect import Post, Category, Tag
from blog import db

class ContentAnalyzer:
    """Анализатор контента для определения релевантности"""
    
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
    
    def extract_terms(self, text: str) -> Set[str]:
        """Извлечение терминов из текста"""
        # Очистка от HTML тегов
        clean_text = re.sub(r'<[^>]+>', '', text.lower())
        
        # Извлечение слов
        words = re.findall(r'\b[а-яё]{3,}\b', clean_text)
        
        # Фильтрация стоп-слов
        terms = {word for word in words if word not in self.stop_words}
        
        return terms
    
    def calculate_tf_idf(self, posts: List[Post]) -> Dict[int, Dict[str, float]]:
        """Расчет TF-IDF для всех постов"""
        # Извлечение терминов для всех постов
        post_terms = {}
        all_terms = set()
        
        for post in posts:
            terms = self.extract_terms(post.title + ' ' + post.content)
            post_terms[post.id] = terms
            all_terms.update(terms)
        
        # Расчет IDF
        idf = {}
        total_posts = len(posts)
        
        for term in all_terms:
            posts_with_term = sum(1 for terms in post_terms.values() if term in terms)
            idf[term] = math.log(total_posts / (1 + posts_with_term))
        
        # Расчет TF-IDF для каждого поста
        tf_idf_scores = {}
        
        for post in posts:
            terms = post_terms[post.id]
            term_counts = Counter(self.extract_terms(post.title + ' ' + post.content))
            total_terms = sum(term_counts.values())
            
            tf_idf_scores[post.id] = {}
            
            for term in terms:
                tf = term_counts[term] / total_terms if total_terms > 0 else 0
                tf_idf_scores[post.id][term] = tf * idf[term]
        
        return tf_idf_scores
    
    def calculate_similarity(self, post1_tfidf: Dict[str, float], post2_tfidf: Dict[str, float]) -> float:
        """Расчет косинусного сходства между постами"""
        # Общие термины
        common_terms = set(post1_tfidf.keys()) & set(post2_tfidf.keys())
        
        if not common_terms:
            return 0.0
        
        # Скалярное произведение
        dot_product = sum(post1_tfidf[term] * post2_tfidf[term] for term in common_terms)
        
        # Нормы векторов
        norm1 = math.sqrt(sum(score ** 2 for score in post1_tfidf.values()))
        norm2 = math.sqrt(sum(score ** 2 for score in post2_tfidf.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

class LinkOpportunityFinder:
    """Поиск возможностей для создания ссылок"""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
        self.min_similarity = 0.1
        self.max_links_per_post = 5
    
    def find_link_opportunities(self, target_post: Post, candidate_posts: List[Post]) -> List[Dict]:
        """Поиск возможностей для ссылок в целевом посте"""
        opportunities = []
        
        # Расчет TF-IDF для всех постов
        all_posts = [target_post] + candidate_posts
        tf_idf_scores = self.analyzer.calculate_tf_idf(all_posts)
        
        target_tfidf = tf_idf_scores[target_post.id]
        
        # Поиск похожих постов
        similarities = []
        for candidate in candidate_posts:
            if candidate.id == target_post.id:
                continue
            
            candidate_tfidf = tf_idf_scores[candidate.id]
            similarity = self.analyzer.calculate_similarity(target_tfidf, candidate_tfidf)
            
            if similarity >= self.min_similarity:
                similarities.append((candidate, similarity))
        
        # Сортировка по релевантности
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Поиск конкретных мест для ссылок
        for candidate_post, similarity in similarities[:self.max_links_per_post]:
            link_positions = self._find_link_positions(target_post, candidate_post)
            
            for position in link_positions:
                opportunities.append({
                    'target_post_id': target_post.id,
                    'linked_post_id': candidate_post.id,
                    'linked_post_title': candidate_post.title,
                    'linked_post_url': f'/blog/post/{candidate_post.slug}',
                    'similarity_score': similarity,
                    'anchor_text': position['anchor_text'],
                    'context': position['context'],
                    'position': position['position'],
                    'confidence': position['confidence']
                })
        
        return opportunities
    
    def _find_link_positions(self, source_post: Post, target_post: Post) -> List[Dict]:
        """Поиск конкретных позиций для размещения ссылок"""
        positions = []
        
        # Извлечение ключевых терминов из целевого поста
        target_terms = self.analyzer.extract_terms(target_post.title + ' ' + target_post.content)
        
        # Поиск упоминаний в исходном посте
        source_content = source_post.content
        sentences = re.split(r'[.!?]+', source_content)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:  # Пропускаем слишком короткие предложения
                continue
            
            sentence_terms = self.analyzer.extract_terms(sentence)
            
            # Проверка пересечения терминов
            common_terms = sentence_terms & target_terms
            
            if len(common_terms) >= 2:  # Минимум 2 общих термина
                # Поиск подходящего анкорного текста
                anchor_candidates = self._find_anchor_candidates(sentence, target_post, common_terms)
                
                for anchor_text, confidence in anchor_candidates:
                    positions.append({
                        'anchor_text': anchor_text,
                        'context': sentence,
                        'position': i,
                        'confidence': confidence,
                        'common_terms': list(common_terms)
                    })
        
        # Сортировка по уверенности
        positions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return positions[:3]  # Максимум 3 ссылки на один пост
    
    def _find_anchor_candidates(self, sentence: str, target_post: Post, common_terms: Set[str]) -> List[Tuple[str, float]]:
        """Поиск кандидатов для анкорного текста"""
        candidates = []
        
        # Кандидат 1: Заголовок целевого поста (если упоминается)
        title_similarity = difflib.SequenceMatcher(None, sentence.lower(), target_post.title.lower()).ratio()
        if title_similarity > 0.3:
            candidates.append((target_post.title, title_similarity))
        
        # Кандидат 2: Ключевые фразы из общих терминов
        for term in common_terms:
            if term in sentence.lower():
                # Поиск контекста вокруг термина
                pattern = rf'\b\w*{re.escape(term)}\w*(?:\s+\w+){{0,2}}'
                matches = re.finditer(pattern, sentence.lower())
                
                for match in matches:
                    phrase = match.group().strip()
                    if len(phrase.split()) <= 4:  # Не более 4 слов
                        confidence = 0.6 + (len(phrase.split()) * 0.1)
                        candidates.append((phrase.title(), confidence))
        
        # Кандидат 3: Категория целевого поста
        if target_post.category:
            category_name = target_post.category.name.lower()
            if category_name in sentence.lower():
                candidates.append((target_post.category.name, 0.5))
        
        # Удаление дубликатов и сортировка
        unique_candidates = {}
        for text, confidence in candidates:
            if text not in unique_candidates or unique_candidates[text] < confidence:
                unique_candidates[text] = confidence
        
        return [(text, conf) for text, conf in unique_candidates.items()]

class LinkInserter:
    """Вставка ссылок в контент"""
    
    def __init__(self):
        self.max_links_per_paragraph = 2
        self.min_distance_between_links = 100  # символов
    
    def insert_links(self, post: Post, opportunities: List[Dict]) -> str:
        """Вставка ссылок в контент поста"""
        content = post.content
        inserted_links = []
        
        # Сортировка возможностей по уверенности
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        for opportunity in opportunities:
            if len(inserted_links) >= 5:  # Максимум 5 ссылок на пост
                break
            
            # Проверка, что ссылка еще не вставлена
            if self._is_link_already_exists(content, opportunity['linked_post_url']):
                continue
            
            # Поиск места для вставки
            anchor_text = opportunity['anchor_text']
            context = opportunity['context']
            
            # Проверка расстояния от других ссылок
            if not self._check_link_distance(content, context, inserted_links):
                continue
            
            # Вставка ссылки
            link_html = f'<a href="{opportunity["linked_post_url"]}" title="{opportunity["linked_post_title"]}">{anchor_text}</a>'
            
            # Замена первого вхождения анкорного текста в контексте
            pattern = re.escape(anchor_text)
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, link_html, content, count=1, flags=re.IGNORECASE)
                inserted_links.append({
                    'url': opportunity['linked_post_url'],
                    'anchor': anchor_text,
                    'position': content.find(link_html)
                })
        
        return content
    
    def _is_link_already_exists(self, content: str, url: str) -> bool:
        """Проверка, существует ли уже ссылка на данный URL"""
        return url in content
    
    def _check_link_distance(self, content: str, context: str, existing_links: List[Dict]) -> bool:
        """Проверка расстояния между ссылками"""
        context_position = content.find(context)
        if context_position == -1:
            return False
        
        for link in existing_links:
            distance = abs(context_position - link['position'])
            if distance < self.min_distance_between_links:
                return False
        
        return True

class RelatedPostsGenerator:
    """Генератор похожих постов"""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
    
    def get_related_posts(self, post: Post, limit: int = 5) -> List[Dict]:
        """Получение похожих постов"""
        # Получение всех опубликованных постов кроме текущего
        candidate_posts = Post.query.filter(
            Post.is_published == True,
            Post.id != post.id
        ).all()
        
        if not candidate_posts:
            return []
        
        # Расчет TF-IDF
        all_posts = [post] + candidate_posts
        tf_idf_scores = self.analyzer.calculate_tf_idf(all_posts)
        
        target_tfidf = tf_idf_scores[post.id]
        
        # Расчет сходства
        similarities = []
        for candidate in candidate_posts:
            candidate_tfidf = tf_idf_scores[candidate.id]
            similarity = self.analyzer.calculate_similarity(target_tfidf, candidate_tfidf)
            
            # Дополнительные факторы релевантности
            category_bonus = 0.2 if post.category_id == candidate.category_id else 0
            tag_bonus = len(set(tag.id for tag in post.tags) & set(tag.id for tag in candidate.tags)) * 0.1
            recency_bonus = self._calculate_recency_bonus(candidate)
            
            total_score = similarity + category_bonus + tag_bonus + recency_bonus
            
            similarities.append({
                'post': candidate,
                'similarity': similarity,
                'total_score': total_score,
                'category_match': post.category_id == candidate.category_id,
                'common_tags': len(set(tag.id for tag in post.tags) & set(tag.id for tag in candidate.tags))
            })
        
        # Сортировка по общему рейтингу
        similarities.sort(key=lambda x: x['total_score'], reverse=True)
        
        return similarities[:limit]
    
    def _calculate_recency_bonus(self, post: Post) -> float:
        """Расчет бонуса за свежесть поста"""
        if not post.created_at:
            return 0
        
        days_old = (datetime.now() - post.created_at).days
        
        if days_old <= 7:
            return 0.1
        elif days_old <= 30:
            return 0.05
        else:
            return 0

class SmartInterlinkingSystem:
    """Основная система умной перелинковки"""
    
    def __init__(self):
        self.opportunity_finder = LinkOpportunityFinder()
        self.link_inserter = LinkInserter()
        self.related_posts_generator = RelatedPostsGenerator()
        self.link_cache = {}
    
    def analyze_post_for_links(self, post: Post) -> Dict:
        """Анализ поста для поиска возможностей перелинковки"""
        # Получение кандидатов для ссылок
        candidate_posts = Post.query.filter(
            Post.is_published == True,
            Post.id != post.id
        ).all()
        
        # Поиск возможностей для исходящих ссылок
        outbound_opportunities = self.opportunity_finder.find_link_opportunities(post, candidate_posts)
        
        # Поиск возможностей для входящих ссылок
        inbound_opportunities = []
        for candidate in candidate_posts:
            opportunities = self.opportunity_finder.find_link_opportunities(candidate, [post])
            inbound_opportunities.extend(opportunities)
        
        # Получение похожих постов
        related_posts = self.related_posts_generator.get_related_posts(post)
        
        return {
            'post_id': post.id,
            'post_title': post.title,
            'outbound_opportunities': outbound_opportunities,
            'inbound_opportunities': inbound_opportunities,
            'related_posts': related_posts,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def auto_insert_links(self, post: Post, max_links: int = 3) -> str:
        """Автоматическая вставка ссылок в пост"""
        analysis = self.analyze_post_for_links(post)
        opportunities = analysis['outbound_opportunities'][:max_links]
        
        return self.link_inserter.insert_links(post, opportunities)
    
    def get_link_suggestions(self, post: Post) -> List[Dict]:
        """Получение предложений по ссылкам для ручной модерации"""
        analysis = self.analyze_post_for_links(post)
        
        suggestions = []
        for opportunity in analysis['outbound_opportunities']:
            suggestions.append({
                'type': 'outbound',
                'linked_post_title': opportunity['linked_post_title'],
                'linked_post_url': opportunity['linked_post_url'],
                'anchor_text': opportunity['anchor_text'],
                'context': opportunity['context'],
                'confidence': opportunity['confidence'],
                'similarity_score': opportunity['similarity_score']
            })
        
        return suggestions
    
    def update_all_interlinks(self):
        """Обновление всех внутренних ссылок"""
        posts = Post.query.filter_by(is_published=True).all()
        updated_count = 0
        
        for post in posts:
            try:
                # Проверка, нужно ли обновлять ссылки
                if self._should_update_links(post):
                    new_content = self.auto_insert_links(post)
                    
                    if new_content != post.content:
                        post.content = new_content
                        db.session.add(post)
                        updated_count += 1
                
            except Exception as e:
                print(f"Ошибка обновления ссылок для поста {post.id}: {e}")
        
        db.session.commit()
        return updated_count
    
    def _should_update_links(self, post: Post) -> bool:
        """Проверка, нужно ли обновлять ссылки в посте"""
        # Проверяем кеш
        cache_key = f"links_updated_{post.id}"
        last_update = self.link_cache.get(cache_key)
        
        if last_update:
            # Обновляем не чаще раза в неделю
            if (datetime.now() - last_update).days < 7:
                return False
        
        # Проверяем количество существующих внутренних ссылок
        internal_links = re.findall(r'<a[^>]*href=["\'][^"\']*blog/post/[^"\']*["\'][^>]*>', post.content)
        
        # Если ссылок мало, стоит добавить
        if len(internal_links) < 3:
            self.link_cache[cache_key] = datetime.now()
            return True
        
        return False
    
    def generate_link_report(self) -> Dict:
        """Генерация отчета по перелинковке"""
        posts = Post.query.filter_by(is_published=True).all()
        
        total_posts = len(posts)
        posts_with_links = 0
        total_internal_links = 0
        link_distribution = defaultdict(int)
        
        for post in posts:
            internal_links = re.findall(r'<a[^>]*href=["\'][^"\']*blog/post/[^"\']*["\'][^>]*>', post.content)
            link_count = len(internal_links)
            
            if link_count > 0:
                posts_with_links += 1
            
            total_internal_links += link_count
            link_distribution[link_count] += 1
        
        avg_links_per_post = total_internal_links / total_posts if total_posts > 0 else 0
        
        return {
            'total_posts': total_posts,
            'posts_with_internal_links': posts_with_links,
            'posts_without_links': total_posts - posts_with_links,
            'total_internal_links': total_internal_links,
            'average_links_per_post': round(avg_links_per_post, 2),
            'link_distribution': dict(link_distribution),
            'coverage_percentage': round((posts_with_links / total_posts) * 100, 1) if total_posts > 0 else 0
        }

# Глобальный экземпляр системы перелинковки
smart_interlinking = SmartInterlinkingSystem()