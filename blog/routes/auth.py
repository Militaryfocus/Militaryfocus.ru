"""
Маршруты аутентификации
"""

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from blog.models import User
from blog.forms import LoginForm, RegisterForm, ProfileForm
from blog import db, limiter

# Настройка логирования безопасности
security_logger = logging.getLogger('security')

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute") if limiter else lambda f: f
def login():
    """Вход в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            # Логирование успешного входа
            security_logger.info(f"Successful login: {user.username} from {request.remote_addr}")
            
            flash(f'Добро пожаловать, {user.get_full_name()}!', 'success')
            return redirect(next_page)
        
        # Логирование неудачной попытки входа
        security_logger.warning(f"Failed login attempt: {form.username.data} from {request.remote_addr}")
        flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute") if limiter else lambda f: f
def register():
    """Регистрация"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Логирование регистрации
        security_logger.info(f"New user registered: {user.username} ({user.email}) from {request.remote_addr}")
        
        flash('Регистрация прошла успешно! Теперь вы можете войти в систему.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    username = current_user.username
    logout_user()
    
    # Логирование выхода
    security_logger.info(f"User logout: {username} from {request.remote_addr}")
    
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """Профиль пользователя"""
    return render_template('auth/profile.html', user=current_user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактирование профиля"""
    form = ProfileForm(obj=current_user, original_email=current_user.email)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Профиль обновлен успешно!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)