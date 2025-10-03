# Быстрый старт: Улучшенная система ИИ

## 🚀 Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# Опционально: для улучшенной проверки фактов
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Инициализация системы

```bash
# Первоначальная настройка блога
python ai_manager.py setup --with-content --posts 5

# Проверка статуса системы
python ai_manager.py ai-status
```

## 🛡️ Безопасная генерация контента

### Базовое использование

```bash
# Генерация 3 постов с полной проверкой
python ai_manager.py generate 3 --safe
```

### Программное использование

```python
from blog.integrated_ai_system import generate_safe_content

# Генерация одного поста
result = generate_safe_content(category="технологии")

if result:
    print(f"Статус: {result.status.value}")
    print(f"Качество: {result.quality_score:.3f}")
    print(f"Безопасность: {result.safety_score:.3f}")
    print(f"Предвзятость: {result.bias_score:.3f}")
    print(f"Ошибок: {result.error_count}")
    
    if result.corrections_applied:
        print("Применены исправления:")
        for correction in result.corrections_applied:
            print(f"  - {correction}")
```

## 📊 Мониторинг системы

### Проверка статуса

```bash
# Общий статус ИИ системы
python ai_manager.py ai-status

# Подробный отчет мониторинга
python ai_manager.py ai-monitor
```

### Оптимизация

```bash
# Автоматическая оптимизация параметров
python ai_manager.py ai-optimize
```

## 🔧 Основные возможности

### ✅ Что система делает автоматически:

- **Проверяет факты** через внешние источники
- **Обнаруживает галлюцинации** и недостоверную информацию
- **Исправляет ошибки** орфографии, грамматики, логики
- **Устраняет предвзятость** гендерную, культурную, лингвистическую
- **Фильтрует контент** на токсичность и вредоносность
- **Оценивает качество** по множественным критериям
- **Модерирует контент** автоматически или направляет на проверку

### 📈 Метрики качества:

- **Оценка валидации**: 0.0-1.0 (выше = лучше)
- **Индекс предвзятости**: 0.0-1.0 (ниже = лучше)
- **Оценка безопасности**: 0.0-1.0 (выше = лучше)
- **Риск галлюцинаций**: 0.0-1.0 (ниже = лучше)
- **Количество ошибок**: целое число (меньше = лучше)

## 🎯 Статусы контента

| Статус | Описание | Действие |
|--------|----------|----------|
| `approved` | Одобрено | Готово к публикации |
| `needs_review` | Требует проверки | Ручная модерация |
| `needs_correction` | Требует исправлений | Автоматическая коррекция |
| `rejected` | Отклонено | Не публикуется |
| `published` | Опубликовано | В блоге |

## ⚙️ Настройка параметров

### Пороговые значения (по умолчанию):

```python
safety_config = {
    'min_quality_score': 0.7,        # Минимальное качество
    'max_bias_score': 0.3,           # Максимальная предвзятость
    'min_safety_score': 0.8,         # Минимальная безопасность
    'max_error_count': 5,            # Максимум ошибок
    'max_hallucination_risk': 0.4,   # Максимальный риск галлюцинаций
}
```

### Изменение настроек:

```python
from blog.integrated_ai_system import integrated_ai_system

# Обновление конфигурации
integrated_ai_system.content_generator.update_safety_config({
    'min_quality_score': 0.8,  # Повышаем требования к качеству
    'max_bias_score': 0.2       # Снижаем допустимую предвзятость
})
```

## 🔍 Диагностика проблем

### Низкий уровень одобрений

```bash
# Проверяем статистику
python ai_manager.py ai-status

# Если много отклонений, снижаем требования
python ai_manager.py ai-optimize
```

### Проблемы с качеством

```python
# Анализ конкретного контента
from blog.ai_validation import ai_content_validator
from blog.error_detection import error_detector
from blog.bias_mitigation import bias_detector

text = "Ваш текст для анализа"

# Детальная проверка
validation_report = ai_content_validator.validate_content(text)
errors = error_detector.detect_all_errors(text)
bias_report = bias_detector.get_bias_report(text)

print(f"Качество: {validation_report.confidence_score:.3f}")
print(f"Ошибок: {len(errors)}")
print(f"Предвзятость: {bias_report['bias_score']:.3f}")
```

## 📋 Частые команды

```bash
# Быстрая генерация с проверкой
python ai_manager.py generate 1 --safe

# Статус системы
python ai_manager.py ai-status

# Статистика блога
python ai_manager.py stats

# Мониторинг ИИ
python ai_manager.py ai-monitor

# Оптимизация
python ai_manager.py ai-optimize

# Очистка тестового контента
python ai_manager.py cleanup posts --force
```

## 🆘 Получение помощи

```bash
# Справка по командам
python ai_manager.py --help

# Справка по конкретной команде
python ai_manager.py generate --help
```

## 🔗 Интеграция с веб-интерфейсом

```python
# В ваших маршрутах Flask
from blog.integrated_ai_system import generate_safe_content

@app.route('/admin/generate-content')
def generate_content():
    result = generate_safe_content()
    
    if result and result.status.value == 'approved':
        # Сохраняем в базу данных
        # ... код сохранения ...
        flash('Контент успешно сгенерирован и одобрен!', 'success')
    else:
        flash('Контент требует проверки', 'warning')
    
    return redirect(url_for('admin.dashboard'))
```

## 🎉 Готово!

Система готова к использованию. Начните с генерации нескольких тестовых постов и изучите метрики качества. При необходимости настройте параметры под ваши требования.

Для подробной информации см. [полную документацию](AI_SYSTEM_DOCUMENTATION.md).