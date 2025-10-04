"""
API endpoints для работы с категориями
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from models import Category, Post, User
from schemas.category import CategorySchema, CategoryCreateSchema, CategoryUpdateSchema
from config.database import db

bp = Blueprint('categories', __name__)

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
category_create_schema = CategoryCreateSchema()
category_update_schema = CategoryUpdateSchema()

@bp.route('', methods=['GET'])
def get_categories():
    """Получить список категорий"""
    # Параметры
    include_empty = request.args.get('include_empty', 'true').lower() == 'true'
    sort_by = request.args.get('sort_by', 'name')  # name, posts_count
    
    # Базовый запрос
    query = Category.query
    
    # Фильтр пустых категорий
    if not include_empty:
        query = query.join(Post).filter(Post.is_published == True).group_by(Category.id)
    
    # Сортировка
    if sort_by == 'posts_count':
        query = query.outerjoin(Post).group_by(Category.id).order_by(
            db.func.count(Post.id).desc()
        )
    else:
        query = query.order_by(Category.name)
    
    categories = query.all()
    
    # Добавляем количество постов
    categories_data = []
    for category in categories:
        cat_dict = category_schema.dump(category)
        cat_dict['posts_count'] = category.posts.filter_by(is_published=True).count()
        categories_data.append(cat_dict)
    
    return jsonify({'categories': categories_data}), 200

@bp.route('/<string:slug>', methods=['GET'])
def get_category(slug):
    """Получить категорию по slug"""
    category = Category.query.filter_by(slug=slug).first()
    
    if not category:
        return jsonify({'error': 'Категория не найдена'}), 404
    
    category_data = category_schema.dump(category)
    category_data['posts_count'] = category.posts.filter_by(is_published=True).count()
    
    return jsonify({'category': category_data}), 200

@bp.route('', methods=['POST'])
@jwt_required()
def create_category():
    """Создать категорию (только админ)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    try:
        data = category_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Проверяем уникальность имени
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Категория с таким именем уже существует'}), 400
    
    category = Category(
        name=data['name'],
        description=data.get('description'),
        color=data.get('color', '#3498db'),
        icon=data.get('icon'),
        parent_id=data.get('parent_id')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({'category': category_schema.dump(category)}), 201

@bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    """Обновить категорию (только админ)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Категория не найдена'}), 404
    
    try:
        data = category_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Проверяем уникальность имени
    if 'name' in data and data['name'] != category.name:
        if Category.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Категория с таким именем уже существует'}), 400
    
    # Обновляем поля
    for field, value in data.items():
        setattr(category, field, value)
    
    db.session.commit()
    
    return jsonify({'category': category_schema.dump(category)}), 200

@bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    """Удалить категорию (только админ)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Категория не найдена'}), 404
    
    # Проверяем наличие постов
    if category.posts.count() > 0:
        return jsonify({'error': 'Невозможно удалить категорию с постами'}), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Категория удалена'}), 200

@bp.route('/<string:slug>/posts', methods=['GET'])
def get_category_posts(slug):
    """Получить посты категории"""
    category = Category.query.filter_by(slug=slug).first()
    
    if not category:
        return jsonify({'error': 'Категория не найдена'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = category.posts.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    from schemas.post import PostListSchema
    posts_schema = PostListSchema(many=True)
    
    return jsonify({
        'category': category_schema.dump(category),
        'posts': posts_schema.dump(posts.items),
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@bp.route('/tree', methods=['GET'])
def get_category_tree():
    """Получить дерево категорий"""
    def build_tree(parent_id=None):
        categories = Category.query.filter_by(parent_id=parent_id).order_by(Category.name).all()
        tree = []
        
        for category in categories:
            cat_dict = category_schema.dump(category)
            cat_dict['posts_count'] = category.posts.filter_by(is_published=True).count()
            cat_dict['children'] = build_tree(category.id)
            tree.append(cat_dict)
        
        return tree
    
    tree = build_tree()
    return jsonify({'categories': tree}), 200