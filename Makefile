.PHONY: help build up down logs shell clean restart init-db migrate

# Цвета для вывода
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

help: ## Показать эту справку
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

build: ## Собрать все Docker образы
	@echo "$(GREEN)Сборка Docker образов...$(NC)"
	docker-compose build

up: ## Запустить все сервисы
	@echo "$(GREEN)Запуск сервисов...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Сервисы запущены!$(NC)"
	@echo "Frontend: http://localhost"
	@echo "Backend API: http://localhost/api/v1"
	@echo "Redis: localhost:6379"
	@echo "PostgreSQL: localhost:5432"

down: ## Остановить все сервисы
	@echo "$(YELLOW)Остановка сервисов...$(NC)"
	docker-compose down

logs: ## Показать логи всех сервисов
	docker-compose logs -f

logs-backend: ## Показать логи backend
	docker-compose logs -f backend

logs-frontend: ## Показать логи frontend
	docker-compose logs -f frontend

shell-backend: ## Открыть shell в backend контейнере
	docker-compose exec backend /bin/sh

shell-frontend: ## Открыть shell в frontend контейнере
	docker-compose exec frontend /bin/sh

shell-db: ## Открыть psql в базе данных
	docker-compose exec postgres psql -U bloguser blogdb

clean: ## Очистить все данные и volumes
	@echo "$(RED)Внимание! Это удалит все данные!$(NC)"
	@read -p "Вы уверены? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)Очистка завершена$(NC)"; \
	fi

restart: ## Перезапустить все сервисы
	@echo "$(YELLOW)Перезапуск сервисов...$(NC)"
	docker-compose restart

restart-backend: ## Перезапустить backend
	docker-compose restart backend

restart-frontend: ## Перезапустить frontend
	docker-compose restart frontend

init-db: ## Инициализировать базу данных
	@echo "$(GREEN)Инициализация базы данных...$(NC)"
	docker-compose exec backend flask db init
	docker-compose exec backend flask db migrate -m "Initial migration"
	docker-compose exec backend flask db upgrade

migrate: ## Выполнить миграции базы данных
	@echo "$(GREEN)Выполнение миграций...$(NC)"
	docker-compose exec backend flask db upgrade

create-migration: ## Создать новую миграцию
	@read -p "Введите описание миграции: " desc; \
	docker-compose exec backend flask db migrate -m "$$desc"

seed-db: ## Заполнить БД тестовыми данными
	@echo "$(GREEN)Заполнение БД тестовыми данными...$(NC)"
	docker-compose exec backend python create_sample_data.py

test-backend: ## Запустить тесты backend
	docker-compose exec backend pytest

lint-backend: ## Проверить код backend
	docker-compose exec backend flake8 .

format-backend: ## Форматировать код backend
	docker-compose exec backend black .

dev-frontend: ## Запустить frontend в режиме разработки
	cd frontend && npm run dev

build-frontend: ## Собрать production build frontend
	cd frontend && npm run build

monitoring-up: ## Запустить мониторинг (Prometheus + Grafana)
	@echo "$(GREEN)Запуск мониторинга...$(NC)"
	docker-compose --profile monitoring up -d
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001"

monitoring-down: ## Остановить мониторинг
	docker-compose --profile monitoring down

backup-db: ## Создать резервную копию БД
	@echo "$(GREEN)Создание резервной копии БД...$(NC)"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U bloguser blogdb > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Резервная копия создана в backups/$(NC)"

restore-db: ## Восстановить БД из резервной копии
	@echo "$(YELLOW)Доступные резервные копии:$(NC)"
	@ls -1 backups/*.sql 2>/dev/null || echo "Нет резервных копий"
	@read -p "Введите имя файла резервной копии: " file; \
	if [ -f "$$file" ]; then \
		cat $$file | docker-compose exec -T postgres psql -U bloguser blogdb; \
		echo "$(GREEN)БД восстановлена$(NC)"; \
	else \
		echo "$(RED)Файл не найден$(NC)"; \
	fi

status: ## Показать статус всех сервисов
	@echo "$(GREEN)Статус сервисов:$(NC)"
	@docker-compose ps