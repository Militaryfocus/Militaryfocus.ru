"""
Админ-панель для управления ИИ контентом
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from blog.models import Post, Category, User, Comment
from blog.ai_content_perfect import PerfectAIContentGenerator, ContentScheduler, populate_blog_with_ai_content
from blog import db
from functools import wraps
import threading
import os

bp = Blueprint('ai_admin', __name__)

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('У вас нет прав доступа к ИИ панели', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/ai-dashboard')
@login_required
@admin_required
def ai_dashboard():
    """Панель управления ИИ контентом"""
    
    # Статистика ИИ контента
    ai_stats = {
        'total_ai_posts': Post.query.filter(Post.content.contains('## ')).count(),
        'ai_posts_today': Post.query.filter(
            Post.created_at >= db.func.date('now'),
            Post.content.contains('## ')
        ).count(),
        'ai_comments': Comment.query.join(User).filter(
            User.username.like('fake_%') | User.email.like('%@example.%')
        ).count(),
        'content_quality_avg': 0.85,  # Средняя оценка качества
        'ai_enabled': os.environ.get('AI_CONTENT_ENABLED', 'False').lower() == 'true'
    }
    
    # Последние ИИ посты
    recent_ai_posts = Post.query.filter(
        Post.content.contains('## ')
    ).order_by(Post.created_at.desc()).limit(10).all()
    
    return render_template('ai_admin/dashboard.html', 
                         stats=ai_stats, 
                         recent_posts=recent_ai_posts)

@bp.route('/generate-post', methods=['POST'])
@login_required
@admin_required
def generate_single_post():
    """Генерация одного поста"""
    try:
        category_name = request.form.get('category')
        topic = request.form.get('topic')
        
        scheduler = ContentScheduler()
        generator = AIContentGenerator()
        
        # Генерируем контент
        if topic:
            post_data = generator.generate_human_like_post(category_name, topic)
        else:
            post_data = generator.generate_human_like_post(category_name)
        
        # Создаем пост
        if scheduler.create_scheduled_post(category_name):
            flash(f'ИИ пост "{post_data["title"]}" успешно создан!', 'success')
        else:
            flash('Ошибка при создании ИИ поста', 'error')
            
    except Exception as e:
        flash(f'Ошибка генерации: {str(e)}', 'error')
    
    return redirect(url_for('ai_admin.ai_dashboard'))

@bp.route('/bulk-generate', methods=['POST'])
@login_required
@admin_required
def bulk_generate_posts():
    """Массовая генерация постов"""
    try:
        num_posts = int(request.form.get('num_posts', 5))
        
        if num_posts > 50:
            flash('Максимальное количество постов за раз: 50', 'error')
            return redirect(url_for('ai_admin.ai_dashboard'))
        
        # Запускаем генерацию в отдельном потоке
        def generate_in_background():
            with db.app.app_context():
                populate_blog_with_ai_content(num_posts)
        
        thread = threading.Thread(target=generate_in_background)
        thread.daemon = True
        thread.start()
        
        flash(f'Запущена генерация {num_posts} постов в фоновом режиме', 'info')
        
    except ValueError:
        flash('Некорректное количество постов', 'error')
    except Exception as e:
        flash(f'Ошибка массовой генерации: {str(e)}', 'error')
    
    return redirect(url_for('ai_admin.ai_dashboard'))

@bp.route('/ai-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def ai_settings():
    """Настройки ИИ системы"""
    
    if request.method == 'POST':
        try:
            # Обновляем настройки
            settings = {
                'ai_enabled': request.form.get('ai_enabled') == 'on',
                'auto_publish': request.form.get('auto_publish') == 'on',
                'generate_comments': request.form.get('generate_comments') == 'on',
                'posts_per_day': int(request.form.get('posts_per_day', 3)),
                'min_quality_score': float(request.form.get('min_quality_score', 0.7)),
                'openai_api_key': request.form.get('openai_api_key', ''),
                'content_style': request.form.get('content_style', 'mixed')
            }
            
            # Сохраняем в переменные окружения (в реальном приложении лучше использовать базу данных)
            os.environ['AI_CONTENT_ENABLED'] = str(settings['ai_enabled'])
            os.environ['AI_AUTO_PUBLISH'] = str(settings['auto_publish'])
            os.environ['AI_GENERATE_COMMENTS'] = str(settings['generate_comments'])
            os.environ['AI_POSTS_PER_DAY'] = str(settings['posts_per_day'])
            os.environ['AI_MIN_QUALITY'] = str(settings['min_quality_score'])
            
            if settings['openai_api_key']:
                os.environ['OPENAI_API_KEY'] = settings['openai_api_key']
            
            flash('Настройки ИИ успешно сохранены!', 'success')
            
        except Exception as e:
            flash(f'Ошибка сохранения настроек: {str(e)}', 'error')
    
    # Текущие настройки
    current_settings = {
        'ai_enabled': os.environ.get('AI_CONTENT_ENABLED', 'False').lower() == 'true',
        'auto_publish': os.environ.get('AI_AUTO_PUBLISH', 'True').lower() == 'true',
        'generate_comments': os.environ.get('AI_GENERATE_COMMENTS', 'True').lower() == 'true',
        'posts_per_day': int(os.environ.get('AI_POSTS_PER_DAY', 3)),
        'min_quality_score': float(os.environ.get('AI_MIN_QUALITY', 0.7)),
        'openai_configured': bool(os.environ.get('OPENAI_API_KEY')),
        'content_style': os.environ.get('AI_CONTENT_STYLE', 'mixed')
    }
    
    return render_template('ai_admin/settings.html', settings=current_settings)

@bp.route('/preview-content')
@login_required
@admin_required
def preview_ai_content():
    """Предпросмотр ИИ контента"""
    try:
        category = request.args.get('category')
        topic = request.args.get('topic')
        
        generator = AIContentGenerator()
        post_data = generator.generate_human_like_post(category, topic)
        
        return jsonify({
            'success': True,
            'data': post_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bp.route('/content-analytics')
@login_required
@admin_required
def content_analytics():
    """Аналитика ИИ контента"""
    
    # Статистика по качеству контента
    ai_posts = Post.query.filter(Post.content.contains('## ')).all()
    
    analytics = {
        'total_posts': len(ai_posts),
        'avg_length': sum(len(post.content.split()) for post in ai_posts) / len(ai_posts) if ai_posts else 0,
        'avg_views': sum(post.views_count for post in ai_posts) / len(ai_posts) if ai_posts else 0,
        'avg_comments': sum(post.get_comments_count() for post in ai_posts) / len(ai_posts) if ai_posts else 0,
        'categories_distribution': {},
        'monthly_stats': {}
    }
    
    # Распределение по категориям
    for post in ai_posts:
        if post.category:
            cat_name = post.category.name
            analytics['categories_distribution'][cat_name] = analytics['categories_distribution'].get(cat_name, 0) + 1
    
    # Статистика по месяцам
    from collections import defaultdict
    monthly = defaultdict(int)
    for post in ai_posts:
        month_key = post.created_at.strftime('%Y-%m')
        monthly[month_key] += 1
    
    analytics['monthly_stats'] = dict(monthly)
    
    return render_template('ai_admin/analytics.html', analytics=analytics)

@bp.route('/manage-ai-users')
@login_required
@admin_required
def manage_ai_users():
    """Управление ИИ пользователями"""
    
    # Находим ИИ пользователей (фейковых)
    ai_users = User.query.filter(
        User.username.like('fake_%') | 
        User.email.like('%@example.%') |
        User.bio.like('%Lorem%')
    ).all()
    
    return render_template('ai_admin/ai_users.html', ai_users=ai_users)

@bp.route('/delete-ai-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_ai_user(user_id):
    """Удаление ИИ пользователя"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Проверяем, что это действительно ИИ пользователь
        if not (user.username.startswith('fake_') or '@example.' in user.email):
            flash('Можно удалять только ИИ пользователей', 'error')
            return redirect(url_for('ai_admin.manage_ai_users'))
        
        # Удаляем пользователя и его комментарии
        Comment.query.filter_by(author_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        
        flash(f'ИИ пользователь {user.username} удален', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления: {str(e)}', 'error')
    
    return redirect(url_for('ai_admin.manage_ai_users'))

@bp.route('/cleanup-ai-content', methods=['POST'])
@login_required
@admin_required
def cleanup_ai_content():
    """Очистка ИИ контента"""
    try:
        cleanup_type = request.form.get('cleanup_type')
        
        if cleanup_type == 'posts':
            # Удаляем ИИ посты
            ai_posts = Post.query.filter(Post.content.contains('## ')).all()
            for post in ai_posts:
                db.session.delete(post)
            db.session.commit()
            flash(f'Удалено {len(ai_posts)} ИИ постов', 'success')
            
        elif cleanup_type == 'comments':
            # Удаляем ИИ комментарии
            ai_comments = Comment.query.join(User).filter(
                User.username.like('fake_%') | User.email.like('%@example.%')
            ).all()
            for comment in ai_comments:
                db.session.delete(comment)
            db.session.commit()
            flash(f'Удалено {len(ai_comments)} ИИ комментариев', 'success')
            
        elif cleanup_type == 'users':
            # Удаляем ИИ пользователей
            ai_users = User.query.filter(
                User.username.like('fake_%') | User.email.like('%@example.%')
            ).all()
            for user in ai_users:
                Comment.query.filter_by(author_id=user.id).delete()
                db.session.delete(user)
            db.session.commit()
            flash(f'Удалено {len(ai_users)} ИИ пользователей', 'success')
            
        else:
            flash('Неизвестный тип очистки', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка очистки: {str(e)}', 'error')
    
    return redirect(url_for('ai_admin.ai_dashboard'))

@bp.route('/export-ai-content')
@login_required
@admin_required
def export_ai_content():
    """Экспорт ИИ контента"""
    try:
        ai_posts = Post.query.filter(Post.content.contains('## ')).all()
        
        export_data = []
        for post in ai_posts:
            export_data.append({
                'title': post.title,
                'content': post.content,
                'category': post.category.name if post.category else None,
                'tags': [tag.name for tag in post.tags],
                'created_at': post.created_at.isoformat(),
                'views': post.views_count,
                'comments': post.get_comments_count()
            })
        
        return jsonify({
            'success': True,
            'data': export_data,
            'count': len(export_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })