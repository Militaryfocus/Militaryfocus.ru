"""
Основные маршруты приложения
"""

from flask import Blueprint, render_template, request, current_app
from blog.models import Post, Category, Comment
from blog import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Главная страница"""
    page = request.args.get('page', 1, type=int)
    
    # Получаем опубликованные посты с пагинацией
    posts = Post.query.filter_by(is_published=True)\
        .order_by(Post.created_at.desc())\
        .paginate(
            page=page,
            per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False
        )
    
    # Получаем рекомендуемые посты
    featured_posts = Post.query.filter_by(is_published=True, is_featured=True)\
        .order_by(Post.created_at.desc())\
        .limit(3).all()
    
    # Получаем популярные посты
    popular_posts = Post.query.filter_by(is_published=True)\
        .order_by(Post.views_count.desc())\
        .limit(5).all()
    
    # Получаем последние комментарии
    recent_comments = Comment.query.filter_by(is_approved=True)\
        .order_by(Comment.created_at.desc())\
        .limit(5).all()
    
    return render_template('index.html',
                         posts=posts,
                         featured_posts=featured_posts,
                         popular_posts=popular_posts,
                         recent_comments=recent_comments)

@bp.route('/about')
def about():
    """Страница о блоге"""
    return render_template('about.html')

@bp.route('/contact')
def contact():
    """Страница контактов"""
    return render_template('contact.html')

@bp.route('/search')
def search():
    """Поиск по блогу"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if query:
        posts = Post.query.filter_by(is_published=True)\
            .filter(Post.title.contains(query) | Post.content.contains(query))\
            .order_by(Post.created_at.desc())\
            .paginate(
                page=page,
                per_page=current_app.config['POSTS_PER_PAGE'],
                error_out=False
            )
    else:
        posts = Post.query.filter_by(id=0).paginate(page=1, per_page=1, error_out=False)
    
    return render_template('search.html', posts=posts, query=query)