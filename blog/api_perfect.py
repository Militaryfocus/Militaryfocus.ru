"""
Идеальная система API и интеграций для блога
Включает REST API, GraphQL, WebSocket, webhooks и внешние интеграции
"""

import os
import json
import time
import asyncio
import aiohttp
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
import hmac
import base64
from functools import wraps
from flask import request, jsonify, current_app, g
from flask_login import current_user, login_required
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, NotFound
import jwt
from marshmallow import Schema, fields, validate, ValidationError
import graphene
from graphene import ObjectType, String, Int, List, Field, Schema as GraphQLSchema
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
import redis
from celery import Celery
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

from blog.models import Post, User, Category, Comment, Tag, db
from blog import db as database

class APIVersion(Enum):
    """Версии API"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

class ContentType(Enum):
    """Типы контента"""
    JSON = "application/json"
    XML = "application/xml"
    HTML = "text/html"
    TEXT = "text/plain"

class WebhookEvent(Enum):
    """События webhook"""
    POST_CREATED = "post.created"
    POST_UPDATED = "post.updated"
    POST_DELETED = "post.deleted"
    COMMENT_CREATED = "comment.created"
    COMMENT_APPROVED = "comment.approved"
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"

@dataclass
class APIResponse:
    """Стандартный ответ API"""
    success: bool
    data: Any = None
    message: str = ""
    errors: List[str] = None
    meta: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'errors': self.errors or [],
            'meta': self.meta or {},
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class WebhookPayload:
    """Полезная нагрузка webhook"""
    event: WebhookEvent
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class APIAuthentication:
    """Система аутентификации API"""
    
    def __init__(self):
        self.secret_key = current_app.config.get('SECRET_KEY')
        self.jwt_secret = current_app.config.get('JWT_SECRET', self.secret_key)
        self.api_keys = {}  # В реальном приложении - из базы данных
        self.rate_limits = {}
        self.lock = threading.Lock()
    
    def generate_api_key(self, user_id: int, name: str) -> str:
        """Генерация API ключа"""
        key_data = f"{user_id}:{name}:{time.time()}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()
        
        with self.lock:
            self.api_keys[api_key] = {
                'user_id': user_id,
                'name': name,
                'created_at': datetime.utcnow(),
                'last_used': None,
                'requests_count': 0
            }
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Валидация API ключа"""
        with self.lock:
            if api_key in self.api_keys:
                key_info = self.api_keys[api_key]
                key_info['last_used'] = datetime.utcnow()
                key_info['requests_count'] += 1
                return key_info
        return None
    
    def generate_jwt_token(self, user_id: int, expires_in: int = 3600) -> str:
        """Генерация JWT токена"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Валидация JWT токена"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 3600) -> bool:
        """Проверка ограничения скорости"""
        current_time = time.time()
        window_start = current_time - window
        
        with self.lock:
            if identifier not in self.rate_limits:
                self.rate_limits[identifier] = []
            
            # Очистка старых записей
            self.rate_limits[identifier] = [
                timestamp for timestamp in self.rate_limits[identifier]
                if timestamp > window_start
            ]
            
            # Проверка лимита
            if len(self.rate_limits[identifier]) >= limit:
                return False
            
            # Добавление текущего запроса
            self.rate_limits[identifier].append(current_time)
            return True

class APISerializers:
    """Сериализаторы для API"""
    
    class UserSchema(Schema):
        """Схема пользователя"""
        id = fields.Int(dump_only=True)
        username = fields.Str(required=True, validate=validate.Length(min=3, max=20))
        email = fields.Email(required=True)
        first_name = fields.Str(validate=validate.Length(max=50))
        last_name = fields.Str(validate=validate.Length(max=50))
        bio = fields.Str(validate=validate.Length(max=500))
        is_admin = fields.Bool(dump_only=True)
        is_active = fields.Bool(dump_only=True)
        created_at = fields.DateTime(dump_only=True)
        last_seen = fields.DateTime(dump_only=True)
        posts_count = fields.Int(dump_only=True)
        reputation_score = fields.Int(dump_only=True)
    
    class PostSchema(Schema):
        """Схема поста"""
        id = fields.Int(dump_only=True)
        title = fields.Str(required=True, validate=validate.Length(min=5, max=200))
        slug = fields.Str(dump_only=True)
        content = fields.Str(required=True, validate=validate.Length(min=50))
        excerpt = fields.Str(validate=validate.Length(max=500))
        featured_image = fields.Str(validate=validate.Length(max=255))
        is_published = fields.Bool()
        is_featured = fields.Bool()
        views_count = fields.Int(dump_only=True)
        likes_count = fields.Int(dump_only=True)
        comments_count = fields.Int(dump_only=True)
        created_at = fields.DateTime(dump_only=True)
        updated_at = fields.DateTime(dump_only=True)
        published_at = fields.DateTime(dump_only=True)
        author_id = fields.Int(required=True)
        category_id = fields.Int()
        tags = fields.List(fields.Int())
    
    class CategorySchema(Schema):
        """Схема категории"""
        id = fields.Int(dump_only=True)
        name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
        slug = fields.Str(dump_only=True)
        description = fields.Str(validate=validate.Length(max=500))
        color = fields.Str(validate=validate.Length(max=7))
        icon = fields.Str(validate=validate.Length(max=50))
        is_active = fields.Bool()
        posts_count = fields.Int(dump_only=True)
        created_at = fields.DateTime(dump_only=True)
    
    class CommentSchema(Schema):
        """Схема комментария"""
        id = fields.Int(dump_only=True)
        content = fields.Str(required=True, validate=validate.Length(min=3, max=1000))
        is_approved = fields.Bool(dump_only=True)
        is_highlighted = fields.Bool(dump_only=True)
        likes_count = fields.Int(dump_only=True)
        replies_count = fields.Int(dump_only=True)
        created_at = fields.DateTime(dump_only=True)
        author_id = fields.Int(required=True)
        post_id = fields.Int(required=True)
        parent_id = fields.Int()
    
    class TagSchema(Schema):
        """Схема тега"""
        id = fields.Int(dump_only=True)
        name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
        slug = fields.Str(dump_only=True)
        description = fields.Str(validate=validate.Length(max=200))
        color = fields.Str(validate=validate.Length(max=7))
        posts_count = fields.Int(dump_only=True)
        created_at = fields.DateTime(dump_only=True)

class GraphQLSchema:
    """GraphQL схема"""
    
    class UserType(SQLAlchemyObjectType):
        """GraphQL тип пользователя"""
        class Meta:
            model = User
            interfaces = (graphene.relay.Node,)
    
    class PostType(SQLAlchemyObjectType):
        """GraphQL тип поста"""
        class Meta:
            model = Post
            interfaces = (graphene.relay.Node,)
    
    class CategoryType(SQLAlchemyObjectType):
        """GraphQL тип категории"""
        class Meta:
            model = Category
            interfaces = (graphene.relay.Node,)
    
    class CommentType(SQLAlchemyObjectType):
        """GraphQL тип комментария"""
        class Meta:
            model = Comment
            interfaces = (graphene.relay.Node,)
    
    class TagType(SQLAlchemyObjectType):
        """GraphQL тип тега"""
        class Meta:
            model = Tag
            interfaces = (graphene.relay.Node,)
    
    class Query(ObjectType):
        """GraphQL запросы"""
        node = graphene.relay.Node.Field()
        
        # Пользователи
        users = SQLAlchemyConnectionField(UserType)
        user = Field(UserType, id=graphene.Int())
        
        # Посты
        posts = SQLAlchemyConnectionField(PostType)
        post = Field(PostType, id=graphene.Int(), slug=graphene.String())
        posts_by_category = SQLAlchemyConnectionField(PostType, category_id=graphene.Int())
        posts_by_author = SQLAlchemyConnectionField(PostType, author_id=graphene.Int())
        
        # Категории
        categories = SQLAlchemyConnectionField(CategoryType)
        category = Field(CategoryType, id=graphene.Int(), slug=graphene.String())
        
        # Комментарии
        comments = SQLAlchemyConnectionField(CommentType)
        comments_by_post = SQLAlchemyConnectionField(CommentType, post_id=graphene.Int())
        
        # Теги
        tags = SQLAlchemyConnectionField(TagType)
        tag = Field(TagType, id=graphene.Int(), slug=graphene.String())
        
        def resolve_user(self, info, id=None):
            """Разрешение пользователя"""
            if id:
                return User.query.get(id)
            return None
        
        def resolve_post(self, info, id=None, slug=None):
            """Разрешение поста"""
            if id:
                return Post.query.get(id)
            elif slug:
                return Post.query.filter_by(slug=slug).first()
            return None
        
        def resolve_category(self, info, id=None, slug=None):
            """Разрешение категории"""
            if id:
                return Category.query.get(id)
            elif slug:
                return Category.query.filter_by(slug=slug).first()
            return None
        
        def resolve_tag(self, info, id=None, slug=None):
            """Разрешение тега"""
            if id:
                return Tag.query.get(id)
            elif slug:
                return Tag.query.filter_by(slug=slug).first()
            return None
    
    class CreatePost(graphene.Mutation):
        """Мутация создания поста"""
        class Arguments:
            title = graphene.String(required=True)
            content = graphene.String(required=True)
            excerpt = graphene.String()
            category_id = graphene.Int()
            tags = graphene.List(graphene.Int())
        
        post = Field(PostType)
        success = graphene.Boolean()
        message = graphene.String()
        
        def mutate(self, info, title, content, excerpt=None, category_id=None, tags=None):
            """Выполнение мутации"""
            try:
                post = Post(
                    title=title,
                    content=content,
                    excerpt=excerpt,
                    author_id=current_user.id,
                    category_id=category_id
                )
                
                if tags:
                    post.tags = Tag.query.filter(Tag.id.in_(tags)).all()
                
                database.session.add(post)
                database.session.commit()
                
                return CreatePost(post=post, success=True, message="Post created successfully")
                
            except Exception as e:
                return CreatePost(success=False, message=str(e))
    
    class CreateComment(graphene.Mutation):
        """Мутация создания комментария"""
        class Arguments:
            content = graphene.String(required=True)
            post_id = graphene.Int(required=True)
            parent_id = graphene.Int()
        
        comment = Field(CommentType)
        success = graphene.Boolean()
        message = graphene.String()
        
        def mutate(self, info, content, post_id, parent_id=None):
            """Выполнение мутации"""
            try:
                comment = Comment(
                    content=content,
                    author_id=current_user.id,
                    post_id=post_id,
                    parent_id=parent_id
                )
                
                database.session.add(comment)
                database.session.commit()
                
                return CreateComment(comment=comment, success=True, message="Comment created successfully")
                
            except Exception as e:
                return CreateComment(success=False, message=str(e))
    
    class Mutation(ObjectType):
        """GraphQL мутации"""
        create_post = CreatePost.Field()
        create_comment = CreateComment.Field()
    
    schema = GraphQLSchema(query=Query, mutation=Mutation)

class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.connections = set()
        self.user_connections = defaultdict(set)
        self.rooms = defaultdict(set)
        self.lock = threading.Lock()
    
    async def register_connection(self, websocket, user_id: Optional[int] = None):
        """Регистрация WebSocket соединения"""
        with self.lock:
            self.connections.add(websocket)
            if user_id:
                self.user_connections[user_id].add(websocket)
    
    async def unregister_connection(self, websocket, user_id: Optional[int] = None):
        """Отмена регистрации WebSocket соединения"""
        with self.lock:
            self.connections.discard(websocket)
            if user_id:
                self.user_connections[user_id].discard(websocket)
    
    async def join_room(self, websocket, room: str):
        """Присоединение к комнате"""
        with self.lock:
            self.rooms[room].add(websocket)
    
    async def leave_room(self, websocket, room: str):
        """Покидание комнаты"""
        with self.lock:
            self.rooms[room].discard(websocket)
    
    async def broadcast(self, message: Dict[str, Any], room: Optional[str] = None):
        """Широковещательная передача сообщения"""
        if room:
            connections = self.rooms[room]
        else:
            connections = self.connections
        
        if connections:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[ws.send(message_str) for ws in connections if ws.open],
                return_exceptions=True
            )
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """Отправка сообщения пользователю"""
        if user_id in self.user_connections:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[ws.send(message_str) for ws in self.user_connections[user_id] if ws.open],
                return_exceptions=True
            )

class WebhookManager:
    """Менеджер webhooks"""
    
    def __init__(self):
        self.webhooks = {}  # В реальном приложении - из базы данных
        self.secret_key = current_app.config.get('WEBHOOK_SECRET', 'webhook_secret')
        self.celery_app = Celery('webhooks')
    
    def register_webhook(self, url: str, events: List[WebhookEvent], user_id: int) -> str:
        """Регистрация webhook"""
        webhook_id = hashlib.sha256(f"{url}:{user_id}:{time.time()}".encode()).hexdigest()
        
        self.webhooks[webhook_id] = {
            'url': url,
            'events': [event.value for event in events],
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'is_active': True,
            'retry_count': 0,
            'last_success': None,
            'last_failure': None
        }
        
        return webhook_id
    
    def trigger_webhook(self, event: WebhookEvent, data: Dict[str, Any]):
        """Запуск webhook"""
        for webhook_id, webhook in self.webhooks.items():
            if webhook['is_active'] and event.value in webhook['events']:
                self._send_webhook.delay(webhook_id, event.value, data)
    
    def _send_webhook(self, webhook_id: str, event: str, data: Dict[str, Any]):
        """Отправка webhook (Celery задача)"""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return
        
        payload = {
            'event': event,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Генерация подписи
        signature = self._generate_signature(json.dumps(payload))
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': event
        }
        
        try:
            response = requests.post(
                webhook['url'],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                webhook['last_success'] = datetime.utcnow()
                webhook['retry_count'] = 0
            else:
                webhook['last_failure'] = datetime.utcnow()
                webhook['retry_count'] += 1
                
                if webhook['retry_count'] > 5:
                    webhook['is_active'] = False
                    
        except Exception as e:
            webhook['last_failure'] = datetime.utcnow()
            webhook['retry_count'] += 1
            
            if webhook['retry_count'] > 5:
                webhook['is_active'] = False
    
    def _generate_signature(self, payload: str) -> str:
        """Генерация подписи webhook"""
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

class ExternalIntegrations:
    """Внешние интеграции"""
    
    def __init__(self):
        self.integrations = {
            'social_media': self._social_media_integration,
            'email_service': self._email_service_integration,
            'analytics': self._analytics_integration,
            'search_engine': self._search_engine_integration
        }
    
    async def share_to_social_media(self, post: Post, platforms: List[str]):
        """Публикация в социальных сетях"""
        for platform in platforms:
            if platform in self.integrations['social_media']:
                await self.integrations['social_media'][platform](post)
    
    async def send_email_notification(self, to: str, subject: str, content: str):
        """Отправка email уведомления"""
        await self.integrations['email_service'](to, subject, content)
    
    async def track_analytics_event(self, event: str, data: Dict[str, Any]):
        """Отслеживание аналитики"""
        await self.integrations['analytics'](event, data)
    
    async def submit_to_search_engine(self, post: Post):
        """Отправка в поисковые системы"""
        await self.integrations['search_engine'](post)
    
    def _social_media_integration(self):
        """Интеграция с социальными сетями"""
        return {
            'twitter': self._share_to_twitter,
            'facebook': self._share_to_facebook,
            'linkedin': self._share_to_linkedin
        }
    
    async def _share_to_twitter(self, post: Post):
        """Публикация в Twitter"""
        # Реализация публикации в Twitter
        pass
    
    async def _share_to_facebook(self, post: Post):
        """Публикация в Facebook"""
        # Реализация публикации в Facebook
        pass
    
    async def _share_to_linkedin(self, post: Post):
        """Публикация в LinkedIn"""
        # Реализация публикации в LinkedIn
        pass
    
    async def _email_service_integration(self, to: str, subject: str, content: str):
        """Интеграция с email сервисом"""
        # Реализация отправки email
        pass
    
    async def _analytics_integration(self, event: str, data: Dict[str, Any]):
        """Интеграция с аналитикой"""
        # Реализация отслеживания аналитики
        pass
    
    async def _search_engine_integration(self, post: Post):
        """Интеграция с поисковыми системами"""
        # Реализация отправки в поисковые системы
        pass

class PerfectAPIManager:
    """Идеальный менеджер API и интеграций"""
    
    def __init__(self):
        self.auth = APIAuthentication()
        self.serializers = APISerializers()
        self.graphql_schema = GraphQLSchema.schema
        self.websocket_manager = WebSocketManager()
        self.webhook_manager = WebhookManager()
        self.external_integrations = ExternalIntegrations()
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def api_auth_required(self, f):
        """Декоратор для аутентификации API"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Проверка API ключа
            api_key = request.headers.get('X-API-Key')
            if api_key:
                key_info = self.auth.validate_api_key(api_key)
                if key_info:
                    g.current_user_id = key_info['user_id']
                    return f(*args, **kwargs)
            
            # Проверка JWT токена
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = self.auth.validate_jwt_token(token)
                if payload:
                    g.current_user_id = payload['user_id']
                    return f(*args, **kwargs)
            
            return jsonify(APIResponse(success=False, message="Authentication required").to_dict()), 401
        
        return decorated_function
    
    def rate_limit(self, limit: int = 100, window: int = 3600):
        """Декоратор для ограничения скорости"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                identifier = request.remote_addr
                if hasattr(g, 'current_user_id'):
                    identifier = f"user_{g.current_user_id}"
                
                if not self.auth.check_rate_limit(identifier, limit, window):
                    return jsonify(APIResponse(
                        success=False, 
                        message="Rate limit exceeded"
                    ).to_dict()), 429
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_request(self, schema_class):
        """Декоратор для валидации запроса"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    schema = schema_class()
                    data = request.get_json()
                    validated_data = schema.load(data)
                    g.validated_data = validated_data
                    return f(*args, **kwargs)
                except ValidationError as e:
                    return jsonify(APIResponse(
                        success=False,
                        message="Validation error",
                        errors=e.messages
                    ).to_dict()), 400
                except Exception as e:
                    return jsonify(APIResponse(
                        success=False,
                        message="Invalid request format"
                    ).to_dict()), 400
            
            return decorated_function
        return decorator
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Получение статистики API"""
        return {
            'api_keys_count': len(self.auth.api_keys),
            'active_connections': len(self.websocket_manager.connections),
            'webhooks_count': len(self.webhook_manager.webhooks),
            'rate_limits': len(self.auth.rate_limits),
            'graphql_schema': 'available',
            'websocket_support': 'available',
            'webhook_support': 'available'
        }
    
    def get_api_documentation(self) -> Dict[str, Any]:
        """Получение документации API"""
        return {
            'version': '1.0.0',
            'base_url': request.url_root + 'api/v1',
            'endpoints': {
                'posts': {
                    'GET': '/posts',
                    'POST': '/posts',
                    'GET': '/posts/{id}',
                    'PUT': '/posts/{id}',
                    'DELETE': '/posts/{id}'
                },
                'users': {
                    'GET': '/users',
                    'GET': '/users/{id}',
                    'PUT': '/users/{id}'
                },
                'categories': {
                    'GET': '/categories',
                    'POST': '/categories',
                    'GET': '/categories/{id}',
                    'PUT': '/categories/{id}',
                    'DELETE': '/categories/{id}'
                },
                'comments': {
                    'GET': '/comments',
                    'POST': '/comments',
                    'GET': '/comments/{id}',
                    'PUT': '/comments/{id}',
                    'DELETE': '/comments/{id}'
                },
                'tags': {
                    'GET': '/tags',
                    'POST': '/tags',
                    'GET': '/tags/{id}',
                    'PUT': '/tags/{id}',
                    'DELETE': '/tags/{id}'
                }
            },
            'authentication': {
                'api_key': 'X-API-Key header',
                'jwt_token': 'Authorization: Bearer <token>'
            },
            'rate_limits': {
                'default': '100 requests per hour',
                'authenticated': '1000 requests per hour'
            },
            'graphql_endpoint': '/graphql',
            'websocket_endpoint': '/ws',
            'webhook_support': True
        }

# Глобальный экземпляр идеального менеджера API
perfect_api_manager = PerfectAPIManager()