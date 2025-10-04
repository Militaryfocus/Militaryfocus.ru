"""
SEO маршруты для расширенной системы
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from blog.models import Post, Category, Tag, User
from blog.advanced_seo import advanced_seo_optimizer
from blog.auto_seo_optimizer import AutoSEOOptimizer
from blog.seo_analytics import SEOAnalytics
from blog.database import db
from datetime import datetime
import json

bp = Blueprint('seo', __name__, url_prefix='/seo')

@bp.route('/dashboard')
@login_required
def dashboard():
    """SEO дашборд"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа к SEO панели', 'error')
        return redirect(url_for('main.index'))
    
    # Получение SEO аналитики
    analytics = advanced_seo_optimizer.get_seo_analytics()
    
    # Топ посты по SEO рейтингу
    posts = Post.query.filter_by(is_published=True).all()
    seo_scores = []
    
    for post in posts[:10]:  # Топ 10 постов
        issues = advanced_seo_optimizer.analyzer.check_seo_issues(post)
        score = 100 - (len(issues) * 10)  # Простой расчет рейтинга
        seo_scores.append({
            'post': post,
            'score': max(0, score),
            'issues_count': len(issues)
        })
    
    seo_scores.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('seo/dashboard.html', 
                         analytics=analytics,
                         top_posts=seo_scores[:5])

@bp.route('/audit/<int:post_id>')
@login_required
def audit_post(post_id):
    """SEO аудит конкретного поста"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    post = Post.query.get_or_404(post_id)
    
    # Комплексный SEO аудит
    audit_results = advanced_seo_optimizer.comprehensive_seo_audit(post)
    
    return render_template('seo/audit.html', 
                         post=post,
                         audit=audit_results)

@bp.route('/audit/<int:post_id>/json')
@login_required
def audit_post_json(post_id):
    """SEO аудит в формате JSON"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    post = Post.query.get_or_404(post_id)
    audit_results = advanced_seo_optimizer.comprehensive_seo_audit(post)
    
    return jsonify(audit_results)

@bp.route('/test/create', methods=['GET', 'POST'])
@login_required
def create_test():
    """Создание A/B теста"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        post_id = request.form.get('post_id')
        test_type = request.form.get('test_type')
        variant_a = request.form.get('variant_a')
        variant_b = request.form.get('variant_b')
        
        post = Post.query.get_or_404(post_id)
        
        try:
            test_id = advanced_seo_optimizer.create_seo_test(post, test_type, variant_a, variant_b)
            flash(f'A/B тест создан успешно! ID: {test_id}', 'success')
            return redirect(url_for('seo.test_results', test_id=test_id))
        except Exception as e:
            flash(f'Ошибка создания теста: {str(e)}', 'error')
    
    # Получение постов для выбора
    posts = Post.query.filter_by(is_published=True).all()
    
    return render_template('seo/create_test.html', posts=posts)

@bp.route('/test/<test_id>/results')
@login_required
def test_results(test_id):
    """Результаты A/B теста"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    results = advanced_seo_optimizer.ab_testing.get_test_results(test_id)
    
    if not results:
        flash('Тест не найден', 'error')
        return redirect(url_for('seo.dashboard'))
    
    return render_template('seo/test_results.html', results=results)

@bp.route('/competitor/analyze', methods=['GET', 'POST'])
@login_required
def analyze_competitor():
    """Анализ конкурента"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        competitor_url = request.form.get('competitor_url')
        
        try:
            analysis = advanced_seo_optimizer.competitor_analyzer.analyze_competitor_keywords(competitor_url)
            
            if 'error' in analysis:
                flash(f'Ошибка анализа: {analysis["error"]}', 'error')
            else:
                return render_template('seo/competitor_analysis.html', 
                                     competitor_url=competitor_url,
                                     analysis=analysis)
        except Exception as e:
            flash(f'Ошибка анализа конкурента: {str(e)}', 'error')
    
    return render_template('seo/analyze_competitor.html')

@bp.route('/monitoring')
@login_required
def monitoring():
    """SEO мониторинг"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    dashboard_data = advanced_seo_optimizer.monitoring.get_seo_dashboard_data()
    
    return render_template('seo/monitoring.html', data=dashboard_data)

