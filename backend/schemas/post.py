"""
Схемы для сериализации/десериализации постов
"""
from marshmallow import Schema, fields, validate

class CategorySchema(Schema):
    """Схема категории"""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    slug = fields.Str()
    color = fields.Str()

class TagSchema(Schema):
    """Схема тега"""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    slug = fields.Str()

class AuthorSchema(Schema):
    """Схема автора (упрощенная)"""
    id = fields.Int(dump_only=True)
    username = fields.Str()
    avatar = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()

class PostSchema(Schema):
    """Полная схема поста"""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    slug = fields.Str(dump_only=True)
    content = fields.Str(required=True)
    excerpt = fields.Str(allow_none=True)
    image_url = fields.Str(allow_none=True)
    
    # Отношения
    author = fields.Nested(AuthorSchema, dump_only=True)
    category = fields.Nested(CategorySchema, dump_only=True)
    tags = fields.Nested(TagSchema, many=True, dump_only=True)
    
    # Метаданные
    views = fields.Int(dump_only=True)
    likes_count = fields.Method('get_likes_count', dump_only=True)
    comments_count = fields.Method('get_comments_count', dump_only=True)
    bookmarks_count = fields.Method('get_bookmarks_count', dump_only=True)
    
    # SEO
    meta_title = fields.Str(allow_none=True)
    meta_description = fields.Str(allow_none=True)
    meta_keywords = fields.Str(allow_none=True)
    
    # Статус
    is_published = fields.Bool()
    is_featured = fields.Bool(dump_only=True)
    
    # Даты
    created_at = fields.DateTime(dump_only=True, format='iso')
    updated_at = fields.DateTime(dump_only=True, format='iso')
    published_at = fields.DateTime(dump_only=True, format='iso')
    
    # Дополнительные поля
    reading_time = fields.Method('get_reading_time', dump_only=True)
    
    def get_likes_count(self, obj):
        from models import Like
        return Like.query.filter_by(item_type='post', item_id=obj.id).count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter_by(is_approved=True).count()
    
    def get_bookmarks_count(self, obj):
        return obj.bookmarks.count()
    
    def get_reading_time(self, obj):
        # Примерный расчет времени чтения (200 слов в минуту)
        word_count = len(obj.content.split())
        return max(1, word_count // 200)

class PostListSchema(Schema):
    """Схема для списка постов (упрощенная)"""
    id = fields.Int(dump_only=True)
    title = fields.Str()
    slug = fields.Str()
    excerpt = fields.Str()
    image_url = fields.Str()
    
    # Упрощенные отношения
    author = fields.Nested(AuthorSchema, only=['id', 'username', 'avatar'])
    category = fields.Nested(CategorySchema, only=['id', 'name', 'color'])
    tags = fields.Nested(TagSchema, many=True, only=['id', 'name'])
    
    # Основные метрики
    views = fields.Int()
    likes_count = fields.Method('get_likes_count')
    comments_count = fields.Method('get_comments_count')
    
    # Даты
    created_at = fields.DateTime(format='iso')
    
    # Дополнительно
    reading_time = fields.Method('get_reading_time')
    
    def get_likes_count(self, obj):
        from models import Like
        return Like.query.filter_by(item_type='post', item_id=obj.id).count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter_by(is_approved=True).count()
    
    def get_reading_time(self, obj):
        word_count = len(obj.content.split())
        return max(1, word_count // 200)

class PostCreateSchema(Schema):
    """Схема для создания поста"""
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    content = fields.Str(required=True, validate=validate.Length(min=10))
    excerpt = fields.Str(validate=validate.Length(max=500))
    category_id = fields.Int()
    tags = fields.List(fields.Str())
    is_published = fields.Bool(missing=False)
    image_url = fields.Str()
    meta_title = fields.Str(validate=validate.Length(max=60))
    meta_description = fields.Str(validate=validate.Length(max=160))
    meta_keywords = fields.Str(validate=validate.Length(max=200))

class PostUpdateSchema(Schema):
    """Схема для обновления поста"""
    title = fields.Str(validate=validate.Length(min=3, max=200))
    content = fields.Str(validate=validate.Length(min=10))
    excerpt = fields.Str(validate=validate.Length(max=500))
    category_id = fields.Int()
    tags = fields.List(fields.Str())
    is_published = fields.Bool()
    image_url = fields.Str()
    meta_title = fields.Str(validate=validate.Length(max=60))
    meta_description = fields.Str(validate=validate.Length(max=160))
    meta_keywords = fields.Str(validate=validate.Length(max=200))