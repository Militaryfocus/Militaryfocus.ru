"""
Маршруты для статистики авторов
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from blog.models import Post, Comment, Like, View, User
from blog.database import db

bp = Blueprint('author_stats', __name__, url_prefix='/author')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Дашборд автора со статистикой"""
    # Получаем статистику текущего пользователя
    stats = get_author_stats(current_user.id)
    
    # Получаем последние посты
    recent_posts = Post.query.filter_by(
        author_id=current_user.id
    ).order_by(Post.created_at.desc()).limit(5).all()
    
    # Получаем популярные посты
    popular_posts = Post.query.filter_by(
        author_id=current_user.id
    ).order_by(Post.views.desc()).limit(5).all()
    
    return render_template('author/dashboard.html',
                         stats=stats,
                         recent_posts=recent_posts,
                         popular_posts=popular_posts)

@bp.route('/stats/<int:user_id>')
def author_stats(user_id):
    """Публичная статистика автора"""
    author = User.query.get_or_404(user_id)
    
    # Проверяем настройки приватности
    if not author.is_active:
        return render_template('error/404.html'), 404
    
    stats = get_author_stats(user_id, public=True)
    
    # Последние посты автора
    recent_posts = Post.query.filter_by(
        author_id=user_id,
        is_published=True
    ).order_by(Post.created_at.desc()).limit(10).all()
    
    return render_template('author/public_stats.html',
                         author=author,
                         stats=stats,
                         recent_posts=recent_posts)

@bp.route('/api/stats')
@login_required
def api_stats():
    """API для получения статистики в JSON"""
    period = request.args.get('period', '30')  # дней
    
    try:
        days = int(period)
    except:
        days = 30
    
    stats = get_detailed_stats(current_user.id, days)
    return jsonify(stats)

def get_author_stats(user_id, public=False):
    """Получает базовую статистику автора"""
    stats = {}
    
    # Общее количество постов
    stats['total_posts'] = Post.query.filter_by(
        author_id=user_id,
        is_published=True
    ).count()
    
    # Общее количество просмотров
    stats['total_views'] = db.session.query(
        func.sum(Post.views)
    ).filter(
        Post.author_id == user_id,
        Post.is_published == True
    ).scalar() or 0
    
    # Общее количество комментариев к постам
    stats['total_comments'] = db.session.query(
        func.count(Comment.id)
    ).join(Post).filter(
        Post.author_id == user_id,
        Comment.is_approved == True
    ).scalar() or 0
    
    # Общее количество лайков
    stats['total_likes'] = db.session.query(
        func.count(Like.id)
    ).join(
        Post, (Like.item_id == Post.id) & (Like.item_type == 'post')
    ).filter(
        Post.author_id == user_id
    ).scalar() or 0
    
    if not public:
        # Приватная статистика (только для владельца)
        stats['draft_posts'] = Post.query.filter_by(
            author_id=user_id,
            is_published=False
        ).count()
        
        # Средние показатели
        if stats['total_posts'] > 0:
            stats['avg_views'] = stats['total_views'] // stats['total_posts']
            stats['avg_comments'] = stats['total_comments'] / stats['total_posts']
            stats['avg_likes'] = stats['total_likes'] / stats['total_posts']
        else:
            stats['avg_views'] = 0
            stats['avg_comments'] = 0
            stats['avg_likes'] = 0
    
    return stats

def get_detailed_stats(user_id, days=30):
    """Получает детальную статистику за период"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = {
        'period': days,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }
    
    # Просмотры по дням
    views_by_day = db.session.query(
        func.date(View.created_at).label('date'),
        func.count(View.id).label('count')
    ).join(
        Post, View.post_id == Post.id
    ).filter(
        Post.author_id == user_id,
        View.created_at >= start_date
    ).group_by(
        func.date(View.created_at)
    ).all()
    
    stats['views_by_day'] = [
        {
            'date': str(day.date),
            'count': day.count
        }
        for day in views_by_day
    ]
    
    # Лайки по дням
    likes_by_day = db.session.query(
        func.date(Like.created_at).label('date'),
        func.count(Like.id).label('count')
    ).join(
        Post, (Like.item_id == Post.id) & (Like.item_type == 'post')
    ).filter(
        Post.author_id == user_id,
        Like.created_at >= start_date
    ).group_by(
        func.date(Like.created_at)
    ).all()
    
    stats['likes_by_day'] = [
        {
            'date': str(day.date),
            'count': day.count
        }
        for day in likes_by_day
    ]
    
    # Топ посты за период
    top_posts = db.session.query(
        Post,
        func.count(View.id).label('view_count')
    ).join(
        View, View.post_id == Post.id
    ).filter(
        Post.author_id == user_id,
        View.created_at >= start_date
    ).group_by(
        Post.id
    ).order_by(
        func.count(View.id).desc()
    ).limit(10).all()
    
    stats['top_posts'] = [
        {
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'views': count
        }
        for post, count in top_posts
    ]
    
    # Статистика по категориям
    category_stats = db.session.query(
        Post.category_id,
        func.count(Post.id).label('post_count'),
        func.sum(Post.views).label('total_views')
    ).filter(
        Post.author_id == user_id,
        Post.is_published == True,
        Post.created_at >= start_date
    ).group_by(
        Post.category_id
    ).all()
    
    stats['categories'] = []
    for cat_id, post_count, total_views in category_stats:
        if cat_id:
            from blog.models import Category
            category = Category.query.get(cat_id)
            if category:
                stats['categories'].append({
                    'name': category.name,
                    'posts': post_count,
                    'views': total_views or 0
                })
    
    return stats