@bp.route('/optimize/<int:post_id>', methods=['POST'])
@login_required
def optimize_post(post_id):
    """Автоматическая SEO оптимизация поста"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    post = Post.query.get_or_404(post_id)
    
    try:
        # Получение рекомендаций
        audit = advanced_seo_optimizer.comprehensive_seo_audit(post)
        recommendations = audit['recommendations']
        
        # Автоматические улучшения
        improvements = []
        
        # Улучшение мета-описания
        if not post.excerpt or len(post.excerpt) < 120:
            post.excerpt = post.content[:160] + '...' if len(post.content) > 160 else post.content
            improvements.append('Улучшено мета-описание')
        
        # Добавление заголовков если их нет
        if not re.search(r'<h[1-6][^>]*>', post.content, re.IGNORECASE):
            # Добавляем H2 заголовок в начало контента
            first_paragraph = post.content.split('\n')[0]
            if len(first_paragraph) > 50:
                post.content = f"## {first_paragraph[:50]}...\n\n{post.content}"
                improvements.append('Добавлен заголовок H2')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'improvements': improvements,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/keywords/analyze', methods=['POST'])
@login_required
def analyze_keywords():
    """Анализ ключевых слов"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        keywords = advanced_seo_optimizer.analyzer.extract_keywords(text, max_keywords=20)
        readability = advanced_seo_optimizer.analyzer.analyze_readability(text)
        
        return jsonify({
            'keywords': keywords,
            'readability': readability
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/sitemap/update')
@login_required
def update_sitemap():
    """Обновление sitemap"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    try:
        from blog.auto_seo_optimizer import AutoSEOOptimizer
        seo_optimizer = AutoSEOOptimizer()
        seo_optimizer.update_all_seo()
        flash('Sitemap и robots.txt обновлены успешно!', 'success')
    except Exception as e:
        flash(f'Ошибка обновления: {str(e)}', 'error')
    
    return redirect(url_for('seo.dashboard'))

@bp.route('/reports/generate')
@login_required
def generate_report():
    """Генерация SEO отчета"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Анализ всех постов
        posts = Post.query.filter_by(is_published=True).all()
        
        report_data = {
            'total_posts': len(posts),
            'posts_analysis': [],
            'overall_stats': {
                'avg_seo_score': 0,
                'posts_with_issues': 0,
                'critical_issues': 0
            }
        }
        
        total_score = 0
        
        for post in posts:
            audit = advanced_seo_optimizer.comprehensive_seo_audit(post)
            report_data['posts_analysis'].append({
                'post_id': post.id,
                'title': post.title,
                'seo_score': audit['overall_score'],
                'issues_count': len(audit['basic_seo']),
                'recommendations': audit['recommendations']
            })
            
            total_score += audit['overall_score']
            
            if len(audit['basic_seo']) > 0:
                report_data['overall_stats']['posts_with_issues'] += 1
            
            critical_issues = [i for i in audit['basic_seo'] if i['type'] == 'error']
            report_data['overall_stats']['critical_issues'] += len(critical_issues)
        
        if posts:
            report_data['overall_stats']['avg_seo_score'] = round(total_score / len(posts), 1)
        
        return render_template('seo/report.html', report=report_data)
        
    except Exception as e:
        flash(f'Ошибка генерации отчета: {str(e)}', 'error')
        return redirect(url_for('seo.dashboard'))

@bp.route('/auto-optimize', methods=['POST'])
@login_required
def auto_optimize_all():
    """Автоматическая оптимизация всех постов"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        results = auto_seo_optimizer.optimize_all_posts()
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/comprehensive')
@login_required
def comprehensive_analytics():
    """Комплексная SEO аналитика"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    try:
        analytics = seo_analytics.get_comprehensive_analytics()
        return render_template('seo/comprehensive_analytics.html', analytics=analytics)
    except Exception as e:
        flash(f'Ошибка получения аналитики: {str(e)}', 'error')
        return redirect(url_for('seo.dashboard'))

@bp.route('/analytics/api')
@login_required
def analytics_api():
    """API для получения аналитики"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        analytics = seo_analytics.get_comprehensive_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/report/download/<format>')
@login_required
def download_report(format):
    """Скачивание SEO отчета"""
    if not current_user.is_admin:
        flash('У вас нет прав доступа', 'error')
        return redirect(url_for('main.index'))
    
    try:
        report_content = seo_analytics.generate_seo_report(format)
        
        if format == 'json':
            from flask import Response
            return Response(
                report_content,
                mimetype='application/json',
                headers={'Content-Disposition': 'attachment; filename=seo_report.json'}
            )
        elif format == 'csv':
            from flask import Response
            return Response(
                report_content,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=seo_report.csv'}
            )
        else:
            flash('Неподдерживаемый формат отчета', 'error')
            return redirect(url_for('seo.dashboard'))
            
    except Exception as e:
        flash(f'Ошибка генерации отчета: {str(e)}', 'error')
        return redirect(url_for('seo.dashboard'))

@bp.route('/score')
@login_required
def seo_score():
    """Общий SEO рейтинг сайта"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        score = seo_analytics.get_seo_score()
        return jsonify({
            'seo_score': score,
            'grade': 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D' if score >= 60 else 'F',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/health')
def api_health():
    """API проверки здоровья SEO системы"""
    try:
        analytics = advanced_seo_optimizer.get_seo_analytics()
        seo_score = seo_analytics.get_seo_score()
        
        return jsonify({
            'status': 'healthy',
            'seo_health_percentage': analytics['seo_health_percentage'],
            'total_posts': analytics['total_posts'],
            'active_tests': analytics['active_tests'],
            'overall_seo_score': seo_score,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500