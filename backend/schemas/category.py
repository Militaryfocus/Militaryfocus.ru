"""
Схемы для сериализации/десериализации категорий
"""
from marshmallow import Schema, fields, validate

class CategorySchema(Schema):
    """Схема категории"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    slug = fields.Str(dump_only=True)
    description = fields.Str(allow_none=True)
    color = fields.Str()
    icon = fields.Str(allow_none=True)
    parent_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True, format='iso')

class CategoryCreateSchema(Schema):
    """Схема для создания категории"""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    description = fields.Str(validate=validate.Length(max=200))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    icon = fields.Str(validate=validate.Length(max=50))
    parent_id = fields.Int()

class CategoryUpdateSchema(Schema):
    """Схема для обновления категории"""
    name = fields.Str(validate=validate.Length(min=2, max=50))
    description = fields.Str(validate=validate.Length(max=200))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    icon = fields.Str(validate=validate.Length(max=50))
    parent_id = fields.Int()