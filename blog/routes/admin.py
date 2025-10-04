"""
Админ-панель
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from blog.models import User, Post, Category, Comment, Tag
from blog.forms import CategoryForm
from blog.database import db
from functools import wraps

bp = Blueprint('admin', __name__)

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('У вас нет прав доступа к админ-панели', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Главная страница админ-панели"""
    # Статистика
    stats = {
        'total_posts': Post.query.count(),
        'published_posts': Post.query.filter_by(is_published=True).count(),
        'total_users': User.query.count(),
        'total_comments': Comment.query.count(),
        'pending_comments': Comment.query.filter_by(is_approved=False).count(),
        'total_categories': Category.query.count()
    }
    
    # Последние посты
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    # Последние комментарии
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    # Популярные посты
    popular_posts = Post.query.filter_by(is_published=True)\
        .order_by(Post.views_count.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments,
                         popular_posts=popular_posts)

@bp.route('/posts')
@login_required
@admin_required
def posts():
    """Управление постами"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc())\
        .paginate(
            page=page,
            per_page=20,
            error_out=False
        )
    return render_template('admin/posts.html', posts=posts)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Управление пользователями"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc())\
        .paginate(
            page=page,
            per_page=20,
            error_out=False
        )
    return render_template('admin/users.html', users=users)

@bp.route('/comments')
@login_required
@admin_required
def comments():
    """Управление комментариями"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Comment.query
    if status == 'pending':
        query = query.filter_by(is_approved=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    
    comments = query.order_by(Comment.created_at.desc())\
        .paginate(
            page=page,
            per_page=20,
            error_out=False
        )
    return render_template('admin/comments.html', comments=comments, status=status)

@bp.route('/comment/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_comment(id):
    """Одобрение комментария"""
    comment = Comment.query.get_or_404(id)
    comment.is_approved = True
    db.session.commit()
    flash('Комментарий одобрен', 'success')
    return redirect(url_for('admin.comments'))

@bp.route('/comment/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_comment(id):
    """Отклонение комментария"""
    comment = Comment.query.get_or_404(id)
    comment.is_approved = False
    db.session.commit()
    flash('Комментарий отклонен', 'warning')
    return redirect(url_for('admin.comments'))

@bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(id):
    """Удаление комментария"""
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('Комментарий удален', 'success')
    return redirect(url_for('admin.comments'))

@bp.route('/categories')
@login_required
@admin_required
def categories():
    """Управление категориями"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/category/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """Создание категории"""
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Категория создана успешно!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/create_category.html', form=form)

@bp.route('/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    """Редактирование категории"""
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.color = form.color.data
        db.session.commit()
        flash('Категория обновлена успешно!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/edit_category.html', form=form, category=category)

@bp.route('/category/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    """Удаление категории"""
    category = Category.query.get_or_404(id)
    
    # Проверяем, есть ли посты в этой категории
    if category.posts.count() > 0:
        flash('Нельзя удалить категорию, в которой есть посты', 'error')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Категория удалена успешно!', 'success')
    return redirect(url_for('admin.categories'))

@bp.route('/user/<int:id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(id):
    """Переключение статуса администратора пользователя"""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Вы не можете изменить свой собственный статус администратора', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'администратором' if user.is_admin else 'обычным пользователем'
    flash(f'Пользователь {user.username} теперь является {status}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(id):
    """Активация/деактивация пользователя"""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Вы не можете деактивировать свой собственный аккаунт', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'активирован' if user.is_active else 'деактивирован'
    flash(f'Пользователь {user.username} {status}', 'success')
    return redirect(url_for('admin.users'))