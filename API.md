# 🔌 API Документация

## 📋 Обзор

REST API предоставляет программный доступ к функциям блога. Все endpoints возвращают JSON.

## 🔐 Аутентификация

### Получение токена
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1,
  "username": "user"
}
```

### Использование токена
```http
GET /api/posts
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 📚 Endpoints

### Посты

#### Получить все посты
```http
GET /api/posts?page=1&per_page=10
```

**Параметры:**
- `page` (int) - номер страницы (по умолчанию: 1)
- `per_page` (int) - количество на странице (по умолчанию: 10)
- `category_id` (int) - фильтр по категории
- `tag` (string) - фильтр по тегу
- `search` (string) - поиск по заголовку и содержанию

**Ответ:**
```json
{
  "posts": [
    {
      "id": 1,
      "title": "Заголовок поста",
      "slug": "zagolovok-posta",
      "excerpt": "Краткое описание...",
      "author": {
        "id": 1,
        "username": "admin"
      },
      "category": {
        "id": 1,
        "name": "Технологии"
      },
      "tags": ["AI", "Python"],
      "views_count": 123,
      "comments_count": 5,
      "created_at": "2025-10-04T12:00:00Z",
      "published_at": "2025-10-04T12:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 10,
  "pages": 5
}
```

#### Получить один пост
```http
GET /api/posts/{id}
```

**Ответ:**
```json
{
  "id": 1,
  "title": "Заголовок поста",
  "slug": "zagolovok-posta",
  "content": "Полное содержание поста...",
  "content_html": "<p>HTML версия...</p>",
  "excerpt": "Краткое описание...",
  "featured_image": "/static/uploads/image.jpg",
  "author": {
    "id": 1,
    "username": "admin",
    "first_name": "Иван",
    "last_name": "Иванов"
  },
  "category": {
    "id": 1,
    "name": "Технологии",
    "slug": "technology"
  },
  "tags": [
    {"id": 1, "name": "AI"},
    {"id": 2, "name": "Python"}
  ],
  "meta_title": "SEO заголовок",
  "meta_description": "SEO описание",
  "views_count": 123,
  "likes_count": 45,
  "comments_count": 5,
  "is_published": true,
  "created_at": "2025-10-04T12:00:00Z",
  "updated_at": "2025-10-04T13:00:00Z",
  "published_at": "2025-10-04T12:00:00Z"
}
```

#### Создать пост
```http
POST /api/posts
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Новый пост",
  "content": "Содержание поста",
  "category_id": 1,
  "tags": ["AI", "ML"],
  "excerpt": "Краткое описание",
  "is_published": true
}
```

#### Обновить пост
```http
PUT /api/posts/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Обновленный заголовок",
  "content": "Обновленное содержание"
}
```

#### Удалить пост
```http
DELETE /api/posts/{id}
Authorization: Bearer {token}
```

### Категории

#### Получить все категории
```http
GET /api/categories
```

**Ответ:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Технологии",
      "slug": "technology",
      "description": "Статьи о технологиях",
      "color": "#007bff",
      "posts_count": 25,
      "parent_id": null
    }
  ]
}
```

#### Создать категорию
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

### Комментарии

#### Получить комментарии к посту
```http
GET /api/posts/{post_id}/comments
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
        "username": "user1"
      },
      "parent_id": null,
      "likes_count": 3,
      "created_at": "2025-10-04T14:00:00Z",
      "replies": [
        {
          "id": 2,
          "content": "Согласен!",
          "author": {
            "id": 3,
            "username": "user2"
          },
          "parent_id": 1,
          "created_at": "2025-10-04T14:30:00Z"
        }
      ]
    }
  ]
}
```

#### Добавить комментарий
```http
POST /api/posts/{post_id}/comments
Authorization: Bearer {token}
Content-Type: application/json

