// Основной JavaScript для блога

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех компонентов
    initSmoothScrolling();
    initSearchEnhancements();
    initFormValidation();
    initImageLazyLoading();
    initTooltips();
    initReadingProgress();
    initThemeToggle();
    initCommentSystem();
});

// Плавная прокрутка для якорных ссылок
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Улучшения для поиска
function initSearchEnhancements() {
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        // Автофокус на поиск при нажатии Ctrl+K
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });

        // Подсветка результатов поиска
        const searchQuery = searchInput.value.trim();
        if (searchQuery && window.location.pathname.includes('/search')) {
            highlightSearchResults(searchQuery);
        }
    }
}

// Подсветка результатов поиска
function highlightSearchResults(query) {
    const regex = new RegExp(`(${query})`, 'gi');
    const elements = document.querySelectorAll('.card-title, .card-text');
    
    elements.forEach(element => {
        if (element.textContent.toLowerCase().includes(query.toLowerCase())) {
            element.innerHTML = element.innerHTML.replace(regex, '<mark>$1</mark>');
        }
    });
}

// Валидация форм в реальном времени
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');
    
    // Очистка предыдущих ошибок
    clearFieldError(field);
    
    if (required && !value) {
        showFieldError(field, 'Это поле обязательно для заполнения');
        return false;
    }
    
    if (type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Введите корректный email адрес');
        return false;
    }
    
    if (field.name === 'password' && value && value.length < 6) {
        showFieldError(field, 'Пароль должен содержать минимум 6 символов');
        return false;
    }
    
    return true;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Ленивая загрузка изображений
function initImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Инициализация тултипов
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Прогресс чтения статьи
function initReadingProgress() {
    if (document.querySelector('.post-content')) {
        const progressBar = createProgressBar();
        
        window.addEventListener('scroll', function() {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight - windowHeight;
            const scrollTop = window.pageYOffset;
            const progress = (scrollTop / documentHeight) * 100;
            
            progressBar.style.width = Math.min(progress, 100) + '%';
        });
    }
}

function createProgressBar() {
    const progressContainer = document.createElement('div');
    progressContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: rgba(0, 0, 0, 0.1);
        z-index: 9999;
    `;
    
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
        height: 100%;
        background: linear-gradient(90deg, #007bff, #0056b3);
        width: 0%;
        transition: width 0.1s ease;
    `;
    
    progressContainer.appendChild(progressBar);
    document.body.appendChild(progressContainer);
    
    return progressBar;
}

// Переключатель темы
function initThemeToggle() {
    const themeToggle = document.createElement('button');
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.className = 'btn btn-outline-light btn-sm position-fixed';
    themeToggle.style.cssText = `
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
    `;
    
    // Проверяем сохраненную тему
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        
        themeToggle.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
    
    document.body.appendChild(themeToggle);
}

// Система комментариев
function initCommentSystem() {
    // Автоматическое изменение размера textarea
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Предпросмотр комментария
    const commentForm = document.querySelector('form[action*="comment"]');
    if (commentForm) {
        const contentField = commentForm.querySelector('#content');
        if (contentField) {
            contentField.addEventListener('input', debounce(function() {
                // Здесь можно добавить предпросмотр Markdown
            }, 300));
        }
    }
}

// Утилита debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 100px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.5s ease;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Анимация появления элементов при скролле
function initScrollAnimations() {
    if ('IntersectionObserver' in window) {
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.card, .post-content > *').forEach(el => {
            el.classList.add('animate-on-scroll');
            animationObserver.observe(el);
        });
    }
}

// Поиск в реальном времени (для админ-панели)
function initLiveSearch() {
    const searchInputs = document.querySelectorAll('.live-search');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            const query = this.value.toLowerCase();
            const targetSelector = this.dataset.target;
            const items = document.querySelectorAll(targetSelector);
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? '' : 'none';
            });
        }, 300));
    });
}

// Копирование ссылки на пост
function copyPostLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        showNotification('Ссылка скопирована в буфер обмена!', 'success');
    });
}

// Экспорт функций для глобального использования
window.blogUtils = {
    showNotification,
    copyPostLink,
    validateField,
    debounce
};