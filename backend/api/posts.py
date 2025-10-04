"""
API endpoints для работы с постами
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError
from sqlalchemy import or_

from models import Post, Category, Tag, User, Like, Bookmark, View
from schemas.post import PostSchema, PostListSchema, PostCreateSchema, PostUpdateSchema
from config.database import db
from middleware.rate_limit import limiter

bp = Blueprint('posts', __name__)

post_schema = PostSchema()
posts_schema = PostListSchema(many=True)
post_create_schema = PostCreateSchema()
post_update_schema = PostUpdateSchema()

@bp.route('', methods=['GET'])
def get_posts():
    """Получить список постов с пагинацией и фильтрацией"""
    # Параметры пагинации
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Параметры фильтрации
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    author_id = request.args.get('author_id', type=int)
    search = request.args.get('search', '')
    
    # Базовый запрос - только опубликованные посты
    query = Post.query.filter_by(is_published=True)
    
    # Применяем фильтры
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if author_id:
        query = query.filter_by(user_id=author_id)
    
    if tag_id:
        query = query.join(Post.tags).filter(Tag.id == tag_id)
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term),
                Post.excerpt.ilike(search_term)
            )
        )
    
    # Сортировка
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    if order == 'desc':
        query = query.order_by(getattr(Post, sort_by).desc())
    else:
        query = query.order_by(getattr(Post, sort_by))
    
    # Пагинация
    posts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Проверяем авторизацию для приватных данных
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
    except:
        current_user_id = None
    
    return jsonify({
        'posts': posts_schema.dump(posts.items),
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': posts.has_next,
        'has_prev': posts.has_prev
    }), 200

@bp.route('/<string:slug>', methods=['GET'])
def get_post(slug):
    """Получить пост по slug"""
    post = Post.query.filter_by(slug=slug, is_published=True).first()
    
    if not post:
        return jsonify({'error': 'Пост не найден'}), 404
    
    # Увеличиваем счетчик просмотров
    post.views += 1
    
    # Записываем просмотр
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        
        view = View(
            post_id=post.id,
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(view)
    except:
        current_user_id = None
    
    db.session.commit()
    
    # Добавляем информацию о взаимодействии пользователя
    post_data = post_schema.dump(post)
    
    if current_user_id:
        post_data['is_liked'] = Like.query.filter_by(
            user_id=current_user_id,
            item_type='post',
            item_id=post.id
        ).first() is not None
        
        post_data['is_bookmarked'] = Bookmark.query.filter_by(
            user_id=current_user_id,
            post_id=post.id
        ).first() is not None
    
    return jsonify({'post': post_data}), 200

@bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_post():
    """Создать новый пост"""
    current_user_id = get_jwt_identity()
    
    try:
        data = post_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Создаем пост
    post = Post(
        title=data['title'],
        content=data['content'],
        excerpt=data.get('excerpt'),
        user_id=current_user_id,
        category_id=data.get('category_id'),
        is_published=data.get('is_published', False),
        meta_title=data.get('meta_title'),
        meta_description=data.get('meta_description'),
        meta_keywords=data.get('meta_keywords')
    )
    
    # Добавляем теги
    if 'tags' in data:
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            post.tags.append(tag)
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'post': post_schema.dump(post)}), 201

@bp.route('/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    """Обновить пост"""
    current_user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': 'Пост не найден'}), 404
    
    # Проверяем права доступа
    if post.user_id != current_user_id and not User.query.get(current_user_id).is_admin:
        return jsonify({'error': 'Нет прав для редактирования'}), 403
    
    try:
        data = post_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Обновляем поля
    for field, value in data.items():
        if field == 'tags':
            # Обновляем теги
            post.tags.clear()
            for tag_name in value:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                post.tags.append(tag)
        else:
            setattr(post, field, value)
    
    post.updated_at = db.func.now()
    db.session.commit()
    
    return jsonify({'post': post_schema.dump(post)}), 200

@bp.route('/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """Удалить пост"""
    current_user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': 'Пост не найден'}), 404
    
    # Проверяем права доступа
    if post.user_id != current_user_id and not User.query.get(current_user_id).is_admin:
        return jsonify({'error': 'Нет прав для удаления'}), 403
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Пост успешно удален'}), 200

@bp.route('/<int:post_id>/like', methods=['POST'])
@jwt_required()
def toggle_like(post_id):
    """Поставить/убрать лайк"""
    current_user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post or not post.is_published:
        return jsonify({'error': 'Пост не найден'}), 404
    
    # Проверяем существующий лайк
    like = Like.query.filter_by(
        user_id=current_user_id,
        item_type='post',
        item_id=post_id
    ).first()
    
    if like:
        # Убираем лайк
        db.session.delete(like)
        liked = False
    else:
        # Добавляем лайк
        like = Like(
            user_id=current_user_id,
            item_type='post',
            item_id=post_id
        )
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    # Подсчитываем общее количество лайков
    likes_count = Like.query.filter_by(
        item_type='post',
        item_id=post_id
    ).count()
    
    return jsonify({
        'liked': liked,
        'likes_count': likes_count,
        'success': True
    }), 200

@bp.route('/<int:post_id>/bookmark', methods=['POST'])
@jwt_required()
def toggle_bookmark(post_id):
    """Добавить/удалить из закладок"""
    current_user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post or not post.is_published:
        return jsonify({'error': 'Пост не найден'}), 404
    
    # Проверяем существующую закладку
    bookmark = Bookmark.query.filter_by(
        user_id=current_user_id,
        post_id=post_id
    ).first()
    
    if bookmark:
        # Удаляем закладку
        db.session.delete(bookmark)
        bookmarked = False
    else:
        # Добавляем закладку
        bookmark = Bookmark(
            user_id=current_user_id,
            post_id=post_id
        )
        db.session.add(bookmark)
        bookmarked = True
    
    db.session.commit()
    
    return jsonify({
        'bookmarked': bookmarked,
        'success': True
    }), 200

@bp.route('/trending', methods=['GET'])
def get_trending_posts():
    """Получить популярные посты"""
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Получаем посты с наибольшим количеством просмотров за последние N дней
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=days)
    
    trending_posts = db.session.query(Post).join(View).filter(
        Post.is_published == True,
        View.created_at >= since_date
    ).group_by(Post.id).order_by(
        db.func.count(View.id).desc()
    ).limit(limit).all()
    
    return jsonify({
        'posts': posts_schema.dump(trending_posts),
        'period_days': days
    }), 200

@bp.route('/related/<int:post_id>', methods=['GET'])
def get_related_posts(post_id):
    """Получить похожие посты"""
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': 'Пост не найден'}), 404
    
    limit = request.args.get('limit', 5, type=int)
    
    # Находим посты с похожими тегами
    related_posts = Post.query.filter(
        Post.id != post_id,
        Post.is_published == True,
        Post.tags.any(Tag.id.in_([tag.id for tag in post.tags]))
    ).order_by(Post.created_at.desc()).limit(limit).all()
    
    # Если мало постов с похожими тегами, добавляем из той же категории
    if len(related_posts) < limit and post.category_id:
        category_posts = Post.query.filter(
            Post.id != post_id,
            Post.is_published == True,
            Post.category_id == post.category_id,
            ~Post.id.in_([p.id for p in related_posts])
        ).order_by(Post.created_at.desc()).limit(limit - len(related_posts)).all()
        
        related_posts.extend(category_posts)
    
    return jsonify({
        'posts': posts_schema.dump(related_posts)
    }), 200