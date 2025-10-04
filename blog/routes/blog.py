"""
Маршруты блога
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from blog.models_perfect import Post, Category, Comment, Tag
from blog.forms import PostForm, CommentForm
from blog import db
from datetime import datetime

bp = Blueprint('blog', __name__)

@bp.route('/post/<slug>')
def post_detail(slug):
    """Детальная страница поста"""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Увеличиваем счетчик просмотров
    post.increment_views()
    
    # Получаем комментарии
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(post_id=post.id, is_approved=True, parent_id=None)\
        .order_by(Comment.created_at.desc())\
        .paginate(
            page=page,
            per_page=current_app.config['COMMENTS_PER_PAGE'],
            error_out=False
        )
    
    # Форма комментария
    comment_form = CommentForm()
    
    # Похожие посты
    related_posts = Post.query.filter_by(category_id=post.category_id, is_published=True)\
        .filter(Post.id != post.id)\
        .order_by(Post.created_at.desc())\
        .limit(3).all()
    
    return render_template('blog/post_detail.html',
                         post=post,
                         comments=comments,
                         comment_form=comment_form,
                         related_posts=related_posts)

@bp.route('/post/<slug>/comment', methods=['POST'])
@login_required
def add_comment(slug):
    """Добавление комментария"""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            author_id=current_user.id,
            post_id=post.id,
            parent_id=form.parent_id.data if form.parent_id.data else None
        )
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен и ожидает модерации', 'success')
    
    return redirect(url_for('blog.post_detail', slug=slug))

@bp.route('/category/<slug>')
def category_posts(slug):
    """Посты по категории"""
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.filter_by(category_id=category.id, is_published=True)\
        .order_by(Post.created_at.desc())\
        .paginate(
            page=page,
            per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False
        )
    
    return render_template('blog/category_posts.html', category=category, posts=posts)

@bp.route('/tag/<slug>')
def tag_posts(slug):
    """Посты по тегу"""
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.filter(Post.tags.contains(tag), Post.is_published == True)\
        .order_by(Post.created_at.desc())\
        .paginate(
            page=page,
            per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False
        )
    
    return render_template('blog/tag_posts.html', tag=tag, posts=posts)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Создание поста"""
    if not current_user.is_admin:
        flash('У вас нет прав для создания постов', 'error')
        return redirect(url_for('main.index'))
    
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            category_id=form.category.data,
            author_id=current_user.id,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data
        )
        
        if form.is_published.data:
            post.published_at = datetime.utcnow()
        
        db.session.add(post)
        db.session.commit()
        
        # Обработка тегов
        if form.tags.data:
            tag_names = [tag.strip() for tag in form.tags.data.split(',')]
            for tag_name in tag_names:
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)
        
        db.session.commit()
        flash('Пост создан успешно!', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))
    
    return render_template('blog/create_post.html', form=form)

@bp.route('/edit/<slug>', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    """Редактирование поста"""
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    if not (current_user.is_admin or current_user.id == post.author_id):
        flash('У вас нет прав для редактирования этого поста', 'error')
        return redirect(url_for('blog.post_detail', slug=slug))
    
    form = PostForm(obj=post)
    form.tags.data = ', '.join([tag.name for tag in post.tags])
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.category_id = form.category.data
        post.is_published = form.is_published.data
        post.is_featured = form.is_featured.data
        post.updated_at = datetime.utcnow()
        
        if form.is_published.data and not post.published_at:
            post.published_at = datetime.utcnow()
        
        # Обновление тегов
        post.tags.clear()
        if form.tags.data:
            tag_names = [tag.strip() for tag in form.tags.data.split(',')]
            for tag_name in tag_names:
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)
        
        db.session.commit()
        flash('Пост обновлен успешно!', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))
    
    return render_template('blog/edit_post.html', form=form, post=post)

@bp.route('/delete/<slug>', methods=['POST'])
@login_required
def delete_post(slug):
    """Удаление поста"""
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    if not (current_user.is_admin or current_user.id == post.author_id):
        flash('У вас нет прав для удаления этого поста', 'error')
        return redirect(url_for('blog.post_detail', slug=slug))
    
    db.session.delete(post)
    db.session.commit()
    flash('Пост удален успешно!', 'success')
    return redirect(url_for('main.index'))