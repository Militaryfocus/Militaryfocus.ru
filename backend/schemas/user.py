"""
Схемы для сериализации/десериализации пользователей
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class UserSchema(Schema):
    """Схема пользователя для API"""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    bio = fields.Str(allow_none=True)
    avatar = fields.Str(dump_only=True)
    website = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    is_admin = fields.Bool(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format='iso')
    last_seen = fields.DateTime(dump_only=True, format='iso')
    posts_count = fields.Method('get_posts_count', dump_only=True)
    followers_count = fields.Method('get_followers_count', dump_only=True)
    following_count = fields.Method('get_following_count', dump_only=True)
    
    def get_posts_count(self, obj):
        return obj.posts.filter_by(is_published=True).count()
    
    def get_followers_count(self, obj):
        # TODO: Реализовать когда будет система подписок
        return 0
    
    def get_following_count(self, obj):
        # TODO: Реализовать когда будет система подписок
        return 0

class LoginSchema(Schema):
    """Схема для входа"""
    username = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

class RegisterSchema(Schema):
    """Схема для регистрации"""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    confirm_password = fields.Str(required=True)
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError('Пароли не совпадают', field_name='confirm_password')

class UserListSchema(Schema):
    """Схема для списка пользователей"""
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    avatar = fields.Str(dump_only=True)
    posts_count = fields.Method('get_posts_count', dump_only=True)
    
    def get_posts_count(self, obj):
        return obj.posts.filter_by(is_published=True).count()

class UserUpdateSchema(Schema):
    """Схема для обновления профиля пользователя"""
    username = fields.Str(validate=validate.Length(min=3, max=80))
    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    bio = fields.Str(validate=validate.Length(max=500))
    avatar = fields.Str(validate=validate.URL())
    website = fields.Str(validate=validate.URL())
    location = fields.Str(validate=validate.Length(max=100))