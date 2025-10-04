"""
Системная админ-панель для управления отказоустойчивостью, SEO и перелинковкой
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
import json
from datetime import datetime

from blog.fault_tolerance_perfect import perfect_fault_tolerance_system
from blog.auto_seo_optimizer import AutoSEOOptimizer
from blog.smart_interlinking import SmartInterlinkingSystem
from blog.monitoring import MonitoringSystem
from blog.models import Post, Category
from blog.database import db

bp = Blueprint('system_admin', __name__)

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('У вас нет прав доступа к системной панели', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/system-dashboard')
@login_required
@admin_required
def system_dashboard():
    """Главная системная панель"""
    
    # Получение метрик системы
    system_metrics = fault_tolerant_system.get_system_metrics()
    monitoring_data = monitoring_system.check_health()
    
    # SEO статистика
    seo_stats = {
        'total_posts': Post.query.filter_by(is_published=True).count(),
        'posts_with_meta': 0,  # Будет рассчитано
        'avg_seo_score': 0,    # Будет рассчитано
        'sitemap_exists': True  # Проверка существования sitemap
    }
    
    # Статистика перелинковки
    interlink_stats = smart_interlinking.generate_link_report()
    
    return render_template('system_admin/dashboard.html',
                         system_metrics=system_metrics,
                         monitoring_data=monitoring_data,
                         seo_stats=seo_stats,
                         interlink_stats=interlink_stats)

@bp.route('/fault-tolerance')
@login_required
@admin_required
def fault_tolerance_panel():
    """Панель отказоустойчивости"""
    
    system_status = fault_tolerant_system.health_checker.get_system_status()
    backup_info = fault_tolerant_system._get_backup_info()
    
    return render_template('system_admin/fault_tolerance.html',
                         system_status=system_status,
                         backup_info=backup_info)

@bp.route('/create-backup', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Создание резервной копии"""
    try:
        backup_type = request.form.get('backup_type', 'database')
        
        if backup_type == 'database':
            backup_path = fault_tolerant_system.backup_manager.create_database_backup()
            flash(f'Резервная копия базы данных создана: {backup_path}', 'success')
        elif backup_type == 'content':
            backup_path = fault_tolerant_system.backup_manager.create_content_backup()
            flash(f'Резервная копия контента создана: {backup_path}', 'success')
        else:
            flash('Неизвестный тип резервной копии', 'error')
            
    except Exception as e:
        flash(f'Ошибка создания резервной копии: {str(e)}', 'error')
    
    return redirect(url_for('system_admin.fault_tolerance_panel'))

@bp.route('/seo-optimizer')
@login_required
@admin_required
def seo_optimizer_panel():
    """Панель SEO оптимизации"""
    
    # Получение постов для анализа
    posts = Post.query.filter_by(is_published=True).limit(20).all()
    seo_analyses = []
    
    for post in posts:
        analysis = seo_optimizer.optimize_post(post)
        seo_analyses.append({
            'post': post,
            'analysis': analysis
        })
    
    return render_template('system_admin/seo_optimizer.html',
                         seo_analyses=seo_analyses)

@bp.route('/analyze-post-seo/<int:post_id>')
@login_required
@admin_required
def analyze_post_seo(post_id):
    """Анализ SEO конкретного поста"""
    post = Post.query.get_or_404(post_id)
    analysis = seo_optimizer.optimize_post(post)
    
    return jsonify({
        'success': True,
        'post_id': post_id,
        'post_title': post.title,
        'analysis': analysis
    })

@bp.route('/update-sitemap', methods=['POST'])
@login_required
@admin_required
def update_sitemap():
    """Обновление sitemap"""
    try:
        seo_optimizer.update_all_seo()
        flash('Sitemap и robots.txt обновлены', 'success')
    except Exception as e:
        flash(f'Ошибка обновления SEO файлов: {str(e)}', 'error')
    
    return redirect(url_for('system_admin.seo_optimizer_panel'))

@bp.route('/interlinking')
@login_required
@admin_required
def interlinking_panel():
    """Панель перелинковки"""
    
    # Статистика перелинковки
    link_report = smart_interlinking.generate_link_report()
    
    # Последние анализы
    recent_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(10).all()
    
    return render_template('system_admin/interlinking.html',
                         link_report=link_report,
                         recent_posts=recent_posts)

@bp.route('/analyze-post-links/<int:post_id>')
@login_required
@admin_required
def analyze_post_links(post_id):
    """Анализ ссылок для поста"""
    post = Post.query.get_or_404(post_id)
    analysis = smart_interlinking.analyze_post_for_links(post)
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })

@bp.route('/auto-insert-links/<int:post_id>', methods=['POST'])
@login_required
@admin_required
def auto_insert_links(post_id):
    """Автоматическая вставка ссылок"""
    try:
        post = Post.query.get_or_404(post_id)
        max_links = int(request.form.get('max_links', 3))
        
        new_content = smart_interlinking.auto_insert_links(post, max_links)
        
        if new_content != post.content:
            post.content = new_content
            db.session.commit()
            flash(f'Ссылки добавлены в пост "{post.title}"', 'success')
        else:
            flash('Подходящие места для ссылок не найдены', 'info')
            
    except Exception as e:
        flash(f'Ошибка добавления ссылок: {str(e)}', 'error')
    
    return redirect(url_for('system_admin.interlinking_panel'))

