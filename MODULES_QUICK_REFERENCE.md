# 📚 БЫСТРЫЙ СПРАВОЧНИК ПО МОДУЛЯМ

## 🎯 Что где искать?

### Если нужно работать с...

**👤 ПОЛЬЗОВАТЕЛЯМИ:**
- Модель: `blog/models/user.py`
- Сервис: `blog/services/user_service.py`
- Формы: `blog/forms.py` (LoginForm, RegisterForm)
- Маршруты: `blog/routes/auth.py`
- Шаблоны: `blog/templates/auth/*`

**📝 ПОСТАМИ:**
- Модель: `blog/models/post.py`
- Сервис: `blog/services/post_service.py`
- Формы: `blog/forms.py` (PostForm)
- Маршруты: `blog/routes/blog.py`
- Шаблоны: `blog/templates/blog/*`

**💬 КОММЕНТАРИЯМИ:**
- Модель: `blog/models/comment.py`
- Сервис: `blog/services/comment_service.py`
- Формы: `blog/forms.py` (CommentForm)
- Маршруты: `blog/routes/blog.py` (внутри post_detail)
- Шаблоны: `blog/templates/blog/post_detail.html`

**🏷️ КАТЕГОРИЯМИ/ТЕГАМИ:**
- Модели: `blog/models/category.py`, `blog/models/tag.py`
- Маршруты: `blog/routes/blog.py` (category_posts)
- Админка: `blog/routes/admin.py`

**🤖 AI ФУНКЦИЯМИ:**
- Генерация: `blog/ai_content_perfect.py`
- Продвинутая: `blog/advanced_content_generator.py`
- Персонализация: `blog/content_personalization.py`
- Управление: `blog/routes/ai_admin.py`
- CLI: `ai_manager.py`

**🔍 SEO:**
- Основной: `blog/advanced_seo.py`
- Автоматизация: `blog/auto_seo_optimizer.py`
- Аналитика: `blog/seo_analytics.py`
- Перелинковка: `blog/smart_interlinking.py`
- Маршруты: `blog/routes/seo.py`

**🔐 БЕЗОПАСНОСТЬЮ:**
- Модуль: `blog/security_perfect.py`
- Декораторы: `@login_required`, `@admin_required`
- Формы: CSRF защита в `blog/forms.py`

**⚡ ПРОИЗВОДИТЕЛЬНОСТЬЮ:**
- Кеширование: `blog/performance_perfect.py`
- Мониторинг: `blog/monitoring.py`
- Оптимизация: `blog/perfect_system.py`

**🛠️ АДМИНИСТРИРОВАНИЕМ:**
- Основная панель: `blog/routes/admin.py`
- AI панель: `blog/routes/ai_admin.py`
- Системная: `blog/routes/system_admin.py`

**🔌 API:**
- REST endpoints: `blog/routes/api.py`
- Расширенный API: `blog/api_perfect.py`

---

## 🚀 Частые задачи

### "Как добавить новое поле в модель?"
1. Изменить модель в `blog/models/<model>.py`
2. Создать миграцию: `flask db migrate -m "описание"`
3. Применить: `flask db upgrade`

### "Как создать новый маршрут?"
1. Добавить функцию в нужный файл `blog/routes/*.py`
2. Декоратор: `@bp.route('/path')`
3. Создать шаблон в `blog/templates/`

### "Как добавить новый сервис?"
```python
# blog/services/new_service.py
from blog.services.base import BaseService
from blog.models import YourModel

class NewService(BaseService):
    model = YourModel
    
    def custom_method(self):
        # ваша логика
        pass

new_service = NewService()
```

### "Как использовать AI генерацию?"
```python
from blog.ai_content_perfect import PerfectAIContentGenerator

generator = PerfectAIContentGenerator()
post_data = generator.generate_human_like_post(
    category='технологии',
    topic='искусственный интеллект'
)
```

### "Как добавить SEO мета-теги?"
```python
from blog.advanced_seo import advanced_seo_optimizer

# Для поста
meta_tags = advanced_seo_optimizer.meta_generator.generate_post_meta(post)

# В шаблоне
{{ seo_meta.title }}
{{ seo_meta.description }}
```

---

## 📁 Структура директорий

```
blog/
├── models/          # Модели данных (User, Post, etc.)
├── services/        # Бизнес-логика (сервисы)
├── routes/          # HTTP маршруты (контроллеры)
├── templates/       # HTML шаблоны (Jinja2)
├── static/          # CSS, JS, изображения
├── config/          # Конфигурация приложения
├── ai/              # AI совместимость
└── *.py            # Специализированные модули
```

---

## 🔧 Переменные окружения (.env)

```bash
# Основные
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///blog.db
FLASK_ENV=development

# AI
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# SEO
SITE_URL=https://yourdomain.com
GOOGLE_ANALYTICS_ID=UA-...

# Безопасность
ADMIN_EMAIL=admin@example.com
ALLOWED_HOSTS=localhost,yourdomain.com
```

---

## 🐛 Отладка

### Логи
- Основной лог: `blog_system.log`
- Просмотр: `tail -f blog_system.log`
- Уровень: настраивается в `app.py`

### Частые ошибки
1. **ImportError** → проверить `blog/ai/__init__.py` для заглушек
2. **Template not found** → проверить путь в `render_template()`
3. **url_for error** → проверить имя blueprint (blog_admin, не admin)
4. **Database error** → проверить миграции `flask db upgrade`

### Полезные команды
```bash
# Создать БД
python app.py

# Запустить shell
flask shell

# AI команды
python ai_manager.py stats
python ai_manager.py generate 5
python ai_manager.py test

# Проверка импортов
python -c "from blog import create_app; print('OK')"
```

---

## 📊 Метрики производительности

- **Кеширование**: Redis на популярных страницах
- **Индексы БД**: на slug, is_published, created_at
- **Lazy loading**: для связей в моделях
- **Пагинация**: 10-20 элементов на страницу

---

## 🔗 Полезные ссылки в коде

- Точка входа: `app.py`
- Фабрика приложений: `blog/__init__.py`
- База данных: `blog/database.py`
- Конфигурация: `blog/config/app_config.py`
- Основные модели: `blog/models/__init__.py`
- Базовый сервис: `blog/services/base.py`
- Главная страница: `blog/routes/main.py`

---

*Справочник создан: 4 октября 2025*