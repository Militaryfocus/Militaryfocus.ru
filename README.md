# 🚀 Military Focus Blog System

Современная система управления блогом с ИИ-поддержкой, SEO-оптимизацией и высокой производительностью.

## 📚 Документация

- [**Руководство по установке**](INSTALLATION.md) - пошаговая инструкция по установке
- [**API документация**](API.md) - REST API endpoints и примеры
- [**Руководство по модулям**](MODULES_ARCHITECTURE_GUIDE.md) - подробное описание всех модулей
- [**Карта взаимодействий**](MODULES_INTERACTION_MAP.md) - схемы и потоки данных
- [**Быстрый справочник**](MODULES_QUICK_REFERENCE.md) - шпаргалка для разработчиков

## ✨ Основные возможности

### 📝 Контент-менеджмент
- **Создание и редактирование постов** с поддержкой Markdown и HTML
- **Система категорий и тегов** с цветовой кодировкой
- **Многоуровневые комментарии** с модерацией
- **Черновики и публикация** с гибким управлением
- **Система закладок и лайков**

### 🤖 ИИ-система
- **Автоматическая генерация контента** (OpenAI, Anthropic, Google AI)
- **Анализ тональности** и извлечение ключевых слов
- **Персонализация контента** под стиль автора
- **Многоязычная поддержка** и переводы

### 📈 SEO-оптимизация
- **Автоматическая оптимизация** мета-тегов и структуры
- **SEO-аудит** и анализ ключевых слов
- **A/B тестирование** заголовков и описаний
- **Динамическая генерация sitemap.xml**

### 🔒 Безопасность
- **Многоуровневая защита** от SQL-инъекций, XSS, CSRF
- **Rate limiting** и блокировка подозрительных IP
- **Управление сессиями** и безопасная аутентификация
- **Мониторинг безопасности** в реальном времени

### ⚡ Производительность
- **Многоуровневое кэширование** (память, Redis, файлы)
- **Оптимизация базы данных** с индексами и пагинацией
- **Обработка изображений** с автоматической оптимизацией
- **Мониторинг метрик** производительности

## 🛠️ Технологический стек

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **База данных**: SQLite (по умолчанию), PostgreSQL, MySQL
- **ИИ**: OpenAI, Anthropic, Google AI, NLTK, Transformers
- **SEO**: Автоматическая оптимизация, аналитика
- **Безопасность**: Werkzeug, bcrypt
- **Кэширование**: Redis, Memcached
- **Мониторинг**: Prometheus

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/Militaryfocus/Militaryfocus.ru.git
cd Militaryfocus.ru
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Web-установщик
```bash
python install.py
```
Откройте http://localhost:5001 в браузере и следуйте инструкциям.

### 4. Ручная настройка (альтернатива)
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 5. Запуск приложения
```bash
python app.py
```

## 📁 Структура проекта

```
blog/
├── models/                     # Модели базы данных
│   ├── user.py                # Модель пользователя
│   ├── post.py                # Модель поста
│   ├── comment.py             # Модель комментария
│   ├── category.py            # Модель категории
│   ├── tag.py                 # Модель тега
│   └── ...                    # Другие модели
├── services/                   # Сервисный слой
│   ├── post_service.py        # Сервис постов
│   ├── user_service.py        # Сервис пользователей
│   ├── comment_service.py     # Сервис комментариев
│   └── ...                    # Другие сервисы
├── routes/                     # Маршруты приложения
│   ├── main.py                # Основные страницы
│   ├── auth.py                # Аутентификация
│   ├── blog.py                # Управление постами
│   ├── admin.py               # Админ-панель
│   ├── api.py                 # REST API
│   └── seo.py                 # SEO-функции
├── config/                     # Конфигурация
│   ├── app_config.py          # Настройки приложения
│   ├── blueprint_config.py    # Регистрация blueprints
│   └── context_processors.py  # Контекстные процессоры
├── ai/                         # ИИ-модули
│   └── __init__.py            # ИИ интеграции
├── utils/                      # Утилиты
│   ├── image_handler.py       # Обработка изображений
│   └── sitemap_generator.py   # Генератор sitemap
├── templates/                  # HTML шаблоны
├── static/                     # Статические файлы
│   ├── css/                   # Стили
│   ├── js/                    # JavaScript
│   ├── images/                # Изображения
│   └── uploads/               # Загружаемые файлы
└── database.py                # Инициализация БД
```

## 🔧 Конфигурация

### Основные настройки (.env)
```env
# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///instance/blog.db

# API Keys (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_AI_KEY=your-google-key

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

### Настройки ИИ (ai_config.json)
```json
{
  "providers": {
    "openai": {"model": "gpt-4", "temperature": 0.7},
    "anthropic": {"model": "claude-3", "temperature": 0.7},
    "google": {"model": "gemini-pro", "temperature": 0.7}
  },
  "content_generation": {
    "max_tokens": 2000,
    "auto_optimize": true,
    "language": "ru"
  }
}
```

## 📊 Мониторинг и аналитика

### Системные метрики
- Время ответа сервера
- Использование памяти и CPU
- Количество активных пользователей
- Статистика ошибок

### SEO-аналитика
- Позиции в поисковых системах
- Анализ ключевых слов
- CTR и конверсия
- Качество контента

### Пользовательская аналитика
- Поведение на сайте
- Популярные посты и категории
- Время чтения и вовлеченность
- География пользователей

## 🔐 Безопасность

### Защита от атак
- **SQL-инъекции**: Параметризованные запросы через SQLAlchemy
- **XSS**: Санитизация пользовательского ввода с bleach
- **CSRF**: Токены защиты через Flask-WTF
- **Rate limiting**: Ограничение частоты запросов

### Мониторинг безопасности
- Логирование подозрительной активности
- Автоматическая блокировка IP
- Анализ сессий пользователей
- Уведомления о нарушениях

## 🚀 Развертывание

### Локальная разработка
```bash
python app.py
```

### Продакшн с Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker
```bash
docker build -t blog-system .
docker run -p 8000:8000 blog-system
```

### Systemd service
```ini
[Unit]
Description=Military Focus Blog
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/blog
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📈 Производительность

### Оптимизация
- Кэширование запросов к БД
- Минификация CSS/JS
- Сжатие изображений
- CDN для статических файлов

### Масштабирование
- Горизонтальное масштабирование
- Репликация базы данных
- Распределенное кэширование
- Load balancing

## 🤝 API

### RESTful API
- `GET /api/posts` - Список постов
- `GET /api/posts/<id>` - Детали поста
- `GET /api/categories` - Список категорий
- `GET /api/search` - Поиск контента
- `POST /api/comments` - Создание комментария

### Подробная документация
См. [API документацию](API.md) для полного списка endpoints.

## 🐛 Устранение неполадок

### Частые проблемы

1. **Ошибки импорта**: 
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Проблемы с БД**:
   ```bash
   flask db upgrade
   ```

3. **Ошибки ИИ**: 
   - Проверьте API ключи в `.env`
   - Убедитесь, что есть доступ к API

4. **Проблемы производительности**:
   - Включите Redis кэширование
   - Настройте индексы БД

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/Militaryfocus/Militaryfocus.ru/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Militaryfocus/Militaryfocus.ru/discussions)

---

**Система готова к использованию!** 🎉

Для быстрого старта используйте [web-установщик](INSTALLATION.md#web-installer) или следуйте [руководству по установке](INSTALLATION.md).