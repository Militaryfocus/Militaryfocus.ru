"""
API endpoints для работы с пользователями
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from models import User, Post, Comment
from schemas.user import UserSchema, UserUpdateSchema
from config.database import db

bp = Blueprint('users', __name__)

user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_update_schema = UserUpdateSchema()

@bp.route('', methods=['GET'])
def get_users():
    """Получить список пользователей"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    # Базовый запрос - только активные пользователи
    query = User.query.filter_by(is_active=True)
    
    # Поиск
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            )
        )
    
    # Сортировка по дате регистрации
    query = query.order_by(User.created_at.desc())
    
    # Пагинация
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': users_schema.dump(users.items),
        'total': users.total,
        'pages': users.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Получить пользователя по ID"""
    user = User.query.get(user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Добавляем статистику
    user_data = user_schema.dump(user)
    user_data['stats'] = {
        'posts_count': user.posts.filter_by(is_published=True).count(),
        'comments_count': user.comments.filter_by(is_approved=True).count(),
        'likes_given': user.likes.count()
    }
    
    return jsonify({'user': user_data}), 200

@bp.route('/<string:username>', methods=['GET'])
def get_user_by_username(username):
    """Получить пользователя по username"""
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Добавляем статистику
    user_data = user_schema.dump(user)
    user_data['stats'] = {
        'posts_count': user.posts.filter_by(is_published=True).count(),
        'comments_count': user.comments.filter_by(is_approved=True).count(),
        'likes_given': user.likes.count()
    }
    
    return jsonify({'user': user_data}), 200

@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Обновить профиль текущего пользователя"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    try:
        data = user_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Проверяем уникальность username
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Это имя пользователя уже занято'}), 400
    
    # Обновляем поля
    for field, value in data.items():
        if field == 'avatar' and value:
            # TODO: Валидация URL аватара
            pass
        setattr(user, field, value)
    
    db.session.commit()
    
    return jsonify({'user': user_schema.dump(user)}), 200

@bp.route('/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """Получить посты пользователя"""
    user = User.query.get(user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Для текущего пользователя показываем все посты, для остальных - только опубликованные
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        
        if current_user_id == user_id:
            query = user.posts
        else:
            query = user.posts.filter_by(is_published=True)
    except:
        query = user.posts.filter_by(is_published=True)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    from schemas.post import PostListSchema
    posts_schema = PostListSchema(many=True)
    
    return jsonify({
        'user': user_schema.dump(user),
        'posts': posts_schema.dump(posts.items),
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@bp.route('/<int:user_id>/follow', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    """Подписаться на пользователя"""
    current_user_id = get_jwt_identity()
    
    if current_user_id == user_id:
        return jsonify({'error': 'Нельзя подписаться на себя'}), 400
    
    user_to_follow = User.query.get(user_id)
    if not user_to_follow or not user_to_follow.is_active:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # TODO: Реализовать систему подписок
    # Нужно добавить таблицу followers
    
    return jsonify({'message': 'Функция в разработке'}), 501

@bp.route('/authors', methods=['GET'])
def get_popular_authors():
    """Получить популярных авторов"""
    limit = request.args.get('limit', 10, type=int)
    
    # Получаем авторов с наибольшим количеством опубликованных постов
    authors = db.session.query(
        User,
        db.func.count(Post.id).label('posts_count')
    ).join(Post).filter(
        User.is_active == True,
        Post.is_published == True
    ).group_by(User.id).order_by(
        db.text('posts_count DESC')
    ).limit(limit).all()
    
    result = []
    for user, posts_count in authors:
        user_data = user_schema.dump(user)
        user_data['posts_count'] = posts_count
        result.append(user_data)
    
    return jsonify({'authors': result}), 200

@bp.route('/search', methods=['GET'])
def search_users():
    """Поиск пользователей"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'users': []}), 200
    
    search_term = f'%{query}%'
    users = User.query.filter(
        User.is_active == True,
        db.or_(
            User.username.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
            User.bio.ilike(search_term)
        )
    ).limit(limit).all()
    
    return jsonify({'users': users_schema.dump(users)}), 200