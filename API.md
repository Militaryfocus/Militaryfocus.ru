# 🔌 API Документация

Полная документация REST API для Military Focus Blog System.

## 🌐 Базовый URL

```
http://localhost:5000/api
```

## 🔐 Аутентификация

### Получение токена
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Использование токена
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 📝 Посты

### Получение списка постов
```http
GET /api/posts?page=1&per_page=10&category=tech&search=python
```

**Параметры:**
- `page` (int): Номер страницы (по умолчанию: 1)
- `per_page` (int): Постов на страницу (по умолчанию: 10)
- `category` (string): Фильтр по категории
- `search` (string): Поиск по тексту
- `published` (bool): Только опубликованные (по умолчанию: true)

**Ответ:**
```json
{
  "posts": [
    {
      "id": 1,
      "title": "Введение в Python",
      "slug": "vvedenie-v-python",
      "excerpt": "Краткое описание поста...",
      "content": "Полное содержимое поста...",
      "author": {
        "id": 1,
        "username": "admin",
        "full_name": "Admin User"
      },
      "category": {
        "id": 1,
        "name": "Программирование",
        "slug": "programming"
      },
      "tags": [
        {"name": "Python", "slug": "python"},
        {"name": "Tutorial", "slug": "tutorial"}
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "published_at": "2024-01-15T10:30:00Z",
      "views_count": 150,
      "comments_count": 5,
      "likes_count": 12,
      "reading_time": 5,
      "url": "/post/vvedenie-v-python"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Получение конкретного поста
```http
GET /api/posts/{id}
```

**Ответ:**
```json
{
  "id": 1,
  "title": "Введение в Python",
  "slug": "vvedenie-v-python",
  "content": "Полное содержимое поста...",
  "excerpt": "Краткое описание...",
  "author": {
    "id": 1,
    "username": "admin",
    "full_name": "Admin User",
    "avatar": "/static/avatars/admin.jpg"
  },
  "category": {
    "id": 1,
    "name": "Программирование",
    "slug": "programming",
    "color": "#3776ab"
  },
  "tags": [
    {"name": "Python", "slug": "python"},
    {"name": "Tutorial", "slug": "tutorial"}
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "published_at": "2024-01-15T10:30:00Z",
  "views_count": 150,
  "comments_count": 5,
  "likes_count": 12,
  "reading_time": 5,
  "is_featured": true,
  "meta_title": "Введение в Python - Military Focus",
  "meta_description": "Подробное руководство по изучению Python...",
  "url": "/post/vvedenie-v-python"
}
```

### Создание поста
```http
POST /api/posts
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Новый пост",
  "content": "Содержимое поста...",
  "excerpt": "Краткое описание",
  "category_id": 1,
  "tags": ["Python", "Tutorial"],
  "is_published": true,
  "is_featured": false
}
```

**Ответ:**
```json
{
  "id": 26,
  "title": "Новый пост",
  "slug": "novyy-post",
  "url": "/post/novyy-post",
  "created_at": "2024-01-15T12:00:00Z"
}
```

### Обновление поста
```http
PUT /api/posts/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Обновленный заголовок",
  "content": "Обновленное содержимое...",
  "is_published": true
}
```

### Удаление поста
```http
DELETE /api/posts/{id}
Authorization: Bearer {token}
```

## 👥 Пользователи

### Получение профиля пользователя
```http
GET /api/users/{id}
```

**Ответ:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "full_name": "Admin User",
  "bio": "Администратор системы",
  "avatar": "/static/avatars/admin.jpg",
  "website": "https://example.com",
  "location": "Москва",
  "is_admin": true,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_seen": "2024-01-15T12:00:00Z",
  "posts_count": 15,
  "comments_count": 45,
  "reputation_score": 100
}
```

### Получение постов пользователя
```http
GET /api/users/{id}/posts?page=1&per_page=10
```

### Обновление профиля
```http
PUT /api/users/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Новое имя",
  "last_name": "Новая фамилия",
  "bio": "Обновленная биография",
  "website": "https://newsite.com"
}
```

## 📂 Категории

### Получение списка категорий
```http
GET /api/categories
```