{
  "content": "Мой комментарий",
  "parent_id": null
}
```

### Пользователи

#### Получить профиль
```http
GET /api/users/{id}
```

**Ответ:**
```json
{
  "id": 1,
  "username": "admin",
  "first_name": "Иван",
  "last_name": "Иванов",
  "bio": "Разработчик и блогер",
  "avatar": "/static/uploads/avatars/user1.jpg",
  "posts_count": 45,
  "comments_count": 123,
  "reputation_score": 500,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### Обновить профиль
```http
PUT /api/users/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Иван",
  "last_name": "Иванов",
  "bio": "Обновленная биография"
}
```

### Поиск

#### Поиск контента
```http
GET /api/search?q=искусственный+интеллект&type=posts
```

**Параметры:**
- `q` (string) - поисковый запрос
- `type` (string) - тип контента (posts, users, tags)
- `page` (int) - страница результатов

**Ответ:**
```json
{
  "results": [
    {
      "type": "post",
      "id": 1,
      "title": "Искусственный интеллект в 2025",
      "excerpt": "...",
      "url": "/blog/post/iskusstvennyj-intellekt-v-2025",
      "score": 0.95
    }
  ],
  "total": 15,
  "query": "искусственный интеллект"
}
```

### Статистика

#### Общая статистика
```http
GET /api/stats
```

**Ответ:**
```json
{
  "posts": {
    "total": 150,
    "published": 140,
    "drafts": 10
  },
  "users": {
    "total": 500,
    "active": 450,
    "new_this_month": 25
  },
  "comments": {
    "total": 1500,
    "today": 15,
    "pending_moderation": 3
  },
  "views": {
    "total": 50000,
    "today": 500,
    "average_per_post": 357
  }
}
```

#### Популярные посты
```http
GET /api/stats/popular?period=week&limit=10
```

**Параметры:**
- `period` (string) - период (day, week, month, all)
- `limit` (int) - количество постов

### AI Функции

#### Сгенерировать пост
```http
POST /api/ai/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "category": "технологии",
  "topic": "искусственный интеллект",
  "tone": "professional",
  "length": "medium"
}
```

**Ответ:**
```json
{
  "title": "Будущее искусственного интеллекта",
  "content": "Сгенерированный контент...",
  "tags": ["AI", "технологии", "будущее"],
  "meta_description": "SEO описание",
  "quality_score": 0.85
}
```

#### Анализ текста
```http
POST /api/ai/analyze
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Текст для анализа..."
}
```

**Ответ:**
```json
{
  "sentiment": "positive",
  "score": 0.75,
  "keywords": ["ключевое", "слово"],
  "entities": ["Компания", "Продукт"],
  "readability": {
    "score": 85,
    "level": "easy"
  }
}
```

#### SEO оптимизация
```http
POST /api/ai/optimize-seo
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Заголовок",
  "content": "Содержание для оптимизации",
  "keywords": ["ключевое", "слово"]
}
```

**Ответ:**
```json
{
  "optimized_title": "Оптимизированный заголовок | Ключевое слово",
  "meta_description": "SEO оптимизированное описание...",
  "suggestions": [
    "Добавьте больше внутренних ссылок",
    "Используйте ключевые слова в подзаголовках"
  ],
  "seo_score": 0.82
}
```

## 🔴 Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | OK - Успешно |
| 201 | Created - Ресурс создан |
| 400 | Bad Request - Неверный запрос |
| 401 | Unauthorized - Требуется аутентификация |
| 403 | Forbidden - Доступ запрещен |
| 404 | Not Found - Ресурс не найден |
| 422 | Unprocessable Entity - Ошибка валидации |
| 429 | Too Many Requests - Превышен лимит запросов |
| 500 | Internal Server Error - Ошибка сервера |

**Пример ошибки:**
```json
{
  "error": {
    "code": 422,
    "message": "Validation failed",
    "details": {
      "title": ["Это поле обязательно"],
      "content": ["Минимальная длина 100 символов"]
    }
  }
}
```

## 🚦 Rate Limiting

- **Анонимные пользователи:** 60 запросов в час
- **Аутентифицированные:** 300 запросов в час
- **AI endpoints:** 10 запросов в час

Информация о лимитах в заголовках:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1696425600
```

## 🔧 Примеры использования

### Python
```python
import requests

# Аутентификация
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access_token']

# Получение постов
headers = {'Authorization': f'Bearer {token}'}
posts = requests.get('http://localhost:5000/api/posts', headers=headers)
print(posts.json())
```

### JavaScript
```javascript
// Аутентификация
const login = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'admin',
    password: 'password'
  })
});
const {access_token} = await login.json();

// Получение постов
const posts = await fetch('/api/posts', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
console.log(await posts.json());
```

### cURL
```bash
# Аутентификация
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Получение постов
curl http://localhost:5000/api/posts \
  -H "Authorization: Bearer $TOKEN"
```

---

*API версия: 1.0*  
*Документация обновлена: 4 октября 2025*