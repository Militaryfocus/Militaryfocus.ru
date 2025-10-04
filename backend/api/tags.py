"""
API endpoints для работы с тегами
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from models import Tag, Post, User
from schemas.tag import TagSchema, TagCreateSchema, TagUpdateSchema
from config.database import db

bp = Blueprint('tags', __name__)

tag_schema = TagSchema()
tags_schema = TagSchema(many=True)
tag_create_schema = TagCreateSchema()
tag_update_schema = TagUpdateSchema()

@bp.route('', methods=['GET'])
def get_tags():
    """Получить список тегов"""
    # Параметры
    search = request.args.get('search', '')
    limit = request.args.get('limit', type=int)
    popular = request.args.get('popular', 'false').lower() == 'true'
    
    # Базовый запрос
    query = Tag.query
    
    # Поиск
    if search:
        query = query.filter(Tag.name.ilike(f'%{search}%'))
    
    # Популярные теги (по количеству постов)
    if popular:
        query = query.join(Tag.posts).filter(
            Post.is_published == True
        ).group_by(Tag.id).order_by(
            db.func.count(Post.id).desc()
        )
    else:
        query = query.order_by(Tag.name)
    
    # Лимит
    if limit:
        query = query.limit(limit)
    
    tags = query.all()
    
    # Добавляем количество постов
    tags_data = []
    for tag in tags:
        tag_dict = tag_schema.dump(tag)
        tag_dict['posts_count'] = tag.posts.filter_by(is_published=True).count()
        tags_data.append(tag_dict)
    
    return jsonify({'tags': tags_data}), 200

@bp.route('/<string:slug>', methods=['GET'])
def get_tag(slug):
    """Получить тег по slug"""
    tag = Tag.query.filter_by(slug=slug).first()
    
    if not tag:
        return jsonify({'error': 'Тег не найден'}), 404
    
    tag_data = tag_schema.dump(tag)
    tag_data['posts_count'] = tag.posts.filter_by(is_published=True).count()
    
    return jsonify({'tag': tag_data}), 200

@bp.route('', methods=['POST'])
@jwt_required()
def create_tag():
    """Создать тег"""
    try:
        data = tag_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Проверяем уникальность
    if Tag.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Тег с таким именем уже существует'}), 400
    
    tag = Tag(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({'tag': tag_schema.dump(tag)}), 201

@bp.route('/<int:tag_id>', methods=['PUT'])
@jwt_required()
def update_tag(tag_id):
    """Обновить тег (только админ)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Тег не найден'}), 404
    
    try:
        data = tag_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Проверяем уникальность имени
    if 'name' in data and data['name'] != tag.name:
        if Tag.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Тег с таким именем уже существует'}), 400
    
    # Обновляем поля
    for field, value in data.items():
        setattr(tag, field, value)
    
    db.session.commit()
    
    return jsonify({'tag': tag_schema.dump(tag)}), 200

@bp.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    """Удалить тег (только админ)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Тег не найден'}), 404
    
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({'message': 'Тег удален'}), 200

@bp.route('/<string:slug>/posts', methods=['GET'])
def get_tag_posts(slug):
    """Получить посты с тегом"""
    tag = Tag.query.filter_by(slug=slug).first()
    
    if not tag:
        return jsonify({'error': 'Тег не найден'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = tag.posts.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    from schemas.post import PostListSchema
    posts_schema = PostListSchema(many=True)
    
    return jsonify({
        'tag': tag_schema.dump(tag),
        'posts': posts_schema.dump(posts.items),
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@bp.route('/cloud', methods=['GET'])
def get_tag_cloud():
    """Получить облако тегов"""
    limit = request.args.get('limit', 50, type=int)
    
    # Получаем теги с количеством постов
    tags = db.session.query(
        Tag,
        db.func.count(Post.id).label('count')
    ).join(Tag.posts).filter(
        Post.is_published == True
    ).group_by(Tag.id).order_by(
        db.text('count DESC')
    ).limit(limit).all()
    
    # Находим мин и макс для расчета размера
    counts = [tag[1] for tag in tags]
    min_count = min(counts) if counts else 0
    max_count = max(counts) if counts else 0
    
    # Формируем облако
    cloud = []
    for tag, count in tags:
        tag_dict = tag_schema.dump(tag)
        tag_dict['count'] = count
        
        # Расчет относительного размера (1-5)
        if max_count > min_count:
            size = 1 + int(4 * (count - min_count) / (max_count - min_count))
        else:
            size = 3
        
        tag_dict['size'] = size
        cloud.append(tag_dict)
    
    return jsonify({'tags': cloud}), 200

@bp.route('/autocomplete', methods=['GET'])
def autocomplete_tags():
    """Автодополнение тегов"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify({'tags': []}), 200
    
    tags = Tag.query.filter(
        Tag.name.ilike(f'{query}%')
    ).order_by(Tag.name).limit(limit).all()
    
    return jsonify({
        'tags': [{'id': tag.id, 'name': tag.name} for tag in tags]
    }), 200