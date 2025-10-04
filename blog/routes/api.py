"""
API для поиска с автодополнением
"""

from flask import Blueprint, request, jsonify
from blog.models_perfect import Post, Category, User
from blog import db
from sqlalchemy import or_

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/search/suggestions')
def search_suggestions():
    """API для получения предложений поиска"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = []
    
    try:
        # Поиск по постам
        posts = Post.query.filter(
            or_(
                Post.title.ilike(f'%{query}%'),
                Post.content.ilike(f'%{query}%'),
                Post.excerpt.ilike(f'%{query}%')
            ),
            Post.is_published == True
        ).limit(5).all()
        
        for post in posts:
            suggestions.append({
                'title': post.title,
                'description': post.excerpt[:100] + '...' if post.excerpt and len(post.excerpt) > 100 else post.excerpt,
                'url': f'/blog/{post.slug}',
                'icon': 'fa-newspaper',
                'type': 'post'
            })
        
        # Поиск по категориям
        categories = Category.query.filter(
            Category.name.ilike(f'%{query}%')
        ).limit(3).all()
        
        for category in categories:
            suggestions.append({
                'title': category.name,
                'description': f'Категория ({category.get_posts_count()} постов)',
                'url': f'/blog/category/{category.slug}',
                'icon': 'fa-folder',
                'type': 'category'
            })
        
        # Поиск по авторам
        authors = User.query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(3).all()
        
        for author in authors:
            suggestions.append({
                'title': author.get_full_name(),
                'description': f'Автор ({author.posts.count()} постов)',
                'url': f'/blog/author/{author.username}',
                'icon': 'fa-user',
                'type': 'author'
            })
        
        # Популярные теги (если есть)
        popular_tags = [
            'Python', 'Flask', 'Web Development', 'Programming', 'Tutorial',
            'AI', 'Machine Learning', 'Data Science', 'JavaScript', 'CSS'
        ]
        
        matching_tags = [tag for tag in popular_tags if query.lower() in tag.lower()]
        for tag in matching_tags[:2]:
            suggestions.append({
                'title': tag,
                'description': 'Популярный тег',
                'url': f'/blog/tag/{tag.lower().replace(" ", "-")}',
                'icon': 'fa-tag',
                'type': 'tag'
            })
        
        # Ограничиваем количество предложений
        suggestions = suggestions[:8]
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/search/posts')
def search_posts():
    """API для поиска постов"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if not query:
        return jsonify({'posts': [], 'total': 0, 'page': page, 'pages': 0})
    
    try:
        posts_query = Post.query.filter(
            or_(
                Post.title.ilike(f'%{query}%'),
                Post.content.ilike(f'%{query}%'),
                Post.excerpt.ilike(f'%{query}%')
            ),
            Post.is_published == True
        ).order_by(Post.created_at.desc())
        
        pagination = posts_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        posts_data = []
        for post in pagination.items:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt,
                'author': post.author.get_full_name(),
                'category': post.category.name if post.category else None,
                'created_at': post.created_at.isoformat(),
                'views_count': post.views_count,
                'comments_count': post.get_comments_count(),
                'url': f'/blog/{post.slug}'
            })
        
        return jsonify({
            'posts': posts_data,
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/navigation/menu')
def navigation_menu():
    """API для получения меню навигации"""
    try:
        # Категории
        categories = Category.query.all()
        categories_data = []
        for category in categories:
            categories_data.append({
                'name': category.name,
                'slug': category.slug,
                'color': category.color,
                'posts_count': category.get_posts_count(),
                'url': f'/blog/category/{category.slug}'
            })
        
        # Статистика
        stats = {
            'total_posts': Post.query.filter_by(is_published=True).count(),
            'total_categories': Category.query.count(),
            'total_users': User.query.count()
        }
        
        return jsonify({
            'categories': categories_data,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/navigation/popular')
def navigation_popular():
    """API для получения популярного контента"""
    try:
        # Популярные посты
        popular_posts = Post.query.filter_by(is_published=True)\
            .order_by(Post.views_count.desc())\
            .limit(5).all()
        
        posts_data = []
        for post in popular_posts:
            posts_data.append({
                'title': post.title,
                'slug': post.slug,
                'views_count': post.views_count,
                'url': f'/blog/{post.slug}'
            })
        
        # Популярные категории
        popular_categories = Category.query.join(Post)\
            .group_by(Category.id)\
            .order_by(db.func.count(Post.id).desc())\
            .limit(5).all()
        
        categories_data = []
        for category in popular_categories:
            categories_data.append({
                'name': category.name,
                'slug': category.slug,
                'color': category.color,
                'posts_count': category.get_posts_count(),
                'url': f'/blog/category/{category.slug}'
            })
        
        return jsonify({
            'popular_posts': posts_data,
            'popular_categories': categories_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500