**Ответ:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Программирование",
      "slug": "programming",
      "description": "Статьи о программировании",
      "color": "#3776ab",
      "posts_count": 15,
      "url": "/category/programming"
    },
    {
      "id": 2,
      "name": "ИИ и ML",
      "slug": "ai-ml",
      "description": "Искусственный интеллект и машинное обучение",
      "color": "#ff6b6b",
      "posts_count": 8,
      "url": "/category/ai-ml"
    }
  ]
}
```

### Получение постов категории
```http
GET /api/categories/{id}/posts?page=1&per_page=10
```

### Создание категории
```http
POST /api/categories
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Новая категория",
  "description": "Описание категории",
  "color": "#28a745"
}
```

## 🏷️ Теги

### Получение популярных тегов
```http
GET /api/tags?limit=20
```

**Ответ:**
```json
{
  "tags": [
    {
      "name": "Python",
      "slug": "python",
      "posts_count": 25,
      "color": "#3776ab"
    },
    {
      "name": "Flask",
      "slug": "flask",
      "posts_count": 18,
      "color": "#000000"
    }
  ]
}
```

### Получение постов тега
```http
GET /api/tags/{slug}/posts?page=1&per_page=10
```

## 💬 Комментарии

### Получение комментариев поста
```http
GET /api/posts/{id}/comments?page=1&per_page=20
```

**Ответ:**
```json
{
  "comments": [
    {
      "id": 1,
      "content": "Отличная статья!",
      "author": {
        "id": 2,
        "username": "user1",
        "full_name": "User One"
      },
      "created_at": "2024-01-15T11:00:00Z",
      "is_approved": true,
      "parent_id": null,
      "replies": [
        {
          "id": 2,
          "content": "Спасибо за комментарий!",
          "author": {
            "id": 1,
            "username": "admin",
            "full_name": "Admin User"
          },
          "created_at": "2024-01-15T11:30:00Z",
          "is_approved": true,
          "parent_id": 1
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

### Создание комментария
```http
POST /api/posts/{id}/comments
Authorization: Bearer {token}
Content-Type: application/json

{
  "content": "Мой комментарий",
  "parent_id": null
}
```

### Одобрение комментария
```http
POST /api/comments/{id}/approve
Authorization: Bearer {token}
```

### Удаление комментария
```http
DELETE /api/comments/{id}
Authorization: Bearer {token}
```

## 🔍 Поиск

### Поиск с автодополнением
```http
GET /api/search/suggestions?q=python
```

**Ответ:**
```json
{
  "suggestions": [
    {
      "title": "Введение в Python",
      "description": "Подробное руководство по изучению Python...",
      "url": "/post/vvedenie-v-python",
      "icon": "fa-newspaper",
      "type": "post"
    },
    {
      "title": "Python",
      "description": "Популярный тег",
      "url": "/tag/python",
      "icon": "fa-tag",
      "type": "tag"
    }
  ]
}
```

### Поиск постов
```http
GET /api/search/posts?q=python&page=1&per_page=10
```

**Ответ:**
```json
{
  "posts": [
    {
      "id": 1,
      "title": "Введение в Python",
      "slug": "vvedenie-v-python",
      "excerpt": "Подробное руководство...",
      "author": "Admin User",
      "category": "Программирование",
      "created_at": "2024-01-15T10:30:00Z",
      "views_count": 150,
      "comments_count": 5,
      "url": "/post/vvedenie-v-python"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

## 🤖 ИИ API

### Генерация контента
```http
POST /api/ai/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "post",
  "topic": "Искусственный интеллект",
  "length": "medium",
  "style": "technical",
  "language": "ru",
  "provider": "openai"
}
```

**Ответ:**
```json
{
  "content": "Сгенерированный контент...",
  "title": "Сгенерированный заголовок",
  "excerpt": "Краткое описание...",
  "keywords": ["ИИ", "машинное обучение", "нейронные сети"],
  "reading_time": 8,
  "provider": "openai",
  "model": "gpt-4",
  "tokens_used": 1250
}
```

### Анализ текста
```http
POST /api/ai/analyze
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Текст для анализа...",
  "analysis_type": "sentiment"
}
```

**Ответ:**
```json
{
  "sentiment": {
    "score": 0.8,
    "label": "positive",
    "confidence": 0.95
  },
  "keywords": [
    {"word": "программирование", "score": 0.9},
    {"word": "python", "score": 0.8}
  ],
  "readability": {
    "score": 75,
    "level": "intermediate"
  },
  "language": "ru",
  "word_count": 250
}
```

### Оптимизация SEO
```http
POST /api/ai/seo-optimize
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Заголовок поста",
  "content": "Содержимое поста...",
  "target_keywords": ["python", "программирование"]
}
```

**Ответ:**
```json
{
  "optimized_title": "Оптимизированный заголовок",
  "meta_description": "Оптимизированное описание...",
  "suggestions": [
    "Добавьте больше ключевых слов в заголовок",
    "Увеличьте длину контента до 300+ слов"
  ],
  "seo_score": 85,
  "keyword_density": {
    "python": 2.5,
    "программирование": 1.8
  }
}
```

## 📊 Аналитика

### Получение статистики
```http
GET /api/analytics/stats
Authorization: Bearer {token}
```

**Ответ:**
```json
{
  "posts": {
    "total": 150,
    "published": 120,
    "drafts": 30,
    "this_month": 15
  },
  "users": {
    "total": 500,
    "active": 350,
    "new_this_month": 25
  },
  "comments": {
    "total": 1200,
    "approved": 1100,
    "pending": 100
  },
  "views": {
    "total": 50000,
    "this_month": 5000,
    "popular_posts": [
      {
        "id": 1,
        "title": "Введение в Python",
        "views": 1500
      }
    ]
  }
}
```

### Получение SEO метрик
```http
GET /api/analytics/seo
Authorization: Bearer {token}
```

**Ответ:**
```json
{
  "overall_score": 85,
  "posts_analyzed": 120,
  "average_score": 82,
  "issues": {
    "critical": 5,
    "warning": 15,
    "info": 30
  },
  "recommendations": [
    "Улучшите мета-описания для 10 постов",
    "Добавьте alt-теги для изображений"
  ]
}
```

## 🔧 Система

### Проверка здоровья системы
```http
GET /api/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "cache": "connected",
  "ai_services": {
    "openai": "available",
    "anthropic": "available",
    "google": "available"
  },
  "performance": {
    "response_time": 120,
    "memory_usage": 45.2,
    "cpu_usage": 12.5
  }
}
```

### Получение версии
```http
GET /api/version
```

**Ответ:**
```json
{
  "version": "1.0.0",
  "build": "2024-01-15",
  "python": "3.11.0",
  "flask": "2.3.3",
  "features": [
    "ai_content_generation",
    "seo_optimization",
    "advanced_security",
    "performance_monitoring"
  ]
}
```

## 📝 Коды ошибок

### HTTP статус коды
- `200` - Успешно
- `201` - Создано
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Не найдено
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

### Формат ошибок
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ошибка валидации данных",
    "details": {
      "field": "title",
      "message": "Заголовок обязателен"
    }
  }
}
```

## 🔒 Ограничения

### Rate Limiting
- **Анонимные пользователи**: 100 запросов/час
- **Авторизованные пользователи**: 1000 запросов/час
- **Администраторы**: Без ограничений

### Размеры данных
- **Максимальный размер поста**: 1MB
- **Максимальный размер комментария**: 10KB
- **Максимальный размер изображения**: 5MB

## 📚 Примеры использования

### JavaScript (Fetch API)
```javascript
// Получение постов
const response = await fetch('/api/posts?page=1&per_page=10');
const data = await response.json();
console.log(data.posts);

// Создание поста
const newPost = await fetch('/api/posts', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    title: 'Новый пост',
    content: 'Содержимое...',
    category_id: 1
  })
});
```

### Python (requests)
```python
import requests

# Получение постов
response = requests.get('http://localhost:5000/api/posts')
posts = response.json()['posts']

# Создание поста
headers = {'Authorization': f'Bearer {token}'}
data = {
    'title': 'Новый пост',
    'content': 'Содержимое...',
    'category_id': 1
}
response = requests.post('http://localhost:5000/api/posts', 
                        json=data, headers=headers)
```

### cURL
```bash
# Получение постов
curl -X GET "http://localhost:5000/api/posts?page=1&per_page=10"

# Создание поста
curl -X POST "http://localhost:5000/api/posts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Новый пост", "content": "Содержимое..."}'
```

---

**API готов к использованию!** 🚀

Для получения дополнительной информации см. [полное описание функций](BLOG_FUNCTIONS.md).