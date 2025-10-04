"""
API endpoints для аутентификации
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from marshmallow import ValidationError

from models import User
from schemas.user import UserSchema, LoginSchema, RegisterSchema
from config.database import db

bp = Blueprint('auth', __name__)

user_schema = UserSchema()
login_schema = LoginSchema()
register_schema = RegisterSchema()

@bp.route('/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    try:
        data = register_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Проверяем, существует ли пользователь
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Пользователь с таким именем уже существует'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 409
    
    # Создаем пользователя
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Создаем токены
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'user': user_schema.dump(user),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    """Вход пользователя"""
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Находим пользователя
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Аккаунт деактивирован'}), 403
    
    # Создаем токены
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # Обновляем последний вход
    user.update_last_seen()
    db.session.commit()
    
    return jsonify({
        'user': user_schema.dump(user),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Обновление access токена"""
    current_user_id = get_jwt_identity()
    
    # Создаем новый access токен
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({'access_token': access_token}), 200

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Выход пользователя"""
    # В реальном приложении здесь можно добавить токен в черный список
    return jsonify({'message': 'Успешный выход'}), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Получить текущего пользователя"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify({'user': user_schema.dump(user)}), 200

@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Обновить профиль текущего пользователя"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    data = request.json
    
    # Обновляем разрешенные поля
    allowed_fields = ['first_name', 'last_name', 'bio', 'website', 'location']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    # Проверяем email, если он изменился
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email уже используется'}), 409
        user.email = data['email']
    
    db.session.commit()
    
    return jsonify({'user': user_schema.dump(user)}), 200

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Изменить пароль"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    data = request.json
    
    # Проверяем старый пароль
    if not user.check_password(data.get('old_password')):
        return jsonify({'error': 'Неверный текущий пароль'}), 400
    
    # Устанавливаем новый пароль
    user.set_password(data.get('new_password'))
    db.session.commit()
    
    return jsonify({'message': 'Пароль успешно изменен'}), 200

@bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """Проверить валидность токена"""
    return jsonify({'valid': True}), 200