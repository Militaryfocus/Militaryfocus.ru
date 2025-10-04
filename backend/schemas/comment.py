"""
Схемы для сериализации/десериализации комментариев
"""
from marshmallow import Schema, fields, validate

class CommentAuthorSchema(Schema):
    """Схема автора комментария"""
    id = fields.Int(dump_only=True)
    username = fields.Str()
    avatar = fields.Str()

class CommentSchema(Schema):
    """Схема комментария"""
    id = fields.Int(dump_only=True)
    content = fields.Str(required=True)
    
    # Отношения
    author = fields.Nested(CommentAuthorSchema, dump_only=True)
    post_id = fields.Int(dump_only=True)
    parent_id = fields.Int(allow_none=True)
    
    # Метаданные
    likes_count = fields.Method('get_likes_count', dump_only=True)
    is_edited = fields.Bool(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)
    is_approved = fields.Bool(dump_only=True)
    
    # Даты
    created_at = fields.DateTime(dump_only=True, format='iso')
    edited_at = fields.DateTime(dump_only=True, format='iso')
    
    # Вложенные комментарии (заполняется вручную в endpoint)
    replies = fields.List(fields.Nested(lambda: CommentSchema()), dump_only=True, load_default=[])
    
    def get_likes_count(self, obj):
        from models import Like
        return Like.query.filter_by(item_type='comment', item_id=obj.id).count()

class CommentCreateSchema(Schema):
    """Схема для создания комментария"""
    content = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    parent_id = fields.Int(allow_none=True)

class CommentUpdateSchema(Schema):
    """Схема для обновления комментария"""
    content = fields.Str(required=True, validate=validate.Length(min=1, max=1000))