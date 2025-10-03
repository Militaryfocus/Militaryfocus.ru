"""
Формы для блога
"""

from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from blog.models import User, Category
import re

class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(), 
        Length(min=3, max=80),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Имя пользователя может содержать только буквы, цифры и подчеркивания')
    ])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')

class RegisterForm(FlaskForm):
    """Форма регистрации"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(), 
        Length(min=3, max=80),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Имя пользователя может содержать только буквы, цифры и подчеркивания')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Имя', validators=[Length(max=50)])
    last_name = StringField('Фамилия', validators=[Length(max=50)])
    password = PasswordField('Пароль', validators=[
        DataRequired(), 
        Length(min=8, max=128),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', message='Пароль должен содержать минимум одну строчную букву, одну заглавную букву и одну цифру')
    ])
    password2 = PasswordField('Повторите пароль', 
                             validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Выберите другое.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Используйте другой.')

class ProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    first_name = StringField('Имя', validators=[Length(max=50)])
    last_name = StringField('Фамилия', validators=[Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('О себе', validators=[Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        self.original_email = kwargs.pop('original_email', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
    
    def validate_email(self, email):
        if self.original_email and email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Этот email уже используется.')

class PostForm(FlaskForm):
    """Форма создания/редактирования поста"""
    title = StringField('Заголовок', validators=[
        DataRequired(), 
        Length(min=5, max=200),
        Regexp(r'^[^<>{}]+$', message='Заголовок содержит недопустимые символы')
    ])
    content = TextAreaField('Содержание', validators=[
        DataRequired(), 
        Length(min=50, max=50000),
        Regexp(r'^[^<>{}]+$', message='Содержание содержит недопустимые символы')
    ], render_kw={"rows": 15, "placeholder": "Используйте Markdown для форматирования"})
    excerpt = TextAreaField('Краткое описание', validators=[
        Length(max=500),
        Regexp(r'^[^<>{}]*$', message='Описание содержит недопустимые символы')
    ], render_kw={"rows": 3, "placeholder": "Краткое описание поста для превью"})
    category = SelectField('Категория', coerce=int)
    tags = StringField('Теги', validators=[
        Regexp(r'^[a-zA-Zа-яА-Я0-9\s,]+$', message='Теги могут содержать только буквы, цифры, пробелы и запятые')
    ], render_kw={"placeholder": "Введите теги через запятую"})
    is_published = BooleanField('Опубликовать')
    is_featured = BooleanField('Рекомендуемый пост')
    
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Кэшируем категории для избежания N+1 запросов
        from flask import current_app
        cache_key = 'categories_choices'
        choices = current_app.cache.get(cache_key) if hasattr(current_app, 'cache') else None
        
        if choices is None:
            choices = [(0, 'Без категории')] + [(c.id, c.name) for c in Category.query.all()]
            if hasattr(current_app, 'cache'):
                current_app.cache.set(cache_key, choices, timeout=300)  # 5 минут
        
        self.category.choices = choices

class CommentForm(FlaskForm):
    """Форма комментария"""
    content = TextAreaField('Комментарий', validators=[DataRequired(), Length(min=10, max=1000)],
                           render_kw={"rows": 4, "placeholder": "Напишите ваш комментарий..."})
    parent_id = HiddenField()

class CategoryForm(FlaskForm):
    """Форма категории"""
    name = StringField('Название', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание', validators=[Length(max=500)])
    color = StringField('Цвет', validators=[Length(max=7)], default='#007bff')

class ContactForm(FlaskForm):
    """Форма обратной связи"""
    name = StringField('Имя', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Тема', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Сообщение', validators=[DataRequired(), Length(min=10, max=1000)],
                           render_kw={"rows": 6})