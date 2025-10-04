"""
Маршруты для экспорта контента
"""
from flask import Blueprint, Response, abort, request
from flask_login import login_required, current_user
from models import Post, User
from utils.pdf_export import export_post_to_pdf, export_posts_to_pdf
import zipfile
from io import BytesIO

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route('/post/<slug>/pdf')
def export_post_pdf(slug):
    """Экспорт одного поста в PDF"""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Генерируем PDF
    pdf_buffer = export_post_to_pdf(post)
    
    # Отправляем файл
    filename = f"{post.slug}.pdf"
    
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@bp.route('/my-posts/pdf')
@login_required
def export_my_posts_pdf():
    """Экспорт всех постов текущего пользователя в PDF"""
    posts = Post.query.filter_by(
        user_id=current_user.id,
        is_published=True
    ).order_by(Post.created_at.desc()).all()
    
    if not posts:
        abort(404, "У вас нет опубликованных постов")
    
    # Генерируем PDF
    title = f"Посты автора {current_user.username}"
    pdf_buffer = export_posts_to_pdf(posts, title)
    
    # Отправляем файл
    filename = f"posts_{current_user.username}.pdf"
    
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@bp.route('/category/<slug>/pdf')
def export_category_pdf(slug):
    """Экспорт всех постов категории в PDF"""
    from models import Category
    
    category = Category.query.filter_by(slug=slug).first_or_404()
    posts = Post.query.filter_by(
        category_id=category.id,
        is_published=True
    ).order_by(Post.created_at.desc()).limit(50).all()  # Ограничиваем 50 постами
    
    if not posts:
        abort(404, "В этой категории нет постов")
    
    # Генерируем PDF
    title = f"Посты в категории: {category.name}"
    pdf_buffer = export_posts_to_pdf(posts, title)
    
    # Отправляем файл
    filename = f"category_{category.slug}.pdf"
    
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@bp.route('/selected-posts/pdf', methods=['POST'])
@login_required
def export_selected_posts_pdf():
    """Экспорт выбранных постов в PDF"""
    post_ids = request.form.getlist('post_ids[]')
    
    if not post_ids:
        abort(400, "Не выбраны посты для экспорта")
    
    # Получаем посты
    posts = Post.query.filter(
        Post.id.in_(post_ids),
        Post.is_published == True
    ).all()
    
    if not posts:
        abort(404, "Посты не найдены")
    
    # Проверяем права доступа
    for post in posts:
        if not post.is_published and post.user_id != current_user.id and not current_user.is_admin:
            abort(403, "Нет доступа к некоторым постам")
    
    # Генерируем PDF
    title = f"Выбранные посты ({len(posts)} шт.)"
    pdf_buffer = export_posts_to_pdf(posts, title)
    
    # Отправляем файл
    filename = "selected_posts.pdf"
    
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@bp.route('/bulk-export', methods=['POST'])
@login_required 
def bulk_export():
    """Массовый экспорт в ZIP архив"""
    if not current_user.is_admin:
        abort(403)
    
    export_type = request.form.get('type', 'all')
    format = request.form.get('format', 'pdf')
    
    # Получаем посты в зависимости от типа
    if export_type == 'all':
        posts = Post.query.filter_by(is_published=True).all()
    elif export_type == 'user':
        user_id = request.form.get('user_id')
        posts = Post.query.filter_by(user_id=user_id, is_published=True).all()
    elif export_type == 'category':
        category_id = request.form.get('category_id')
        posts = Post.query.filter_by(category_id=category_id, is_published=True).all()
    else:
        abort(400, "Неверный тип экспорта")
    
    if not posts:
        abort(404, "Нет постов для экспорта")
    
    # Создаем ZIP архив в памяти
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for post in posts:
            if format == 'pdf':
                # Экспортируем в PDF
                pdf_buffer = export_post_to_pdf(post)
                filename = f"{post.slug}.pdf"
                zip_file.writestr(filename, pdf_buffer.getvalue())
            elif format == 'txt':
                # Экспортируем в текст
                from utils.pdf_export import strip_html
                content = f"# {post.title}\n\n"
                content += f"Автор: {post.author.username}\n"
                content += f"Дата: {post.created_at.strftime('%d.%m.%Y')}\n\n"
                content += strip_html(post.content)
                filename = f"{post.slug}.txt"
                zip_file.writestr(filename, content.encode('utf-8'))
    
    zip_buffer.seek(0)
    
    # Отправляем архив
    return Response(
        zip_buffer.getvalue(),
        mimetype='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename="posts_export.zip"'
        }
    )