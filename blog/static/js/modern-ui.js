/**
 * Современный UI для блога
 */

// Утилиты
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Класс для управления UI
class ModernUI {
    constructor() {
        this.init();
    }

    init() {
        this.initNavbar();
        this.initAnimations();
        this.initLazyLoading();
        this.initInfiniteScroll();
        this.initTooltips();
        this.initModals();
        this.initFAB();
        this.initParallax();
        this.initSmoothScroll();
    }

    // Навбар с эффектом при скролле
    initNavbar() {
        const navbar = $('.modern-navbar');
        if (!navbar) return;

        let lastScroll = 0;
        
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            
            // Скрываем/показываем навбар при скролле
            if (currentScroll > lastScroll && currentScroll > 100) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
            
            lastScroll = currentScroll;
        });
    }

    // Анимации при скролле
    initAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Наблюдаем за элементами с анимацией
        $$('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    // Ленивая загрузка изображений
    initLazyLoading() {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        });

        $$('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Бесконечный скролл
    initInfiniteScroll() {
        let page = 1;
        let loading = false;
        const loader = $('.infinite-scroll-loader');
        const container = $('.posts-container');
        
        if (!loader || !container) return;

        const loadMore = async () => {
            if (loading) return;
            
            loading = true;
            loader.style.display = 'block';
            
            try {
                const response = await fetch(`/api/posts?page=${++page}`);
                const data = await response.json();
                
                if (data.posts && data.posts.length > 0) {
                    data.posts.forEach(post => {
                        container.insertAdjacentHTML('beforeend', this.createPostCard(post));
                    });
                    
                    // Инициализируем анимации для новых элементов
                    this.initAnimations();
                } else {
                    // Больше постов нет
                    window.removeEventListener('scroll', handleScroll);
                    loader.innerHTML = '<p>Все посты загружены</p>';
                }
            } catch (error) {
                console.error('Ошибка загрузки постов:', error);
                this.showToast('Ошибка загрузки постов', 'error');
            } finally {
                loading = false;
                loader.style.display = 'none';
            }
        };

        const handleScroll = () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                loadMore();
            }
        };

        window.addEventListener('scroll', handleScroll);
    }

    // Создание карточки поста
    createPostCard(post) {
        return `
            <div class="col-md-6 col-lg-4 mb-4 animate-on-scroll">
                <div class="modern-card">
                    ${post.image_url ? `
                        <img src="${post.image_url}" alt="${post.title}" class="modern-card-image">
                    ` : ''}
                    <div class="modern-card-body">
                        ${post.category ? `
                            <span class="modern-card-category">${post.category.name}</span>
                        ` : ''}
                        <h3 class="modern-card-title">${post.title}</h3>
                        <p class="modern-card-excerpt">${post.excerpt}</p>
                        <div class="modern-card-meta">
                            <div class="modern-card-author">
                                <img src="${post.author.avatar || '/static/images/default-avatar.png'}" 
                                     alt="${post.author.username}" class="author-avatar">
                                <span>${post.author.username}</span>
                            </div>
                            <span>${this.formatDate(post.created_at)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Форматирование даты
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'только что';
        if (diff < 3600000) return `${Math.floor(diff / 60000)} мин. назад`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)} ч. назад`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)} дн. назад`;
        
        return date.toLocaleDateString('ru-RU');
    }

    // Тултипы
    initTooltips() {
        $$('[data-tooltip]').forEach(el => {
            el.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip-modern';
                tooltip.textContent = e.target.dataset.tooltip;
                document.body.appendChild(tooltip);
                
                const rect = e.target.getBoundingClientRect();
                tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
                tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
                
                setTimeout(() => tooltip.classList.add('show'), 10);
            });
            
            el.addEventListener('mouseleave', () => {
                $$('.tooltip-modern').forEach(tooltip => tooltip.remove());
            });
        });
    }

    // Модальные окна
    initModals() {
        $$('[data-modal-trigger]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = trigger.dataset.modalTrigger;
                this.openModal(modalId);
            });
        });

        $$('.modal-close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                this.closeModal(e.target.closest('.modal-modern'));
            });
        });

        // Закрытие по клику вне модального окна
        $$('.modal-modern').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        });
    }

    openModal(modalId) {
        const modal = $(`#${modalId}`);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modal) {
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    // Floating Action Button
    initFAB() {
        const fab = $('.fab');
        if (!fab) return;

        // Показываем/скрываем при скролле
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 500) {
                fab.style.transform = 'scale(1)';
            } else {
                fab.style.transform = 'scale(0)';
            }
            
            lastScroll = currentScroll;
        });

        // Скролл наверх
        fab.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Параллакс эффект
    initParallax() {
        const parallaxElements = $$('.parallax');
        
        if (parallaxElements.length === 0) return;
        
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            
            parallaxElements.forEach(el => {
                const speed = el.dataset.speed || 0.5;
                const yPos = -(scrolled * speed);
                el.style.transform = `translateY(${yPos}px)`;
            });
        });
    }

    // Плавный скролл
    initSmoothScroll() {
        $$('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = $(anchor.getAttribute('href'));
                
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Toast уведомления
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast-modern ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        let container = $('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }

    // Skeleton loading
    showSkeleton(container, count = 3) {
        const skeletons = Array(count).fill(0).map(() => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="skeleton-card">
                    <div class="skeleton skeleton-image"></div>
                    <div class="p-3">
                        <div class="skeleton skeleton-text" style="width: 60%"></div>
                        <div class="skeleton skeleton-title"></div>
                        <div class="skeleton skeleton-text"></div>
                        <div class="skeleton skeleton-text" style="width: 80%"></div>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = skeletons;
    }

    // Копирование в буфер обмена
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Скопировано в буфер обмена', 'success');
        }).catch(() => {
            this.showToast('Ошибка копирования', 'error');
        });
    }

    // Поделиться
    share(title, url) {
        if (navigator.share) {
            navigator.share({
                title: title,
                url: url
            }).catch(() => {});
        } else {
            // Fallback - копируем ссылку
            this.copyToClipboard(url);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.modernUI = new ModernUI();
});

// Экспортируем для использования в других модулях
window.ModernUI = ModernUI;