# Military Focus Blog

Современная блог-платформа с разделенной архитектурой Frontend/Backend, военной тематикой и AI-интеграцией.

## 🚀 Технологический стек

### Backend
- **Flask** - Python веб-фреймворк
- **PostgreSQL** - основная база данных
- **Redis** - кеширование и rate limiting
- **JWT** - аутентификация
- **SQLAlchemy** - ORM
- **Marshmallow** - сериализация

### Frontend
- **Vue 3** - прогрессивный JavaScript фреймворк
- **Vite** - сборщик
- **Pinia** - state management
- **Vue Router** - маршрутизация
- **Tailwind CSS** - стилизация
- **Axios** - HTTP клиент

### DevOps
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - reverse proxy
- **Gunicorn** - WSGI сервер
- **GitHub Actions** - CI/CD

## 📁 Структура проекта

```
.
├── backend/                # Backend API
│   ├── api/               # API endpoints
│   ├── config/            # Конфигурация
│   ├── middleware/        # Middleware
│   ├── schemas/           # Marshmallow схемы
│   ├── models.py          # Модели БД
│   ├── app.py            # Точка входа
│   └── requirements.txt   # Python зависимости
│
├── frontend/              # Frontend SPA
│   ├── src/              # Исходный код
│   │   ├── components/   # Vue компоненты
│   │   ├── views/        # Страницы
│   │   ├── stores/       # Pinia stores
│   │   ├── services/     # API сервисы
│   │   └── utils/        # Утилиты
│   ├── package.json      # Node зависимости
│   └── vite.config.js    # Конфигурация Vite
│
├── nginx/                 # Nginx конфигурация
├── docker-compose.yml     # Docker Compose конфигурация
├── Makefile              # Команды для управления
└── README.md             # Этот файл
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Make (опционально, для удобства)
- Git

### Установка и запуск

1. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/Militaryfocus/Militaryfocus.ru.git
   cd Militaryfocus.ru
   ```

2. **Настройте окружение**
   ```bash
   cp .env.docker.example .env
   # Отредактируйте .env файл с вашими настройками
   ```

3. **Запустите с помощью Docker Compose**
   ```bash
   # С использованием Make
   make build
   make up
   make init-db

   # Или напрямую через docker-compose
   docker-compose build
   docker-compose up -d
   docker-compose exec backend flask db upgrade
   ```

4. **Откройте в браузере**
   - Frontend: http://localhost
   - Backend API: http://localhost/api/v1
   - API документация: http://localhost/api/v1/docs

## 📝 Основные команды

### Make команды

```bash
make help          # Показать все доступные команды
make up            # Запустить все сервисы
make down          # Остановить все сервисы
make logs          # Показать логи
make shell-backend # Открыть shell в backend контейнере
make migrate       # Выполнить миграции БД
make test          # Запустить тесты
```

### Разработка

**Backend разработка:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
```

**Frontend разработка:**
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Конфигурация

### Environment переменные

Основные переменные окружения (см. `.env.docker.example`):

- `DB_USER`, `DB_PASSWORD`, `DB_NAME` - настройки PostgreSQL
- `SECRET_KEY`, `JWT_SECRET_KEY` - ключи безопасности
- `REDIS_URL` - подключение к Redis
- `VITE_API_URL` - URL API для frontend

## 📚 API Документация

### Основные endpoints

- `POST /api/v1/auth/register` - регистрация
- `POST /api/v1/auth/login` - вход
- `GET /api/v1/posts` - список постов
- `GET /api/v1/posts/:slug` - получить пост
- `POST /api/v1/posts` - создать пост (требует авторизации)
- `GET /api/v1/categories` - список категорий
- `GET /api/v1/tags` - список тегов

## 🚀 Деплой

### Production с Docker

```bash
# Настройте production окружение
cp .env.docker.example .env.production
# Отредактируйте с production настройками

# Запустите в production режиме
docker-compose -f docker-compose.yml up -d
```

### Мониторинг

Для включения мониторинга (Prometheus + Grafana):

```bash
make monitoring-up
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## 🧪 Тестирование

```bash
# Backend тесты
make test-backend

# Frontend тесты
cd frontend && npm run test

# E2E тесты
cd frontend && npm run test:e2e
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Контакты

- Email: support@militaryfocus.ru
- Telegram: [@militaryfocus](https://t.me/militaryfocus)
- Website: [militaryfocus.ru](https://militaryfocus.ru)

---

Made with ❤️ by Military Focus Team