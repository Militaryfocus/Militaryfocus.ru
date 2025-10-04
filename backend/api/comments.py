"""
API endpoints для работы с комментариями
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from models import Comment, Post, User, Like
from schemas.comment import CommentSchema, CommentCreateSchema, CommentUpdateSchema
from config.database import db
from middleware.rate_limit import limiter

bp = Blueprint('comments', __name__)

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)
comment_create_schema = CommentCreateSchema()
comment_update_schema = CommentUpdateSchema()

@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """Получить комментарии к посту"""
    post = Post.query.get(post_id)
    
    if not post or not post.is_published:
        return jsonify({'error': 'Пост не найден'}), 404
    
    # Параметры
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort = request.args.get('sort', 'newest')  # newest, oldest, popular
    
    # Базовый запрос - только одобренные комментарии верхнего уровня
    query = Comment.query.filter_by(
        post_id=post_id,
        is_approved=True,
        parent_id=None
    )
    
    # Сортировка
    if sort == 'oldest':
        query = query.order_by(Comment.created_at.asc())
    elif sort == 'popular':
        # Сортировка по количеству лайков
        query = query.outerjoin(Like, 
            (Like.item_type == 'comment') & (Like.item_id == Comment.id)
        ).group_by(Comment.id).order_by(
            db.func.count(Like.id).desc(),
            Comment.created_at.desc()
        )
    else:  # newest
        query = query.order_by(Comment.created_at.desc())
    
    # Пагинация
    comments_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Сериализация
    comments_data = []
    for comment in comments_paginated.items:
        comment_dict = comment_schema.dump(comment)
        # Добавляем вложенные комментарии
        comment_dict['replies'] = comments_schema.dump(
            comment.replies.filter_by(is_approved=True).order_by(Comment.created_at.asc()).all()
        )
        comments_data.append(comment_dict)
    
    return jsonify({
        'comments': comments_data,
        'total': comments_paginated.total,
        'pages': comments_paginated.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': comments_paginated.has_next,
        'has_prev': comments_paginated.has_prev
    }), 200

@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_comment(post_id):
    """Создать комментарий"""
    current_user_id = get_jwt_identity()
    
    post = Post.query.get(post_id)
    if not post or not post.is_published:
        return jsonify({'error': 'Пост не найден'}), 404
    
    try:
        data = comment_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Создаем комментарий
    comment = Comment(
        content=data['content'],
        post_id=post_id,
        user_id=current_user_id,
        parent_id=data.get('parent_id'),
        is_approved=True  # Можно добавить модерацию
    )
    
    # Проверяем parent_id
    if comment.parent_id:
        parent = Comment.query.get(comment.parent_id)
        if not parent or parent.post_id != post_id:
            return jsonify({'error': 'Неверный родительский комментарий'}), 400
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'comment': comment_schema.dump(comment)}), 201

@bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Обновить комментарий"""
    current_user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    # Проверяем права
    if comment.user_id != current_user_id:
        return jsonify({'error': 'Нет прав для редактирования'}), 403
    
    try:
        data = comment_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    comment.content = data['content']
    comment.is_edited = True
    comment.edited_at = db.func.now()
    
    db.session.commit()
    
    return jsonify({'comment': comment_schema.dump(comment)}), 200

@bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Удалить комментарий"""
    current_user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    # Проверяем права
    user = User.query.get(current_user_id)
    if comment.user_id != current_user_id and not user.is_admin:
        return jsonify({'error': 'Нет прав для удаления'}), 403
    
    # Если есть ответы, помечаем как удаленный
    if comment.replies.count() > 0:
        comment.content = '[Комментарий удален]'
        comment.is_deleted = True
    else:
        db.session.delete(comment)
    
    db.session.commit()
    
    return jsonify({'message': 'Комментарий удален'}), 200

@bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@jwt_required()
def toggle_comment_like(comment_id):
    """Поставить/убрать лайк комментарию"""
    current_user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)
    
    if not comment or not comment.is_approved:
        return jsonify({'error': 'Комментарий не найден'}), 404
    
    # Проверяем существующий лайк
    like = Like.query.filter_by(
        user_id=current_user_id,
        item_type='comment',
        item_id=comment_id
    ).first()
    
    if like:
        db.session.delete(like)
        liked = False
    else:
        like = Like(
            user_id=current_user_id,
            item_type='comment',
            item_id=comment_id
        )
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    likes_count = Like.query.filter_by(
        item_type='comment',
        item_id=comment_id
    ).count()
    
    return jsonify({
        'liked': liked,
        'likes_count': likes_count
    }), 200

@bp.route('/users/<int:user_id>/comments', methods=['GET'])
def get_user_comments(user_id):
    """Получить комментарии пользователя"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    comments = Comment.query.filter_by(
        user_id=user_id,
        is_approved=True
    ).order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'comments': comments_schema.dump(comments.items),
        'total': comments.total,
        'pages': comments.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@bp.route('/comments/recent', methods=['GET'])
def get_recent_comments():
    """Получить последние комментарии"""
    limit = request.args.get('limit', 10, type=int)
    
    comments = Comment.query.filter_by(
        is_approved=True
    ).order_by(Comment.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'comments': comments_schema.dump(comments)
    }), 200