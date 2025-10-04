"""
Маршруты для статистики авторов
"""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from blog.models import Post, User, Comment, View, Like, Bookmark
from blog.database import db

bp = Blueprint('author_stats', __name__, url_prefix='/author')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Панель статистики для автора"""
    # Получаем статистику постов
    posts_count = Post.query.filter_by(user_id=current_user.id).count()
    published_posts = Post.query.filter_by(user_id=current_user.id, is_published=True).count()
    draft_posts = Post.query.filter_by(user_id=current_user.id, is_published=False).count()
    
    # Общее количество просмотров
    total_views = db.session.query(func.sum(Post.views)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Количество комментариев к постам автора
    comments_count = db.session.query(func.count(Comment.id)).join(Post).filter(
        Post.user_id == current_user.id
    ).scalar() or 0
    
    # Количество лайков к постам автора
    likes_count = db.session.query(func.count(Like.id)).filter(
        Like.item_type == 'post'
    ).join(Post, Post.id == Like.item_id).filter(
        Post.user_id == current_user.id
    ).scalar() or 0
    
    # Количество закладок постов автора
    bookmarks_count = db.session.query(func.count(Bookmark.id)).join(Post).filter(
        Post.user_id == current_user.id
    ).scalar() or 0
    
    # Популярные посты
    popular_posts = Post.query.filter_by(
        user_id=current_user.id,
        is_published=True
    ).order_by(Post.views.desc()).limit(5).all()
    
    # Последние комментарии
    recent_comments = Comment.query.join(Post).filter(
        Post.user_id == current_user.id,
        Comment.is_approved == True
    ).order_by(Comment.created_at.desc()).limit(5).all()
    
    # График просмотров за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_views = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        views = View.query.join(Post).filter(
            Post.user_id == current_user.id,
            func.date(View.created_at) == date.date()
        ).count()
        daily_views.append({
            'date': date.strftime('%d.%m'),
            'views': views
        })
    
    return render_template('author/dashboard.html',
                         posts_count=posts_count,
                         published_posts=published_posts,
                         draft_posts=draft_posts,
                         total_views=total_views,
                         comments_count=comments_count,
                         likes_count=likes_count,
                         bookmarks_count=bookmarks_count,
                         popular_posts=popular_posts,
                         recent_comments=recent_comments,
                         daily_views=daily_views)

@bp.route('/analytics/<int:post_id>')
@login_required
def post_analytics(post_id):
    """Детальная аналитика поста"""
    post = Post.query.get_or_404(post_id)
    
    # Проверяем, что это пост текущего пользователя
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Статистика просмотров по дням
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_views = db.session.query(
        func.date(View.created_at).label('date'),
        func.count(View.id).label('count')
    ).filter(
        View.post_id == post_id,
        View.created_at >= seven_days_ago
    ).group_by(func.date(View.created_at)).all()
    
    # Источники трафика
    referrers = db.session.query(
        View.referrer,
        func.count(View.id).label('count')
    ).filter(
        View.post_id == post_id,
        View.referrer.isnot(None)
    ).group_by(View.referrer).order_by(func.count(View.id).desc()).limit(10).all()
    
    # География просмотров (если есть данные)
    # Это заглушка - в реальном приложении нужно использовать GeoIP
    geography = []
    
    # Время чтения (примерное)
    word_count = len(post.content.split())
    reading_time = max(1, word_count // 200)  # ~200 слов в минуту
    
    return render_template('author/post_analytics.html',
                         post=post,
                         daily_views=daily_views,
                         referrers=referrers,
                         geography=geography,
                         reading_time=reading_time)

@bp.route('/earnings')
@login_required
def earnings():
    """Страница доходов автора (заглушка)"""
    # В реальном приложении здесь была бы интеграция с платежной системой
    return render_template('author/earnings.html',
                         total_earnings=0,
                         pending_earnings=0,
                         paid_earnings=0)