"""
Схемы для сериализации/десериализации тегов
"""
from marshmallow import Schema, fields, validate

class TagSchema(Schema):
    """Схема тега"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    slug = fields.Str(dump_only=True)
    description = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True, format='iso')

class TagCreateSchema(Schema):
    """Схема для создания тега"""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=30))
    description = fields.Str(validate=validate.Length(max=100))

class TagUpdateSchema(Schema):
    """Схема для обновления тега"""
    name = fields.Str(validate=validate.Length(min=2, max=30))
    description = fields.Str(validate=validate.Length(max=100))