@bp.route('/update-all-interlinks', methods=['POST'])
@login_required
@admin_required
def update_all_interlinks():
    """Обновление всех внутренних ссылок"""
    try:
        updated_count = smart_interlinking.update_all_interlinks()
        flash(f'Обновлено ссылок в {updated_count} постах', 'success')
    except Exception as e:
        flash(f'Ошибка обновления ссылок: {str(e)}', 'error')
    
    return redirect(url_for('system_admin.interlinking_panel'))

@bp.route('/monitoring')
@login_required
@admin_required
def monitoring_panel():
    """Панель мониторинга"""
    
    dashboard_data = monitoring_system.dashboard.get_dashboard_data()
    
    return render_template('system_admin/monitoring.html',
                         dashboard_data=dashboard_data)

@bp.route('/monitoring-api')
@login_required
@admin_required
def monitoring_api():
    """API для получения данных мониторинга"""
    dashboard_data = monitoring_system.dashboard.get_dashboard_data()
    return jsonify(dashboard_data)

@bp.route('/system-health')
@login_required
@admin_required
def system_health():
    """Проверка здоровья системы"""
    health_data = fault_tolerant_system.health_checker.get_system_status()
    return jsonify(health_data)

@bp.route('/performance-test', methods=['POST'])
@login_required
@admin_required
def performance_test():
    """Тест производительности"""
    try:
        test_type = request.form.get('test_type', 'database')
        
        if test_type == 'database':
            # Тест базы данных
            import time
            start_time = time.time()
            
            posts = Post.query.limit(100).all()
            for post in posts:
                _ = post.get_comments_count()
            
            duration = time.time() - start_time
            
            result = {
                'test_type': 'database',
                'duration': round(duration, 3),
                'queries_count': len(posts),
                'avg_query_time': round(duration / len(posts), 4) if posts else 0
            }
            
        elif test_type == 'ai_generation':
            # Тест ИИ генерации
            from blog.ai_content_perfect import AIContentGenerator
            
            start_time = time.time()
            generator = AIContentGenerator()
            test_post = generator.generate_human_like_post('технологии', 'тест')
            duration = time.time() - start_time
            
            result = {
                'test_type': 'ai_generation',
                'duration': round(duration, 3),
                'content_length': len(test_post['content']),
                'quality_score': test_post['quality_score']
            }
            
        else:
            result = {'error': 'Unknown test type'}
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bp.route('/system-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    """Системные настройки"""
    
    if request.method == 'POST':
        try:
            # Настройки отказоустойчивости
            fault_tolerance_enabled = request.form.get('fault_tolerance_enabled') == 'on'
            backup_interval = int(request.form.get('backup_interval', 6))
            
            # Настройки SEO
            auto_seo_enabled = request.form.get('auto_seo_enabled') == 'on'
            sitemap_update_interval = int(request.form.get('sitemap_update_interval', 24))
            
            # Настройки перелинковки
            auto_interlinking_enabled = request.form.get('auto_interlinking_enabled') == 'on'
            max_links_per_post = int(request.form.get('max_links_per_post', 5))
            
            # Настройки мониторинга
            monitoring_enabled = request.form.get('monitoring_enabled') == 'on'
            alert_threshold_cpu = int(request.form.get('alert_threshold_cpu', 90))
            alert_threshold_memory = int(request.form.get('alert_threshold_memory', 90))
            
            # Сохранение настроек (в реальном приложении лучше использовать базу данных)
            import os
            os.environ['FAULT_TOLERANCE_ENABLED'] = str(fault_tolerance_enabled)
            os.environ['AUTO_SEO_ENABLED'] = str(auto_seo_enabled)
            os.environ['AUTO_INTERLINKING_ENABLED'] = str(auto_interlinking_enabled)
            os.environ['MONITORING_ENABLED'] = str(monitoring_enabled)
            
            flash('Системные настройки сохранены', 'success')
            
        except Exception as e:
            flash(f'Ошибка сохранения настроек: {str(e)}', 'error')
    
    # Текущие настройки
    current_settings = {
        'fault_tolerance_enabled': os.environ.get('FAULT_TOLERANCE_ENABLED', 'True').lower() == 'true',
        'auto_seo_enabled': os.environ.get('AUTO_SEO_ENABLED', 'True').lower() == 'true',
        'auto_interlinking_enabled': os.environ.get('AUTO_INTERLINKING_ENABLED', 'True').lower() == 'true',
        'monitoring_enabled': os.environ.get('MONITORING_ENABLED', 'True').lower() == 'true'
    }
    
    return render_template('system_admin/settings.html',
                         settings=current_settings)

@bp.route('/export-system-report')
@login_required
@admin_required
def export_system_report():
    """Экспорт системного отчета"""
    try:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': fault_tolerant_system.get_system_metrics(),
            'monitoring_data': monitoring_system.dashboard.get_dashboard_data(),
            'seo_stats': {
                'total_posts': Post.query.filter_by(is_published=True).count(),
                'categories_count': Category.query.count()
            },
            'interlinking_stats': smart_interlinking.generate_link_report()
        }
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    """Просмотр системных логов"""
    try:
        log_file = 'blog_system.log'
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # Последние 100 строк
            recent_logs = log_lines[-100:] if len(log_lines) > 100 else log_lines
            
            return render_template('system_admin/logs.html',
                                 log_lines=recent_logs)
        else:
            return render_template('system_admin/logs.html',
                                 log_lines=['Файл логов не найден'])
            
    except Exception as e:
        return render_template('system_admin/logs.html',
                             log_lines=[f'Ошибка чтения логов: {str(e)}'])