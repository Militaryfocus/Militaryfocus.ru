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

@bp.route('/popular')
def popular():
    """Популярные посты"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(is_published=True)\
        .order_by(Post.views_count.desc())\
        .paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    return render_template('blog/popular.html', posts=posts, title='Популярные посты')

@bp.route('/recent')
def recent():
    """Недавние посты"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(is_published=True)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    return render_template('blog/recent.html', posts=posts, title='Свежие посты')

@bp.route('/tags')
def tags():
    """Страница тегов"""
    # Получаем популярные теги из постов
    popular_tags = [
        {'name': 'Python', 'count': 15, 'color': '#3776ab'},
        {'name': 'Flask', 'count': 12, 'color': '#000000'},
        {'name': 'Web Development', 'count': 10, 'color': '#61dafb'},
        {'name': 'Programming', 'count': 8, 'color': '#f7df1e'},
        {'name': 'Tutorial', 'count': 7, 'color': '#28a745'},
        {'name': 'AI', 'count': 6, 'color': '#ff6b6b'},
        {'name': 'Machine Learning', 'count': 5, 'color': '#4ecdc4'},
        {'name': 'Data Science', 'count': 4, 'color': '#45b7d1'},
        {'name': 'JavaScript', 'count': 3, 'color': '#f39c12'},
        {'name': 'CSS', 'count': 2, 'color': '#e74c3c'}
    ]
    
    return render_template('blog/tags.html', tags=popular_tags, title='Теги')

@bp.route('/authors')
def authors():
    """Страница авторов"""
    authors = User.query.filter(User.posts.any()).all()
    return render_template('blog/authors.html', authors=authors, title='Авторы')

@bp.route('/bookmarks')
@login_required
def bookmarks():
    """Закладки пользователя"""
    # Здесь можно добавить модель Bookmark
    return render_template('blog/bookmarks.html', title='Мои закладки')

@bp.route('/history')
@login_required
def history():
    """История чтения пользователя"""
    # Здесь можно добавить модель ReadingHistory
    return render_template('blog/history.html', title='История чтения')