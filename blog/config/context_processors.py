"""
Контекстные процессоры для Flask приложения
Выделены из app_config.py для улучшения архитектуры
"""
from flask import request
import logging

logger = logging.getLogger(__name__)

def inject_categories():
    """
    Инжектим категории во все шаблоны
    
    Returns:
        dict: Словарь с категориями для шаблонов
    """
    try:
        from blog.models import Category
        categories = Category.query.all()
        return dict(categories=categories)
    except Exception as e:
        logger.error(f"Error injecting categories: {e}")
        return dict(categories=[])

def inject_seo_meta():
    """
    Автоматическое добавление SEO мета-тегов
    
    Returns:
        dict: Словарь с SEO мета-тегами
    """
    from blog.advanced_seo import advanced_seo_optimizer
    from blog.models import Post, Category
    
    # Базовые мета-теги по умолчанию
    default_meta = {
        'title': 'МойБлог - Современный блог с ИИ контентом',
        'description': 'Современный блог на Python Flask с автоматическим наполнением контентом',
        'keywords': 'блог, python, flask, искусственный интеллект',
        'author': 'МойБлог',
        'robots': 'index, follow',
        'og_type': 'website',
        'og_site_name': 'МойБлог',
        'twitter_card': 'summary_large_image'
    }
    
    meta_tags = default_meta.copy()
    
    try:
        # Определение типа страницы и генерация соответствующих мета-тегов
        if request.endpoint == 'blog.post_detail':
            # Для страниц постов
            slug = request.view_args.get('slug')
            if slug:
                post = Post.query.filter_by(slug=slug, is_published=True).first()
                if post:
                    post_meta = advanced_seo_optimizer.meta_generator.generate_post_meta(post)
                    meta_tags.update(post_meta)
                    meta_tags['og_type'] = 'article'
                    
        elif request.endpoint == 'blog.category_posts':
            # Для страниц категорий
            slug = request.view_args.get('slug')
            if slug:
                category = Category.query.filter_by(slug=slug).first()
                if category:
                    category_meta = advanced_seo_optimizer.meta_generator.generate_category_meta(category)
                    meta_tags.update(category_meta)
                    
        elif request.endpoint == 'main.index':
            # Для главной страницы
            home_meta = advanced_seo_optimizer.meta_generator.generate_home_meta()
            meta_tags.update(home_meta)
            
        elif request.endpoint == 'auth.profile':
            # Для страниц профиля
            meta_tags['title'] = 'Профиль пользователя - МойБлог'
            meta_tags['robots'] = 'noindex, nofollow'
            
        elif request.endpoint == 'blog.search':
            # Для страницы поиска
            query = request.args.get('q', '')
            if query:
                meta_tags['title'] = f'Поиск: {query} - МойБлог'
                meta_tags['description'] = f'Результаты поиска по запросу "{query}" на МойБлог'
            else:
                meta_tags['title'] = 'Поиск - МойБлог'
            meta_tags['robots'] = 'noindex, follow'
            
    except Exception as e:
        # В случае ошибки логируем и возвращаем базовые мета-теги
        logger.error(f"Error generating SEO meta tags: {e}")
    
    return dict(seo_meta=meta_tags)

def inject_user_data():
    """
    Инжектим данные текущего пользователя
    
    Returns:
        dict: Словарь с данными пользователя
    """
    from flask_login import current_user
    
    user_data = {
        'is_authenticated': current_user.is_authenticated,
        'is_admin': False,
        'username': None,
        'user_id': None
    }
    
    if current_user.is_authenticated:
        user_data.update({
            'is_admin': getattr(current_user, 'is_admin', False),
            'username': current_user.username,
            'user_id': current_user.id
        })
    
    return dict(user_data=user_data)

def inject_site_config():
    """
    Инжектим конфигурацию сайта
    
    Returns:
        dict: Словарь с конфигурацией сайта
    """
    import os
    
    site_config = {
        'site_name': os.environ.get('SITE_NAME', 'МойБлог'),
        'site_url': os.environ.get('SITE_URL', 'http://localhost:5000'),
        'site_description': os.environ.get('SITE_DESCRIPTION', 'Современный блог с ИИ контентом'),
        'contact_email': os.environ.get('CONTACT_EMAIL', 'admin@blog.com'),
        'social_links': {
            'twitter': os.environ.get('TWITTER_URL', ''),
            'facebook': os.environ.get('FACEBOOK_URL', ''),
            'instagram': os.environ.get('INSTAGRAM_URL', ''),
            'github': os.environ.get('GITHUB_URL', '')
        },
        'google_analytics_id': os.environ.get('GOOGLE_ANALYTICS_ID', ''),
        'yandex_metrika_id': os.environ.get('YANDEX_METRIKA_ID', '')
    }
    
    return dict(site_config=site_config)

def inject_flash_categories():
    """
    Инжектим категории для flash сообщений
    
    Returns:
        dict: Словарь с категориями flash сообщений
    """
    flash_categories = {
        'success': 'alert-success',
        'info': 'alert-info',
        'warning': 'alert-warning',
        'danger': 'alert-danger',
        'error': 'alert-danger'
    }
    
    return dict(flash_categories=flash_categories)

# Список всех контекстных процессоров для удобного импорта
ALL_CONTEXT_PROCESSORS = [
    inject_categories,
    inject_seo_meta,
    inject_user_data,
    inject_site_config,
    inject_flash_categories
]