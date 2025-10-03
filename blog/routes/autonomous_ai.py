"""
Веб-интерфейс для автономной ИИ системы
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from blog.autonomous_ai import (
    autonomous_manager,
    start_autonomous_content_generation,
    get_autonomous_stats
)
from blog.models import Category, Tag, Post
from blog import db
import json

bp = Blueprint('autonomous_ai', __name__, url_prefix='/autonomous')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Панель управления автономной ИИ системой"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа к автономной ИИ системе', 'error')
        return redirect(url_for('main.index'))
    
    # Получаем статистику
    stats = get_autonomous_stats()
    
    # Получаем текущие категории
    categories = Category.query.all()
    
    # Получаем популярные теги
    popular_tags = db.session.query(Tag.name, db.func.count(Tag.id)).join(
        Tag.posts
    ).group_by(Tag.name).order_by(db.func.count(Tag.id).desc()).limit(10).all()
    
    # Получаем последние посты
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template('autonomous_ai/dashboard.html',
                         stats=stats,
                         categories=categories,
                         popular_tags=popular_tags,
                         recent_posts=recent_posts)

@bp.route('/generate', methods=['POST'])
@login_required
def generate_content():
    """Запуск автономной генерации контента"""
    if not current_user.is_admin:
        return jsonify({'error': 'Недостаточно прав доступа'}), 403
    
    try:
        results = start_autonomous_content_generation()
        
        return jsonify({
            'success': True,
            'message': 'Автономная генерация завершена успешно',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/stats')
@login_required
def get_stats():
    """Получение статистики автономной системы"""
    if not current_user.is_admin:
        return jsonify({'error': 'Недостаточно прав доступа'}), 403
    
    try:
        stats = get_autonomous_stats()
        
        # Дополнительная статистика
        categories_count = Category.query.count()
        tags_count = Tag.query.count()
        posts_count = Post.query.count()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'additional': {
                'total_categories': categories_count,
                'total_tags': tags_count,
                'total_posts': posts_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/trends')
@login_required
def analyze_trends():
    """Анализ трендов"""
    if not current_user.is_admin:
        return jsonify({'error': 'Недостаточно прав доступа'}), 403
    
    try:
        trends = autonomous_manager.trend_analyzer.analyze_current_trends()
        
        return jsonify({
            'success': True,
            'trends': trends
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/categories')
@login_required
def manage_categories():
    """Управление категориями"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    categories = Category.query.all()
    
    return render_template('autonomous_ai/categories.html', categories=categories)

@bp.route('/tags')
@login_required
def manage_tags():
    """Управление тегами"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    # Получаем теги с количеством постов
    tags_with_count = db.session.query(
        Tag.name, 
        Tag.created_at,
        db.func.count(Tag.id).label('posts_count')
    ).join(Tag.posts).group_by(Tag.id).order_by(db.func.count(Tag.id).desc()).all()
    
    return render_template('autonomous_ai/tags.html', tags=tags_with_count)

@bp.route('/settings')
@login_required
def settings():
    """Настройки автономной системы"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('autonomous_ai/settings.html')

@bp.route('/logs')
@login_required
def logs():
    """Логи автономной системы"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    # Здесь можно добавить логирование действий автономной системы
    logs = [
        {
            'timestamp': '2024-01-15 10:30:00',
            'action': 'Автономная генерация',
            'result': 'Создано 3 категории, 15 тегов, 5 постов',
            'status': 'success'
        },
        {
            'timestamp': '2024-01-15 09:15:00',
            'action': 'Анализ трендов',
            'result': 'Проанализировано 10 трендов',
            'status': 'success'
        }
    ]
    
    return render_template('autonomous_ai/logs.html', logs=logs)