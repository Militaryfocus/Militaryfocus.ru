/**
 * Переключатель темы
 */

(function() {
    'use strict';
    
    // Получаем сохраненную тему или используем светлую по умолчанию
    function getTheme() {
        return localStorage.getItem('theme') || 'light';
    }
    
    // Сохраняем выбранную тему
    function saveTheme(theme) {
        localStorage.setItem('theme', theme);
    }
    
    // Применяем тему
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Обновляем состояние переключателя
        const themeSwitch = document.getElementById('theme-switch');
        if (themeSwitch) {
            themeSwitch.checked = theme === 'dark';
        }
        
        // Обновляем иконку
        updateThemeIcon(theme);
        
        // Обновляем мета-тег theme-color
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.content = theme === 'dark' ? '#1a1a1a' : '#ffffff';
        }
    }
    
    // Обновляем иконку темы
    function updateThemeIcon(theme) {
        const iconLight = document.querySelector('.theme-icon-light');
        const iconDark = document.querySelector('.theme-icon-dark');
        
        if (iconLight && iconDark) {
            if (theme === 'dark') {
                iconLight.style.display = 'none';
                iconDark.style.display = 'inline';
            } else {
                iconLight.style.display = 'inline';
                iconDark.style.display = 'none';
            }
        }
    }
    
    // Переключаем тему
    function toggleTheme() {
        const currentTheme = getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        saveTheme(newTheme);
        applyTheme(newTheme);
        
        // Отправляем событие для других компонентов
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
    }
    
    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        // Применяем сохраненную тему
        const savedTheme = getTheme();
        applyTheme(savedTheme);
        
        // Добавляем обработчик для переключателя
        const themeSwitch = document.getElementById('theme-switch');
        if (themeSwitch) {
            themeSwitch.addEventListener('change', toggleTheme);
        }
        
        // Добавляем обработчик для кнопки переключения
        const themeToggleBtn = document.getElementById('theme-toggle-btn');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', toggleTheme);
        }
        
        // Добавляем HTML для переключателя в навбар
        const navbar = document.querySelector('.navbar-nav.ms-auto');
        if (navbar && !document.getElementById('theme-switch-wrapper')) {
            const themeSwitchHtml = `
                <li class="nav-item d-flex align-items-center ms-3">
                    <div class="theme-switch-wrapper" id="theme-switch-wrapper">
                        <label class="theme-switch" for="theme-switch">
                            <input type="checkbox" id="theme-switch">
                            <div class="slider round"></div>
                        </label>
                        <span class="theme-switch-label ms-2">
                            <i class="fas fa-sun theme-icon-light"></i>
                            <i class="fas fa-moon theme-icon-dark" style="display: none;"></i>
                        </span>
                    </div>
                </li>
            `;
            navbar.insertAdjacentHTML('beforeend', themeSwitchHtml);
            
            // Повторно получаем элементы после вставки
            const newThemeSwitch = document.getElementById('theme-switch');
            if (newThemeSwitch) {
                newThemeSwitch.checked = savedTheme === 'dark';
                newThemeSwitch.addEventListener('change', toggleTheme);
            }
            
            updateThemeIcon(savedTheme);
        }
    });
    
    // Слушаем изменения системной темы
    if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        // Функция для обработки изменения системной темы
        function handleSystemThemeChange(e) {
            // Проверяем, есть ли сохраненная пользовательская настройка
            const savedTheme = localStorage.getItem('theme');
            if (!savedTheme) {
                // Если пользователь не выбирал тему, следуем системной
                const systemTheme = e.matches ? 'dark' : 'light';
                applyTheme(systemTheme);
            }
        }
        
        // Слушаем изменения
        mediaQuery.addEventListener('change', handleSystemThemeChange);
        
        // Применяем системную тему при первой загрузке, если нет сохраненной
        if (!localStorage.getItem('theme')) {
            const systemTheme = mediaQuery.matches ? 'dark' : 'light';
            applyTheme(systemTheme);
        }
    }
    
    // Экспортируем функции для использования в других модулях
    window.ThemeSwitcher = {
        getTheme: getTheme,
        setTheme: function(theme) {
            saveTheme(theme);
            applyTheme(theme);
        },
        toggle: toggleTheme
    };
})();