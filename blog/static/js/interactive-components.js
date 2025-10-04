/**
 * Интерактивные компоненты для блога
 */

class InteractiveComponents {
    constructor() {
        this.init();
    }

    init() {
        this.initLikeButtons();
        this.initBookmarkButtons();
        this.initShareButtons();
        this.initCommentForm();
        this.initImageViewer();
        this.initContentCopy();
        this.initReadingProgress();
        this.initScrollSpy();
    }

    // Лайки
    initLikeButtons() {
        document.addEventListener('click', async (e) => {
            const likeBtn = e.target.closest('.like-button');
            if (!likeBtn) return;

            e.preventDefault();
            const postId = likeBtn.dataset.postId;
            const likeCount = likeBtn.querySelector('.like-count');
            const icon = likeBtn.querySelector('i');

            // Анимация
            icon.classList.add('animate__animated', 'animate__heartBeat');
            
            try {
                const response = await fetch(`/api/posts/${postId}/like`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });

                const data = await response.json();
                
                if (data.success) {
                    likeBtn.classList.toggle('liked');
                    likeCount.textContent = data.likes_count;
                    
                    // Изменяем иконку
                    if (data.liked) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        this.showToast('Добавлено в понравившиеся', 'success');
                    } else {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                    }
                }
            } catch (error) {
                this.showToast('Ошибка при обработке лайка', 'error');
            }

            setTimeout(() => {
                icon.classList.remove('animate__animated', 'animate__heartBeat');
            }, 1000);
        });
    }

    // Закладки
    initBookmarkButtons() {
        document.addEventListener('click', async (e) => {
            const bookmarkBtn = e.target.closest('.bookmark-btn');
            if (!bookmarkBtn) return;

            e.preventDefault();
            const postId = bookmarkBtn.dataset.postId;
            const icon = bookmarkBtn.querySelector('i');

            try {
                const response = await fetch(`/api/posts/${postId}/bookmark`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });

                const data = await response.json();
                
                if (data.success) {
                    bookmarkBtn.classList.toggle('bookmarked');
                    
                    if (data.bookmarked) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        this.showToast('Добавлено в закладки', 'success');
                    } else {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                        this.showToast('Удалено из закладок', 'info');
                    }
                }
            } catch (error) {
                this.showToast('Ошибка при работе с закладками', 'error');
            }
        });
    }

    // Поделиться
    initShareButtons() {
        document.addEventListener('click', async (e) => {
            const shareBtn = e.target.closest('.share-btn');
            if (!shareBtn) return;

            e.preventDefault();
            const postId = shareBtn.dataset.postId;
            const postTitle = shareBtn.dataset.title || document.title;
            const postUrl = shareBtn.dataset.url || window.location.href;

            // Создаем модальное окно для шаринга
            const shareModal = this.createShareModal(postTitle, postUrl);
            document.body.appendChild(shareModal);
            
            // Показываем модальное окно
            setTimeout(() => shareModal.classList.add('show'), 10);
        });
    }

    createShareModal(title, url) {
        const modal = document.createElement('div');
        modal.className = 'share-modal';
        modal.innerHTML = `
            <div class="share-modal-content">
                <div class="share-modal-header">
                    <h3>Поделиться</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="share-modal-body">
                    <div class="share-buttons-grid">
                        <button class="share-option" data-network="twitter">
                            <i class="fab fa-twitter"></i>
                            <span>Twitter</span>
                        </button>
                        <button class="share-option" data-network="facebook">
                            <i class="fab fa-facebook-f"></i>
                            <span>Facebook</span>
                        </button>
                        <button class="share-option" data-network="telegram">
                            <i class="fab fa-telegram-plane"></i>
                            <span>Telegram</span>
                        </button>
                        <button class="share-option" data-network="whatsapp">
                            <i class="fab fa-whatsapp"></i>
                            <span>WhatsApp</span>
                        </button>
                        <button class="share-option" data-network="vk">
                            <i class="fab fa-vk"></i>
                            <span>VKontakte</span>
                        </button>
                        <button class="share-option" data-network="copy">
                            <i class="fas fa-link"></i>
                            <span>Копировать</span>
                        </button>
                    </div>
                    <div class="share-url-input">
                        <input type="text" value="${url}" readonly>
                        <button class="copy-url-btn">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Обработчики
        modal.querySelector('.close-btn').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
                setTimeout(() => modal.remove(), 300);
            }
        });

        // Кнопки шаринга
        modal.querySelectorAll('.share-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const network = btn.dataset.network;
                this.shareToNetwork(network, title, url);
            });
        });

        // Копирование URL
        modal.querySelector('.copy-url-btn').addEventListener('click', () => {
            const input = modal.querySelector('input');
            input.select();
            document.execCommand('copy');
            this.showToast('Ссылка скопирована', 'success');
        });

        return modal;
    }

    shareToNetwork(network, title, url) {
        const shareUrls = {
            twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`,
            facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
            telegram: `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`,
            whatsapp: `https://wa.me/?text=${encodeURIComponent(title + ' ' + url)}`,
            vk: `https://vk.com/share.php?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`,
        };

        if (network === 'copy') {
            navigator.clipboard.writeText(url).then(() => {
                this.showToast('Ссылка скопирована', 'success');
            });
        } else if (shareUrls[network]) {
            window.open(shareUrls[network], '_blank', 'width=600,height=400');
        }
    }

    // Форма комментариев
    initCommentForm() {
        const commentForm = document.querySelector('#comment-form');
        if (!commentForm) return;

        const textarea = commentForm.querySelector('textarea');
        const charCount = commentForm.querySelector('.char-count');
        const submitBtn = commentForm.querySelector('button[type="submit"]');

        // Счетчик символов
        if (textarea && charCount) {
            textarea.addEventListener('input', () => {
                const count = textarea.value.length;
                const max = textarea.maxLength || 1000;
                charCount.textContent = `${count}/${max}`;
                
                if (count > max * 0.9) {
                    charCount.classList.add('text-danger');
                } else {
                    charCount.classList.remove('text-danger');
                }
            });
        }

        // Отправка формы
        commentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(commentForm);
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';

            try {
                const response = await fetch(commentForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });

                const data = await response.json();
                
                if (data.success) {
                    // Добавляем комментарий в DOM
                    this.addCommentToDOM(data.comment);
                    commentForm.reset();
                    this.showToast('Комментарий добавлен', 'success');
                } else {
                    this.showToast(data.message || 'Ошибка при добавлении комментария', 'error');
                }
            } catch (error) {
                this.showToast('Ошибка при отправке комментария', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Отправить';
            }
        });
    }

    addCommentToDOM(comment) {
        const commentsContainer = document.querySelector('.comments-list');
        if (!commentsContainer) return;

        const commentHTML = `
            <div class="comment-item animate__animated animate__fadeInUp" data-comment-id="${comment.id}">
                <div class="comment-avatar">
                    <img src="${comment.author.avatar || '/static/images/default-avatar.png'}" 
                         alt="${comment.author.username}">
                </div>
                <div class="comment-content">
                    <div class="comment-header">
                        <span class="comment-author">${comment.author.username}</span>
                        <span class="comment-date">только что</span>
                    </div>
                    <div class="comment-text">${comment.content}</div>
                    <div class="comment-actions">
                        <button class="comment-action like-comment" data-comment-id="${comment.id}">
                            <i class="far fa-heart"></i> 0
                        </button>
                        <button class="comment-action reply-comment" data-comment-id="${comment.id}">
                            <i class="fas fa-reply"></i> Ответить
                        </button>
                    </div>
                </div>
            </div>
        `;

        commentsContainer.insertAdjacentHTML('afterbegin', commentHTML);
    }

    // Просмотр изображений
    initImageViewer() {
        document.addEventListener('click', (e) => {
            const img = e.target.closest('.post-content img, .gallery-image');
            if (!img) return;

            const viewer = document.createElement('div');
            viewer.className = 'image-viewer';
            viewer.innerHTML = `
                <div class="image-viewer-content">
                    <img src="${img.src}" alt="${img.alt || ''}">
                    <button class="viewer-close">&times;</button>
                    <div class="viewer-controls">
                        <button class="viewer-zoom-in"><i class="fas fa-search-plus"></i></button>
                        <button class="viewer-zoom-out"><i class="fas fa-search-minus"></i></button>
                        <button class="viewer-fullscreen"><i class="fas fa-expand"></i></button>
                    </div>
                </div>
            `;

            document.body.appendChild(viewer);
            document.body.style.overflow = 'hidden';

            // Закрытие
            viewer.querySelector('.viewer-close').addEventListener('click', () => {
                viewer.remove();
                document.body.style.overflow = '';
            });

            viewer.addEventListener('click', (e) => {
                if (e.target === viewer) {
                    viewer.remove();
                    document.body.style.overflow = '';
                }
            });

            // Zoom
            let scale = 1;
            const viewerImg = viewer.querySelector('img');
            
            viewer.querySelector('.viewer-zoom-in').addEventListener('click', () => {
                scale += 0.2;
                viewerImg.style.transform = `scale(${scale})`;
            });

            viewer.querySelector('.viewer-zoom-out').addEventListener('click', () => {
                scale = Math.max(0.5, scale - 0.2);
                viewerImg.style.transform = `scale(${scale})`;
            });
        });
    }

    // Копирование кода
    initContentCopy() {
        document.querySelectorAll('pre code').forEach(block => {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-copy-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Копировать код';

            const pre = block.parentElement;
            pre.style.position = 'relative';
            pre.appendChild(copyBtn);

            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(block.textContent).then(() => {
                    copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                    this.showToast('Код скопирован', 'success');
                    
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                    }, 2000);
                });
            });
        });
    }

    // Прогресс чтения
    initReadingProgress() {
        const article = document.querySelector('.post-content');
        if (!article) return;

        const progressBar = document.createElement('div');
        progressBar.className = 'reading-progress';
        document.body.appendChild(progressBar);

        window.addEventListener('scroll', () => {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            const scrollTop = window.scrollY;
            const progress = (scrollTop / (documentHeight - windowHeight)) * 100;
            
            progressBar.style.width = `${Math.min(100, progress)}%`;
        });
    }

    // ScrollSpy для оглавления
    initScrollSpy() {
        const toc = document.querySelector('.table-of-contents');
        if (!toc) return;

        const headings = document.querySelectorAll('.post-content h2, .post-content h3');
        const tocLinks = toc.querySelectorAll('a');

        window.addEventListener('scroll', () => {
            let current = '';
            
            headings.forEach(heading => {
                const rect = heading.getBoundingClientRect();
                if (rect.top <= 100) {
                    current = heading.id;
                }
            });

            tocLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${current}`) {
                    link.classList.add('active');
                }
            });
        });
    }

    // Утилиты
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    showToast(message, type = 'info') {
        if (window.modernUI) {
            window.modernUI.showToast(message, type);
        }
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    new InteractiveComponents();
});

// CSS для компонентов
const style = document.createElement('style');
style.textContent = `
/* Share Modal */
.share-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.share-modal.show {
    opacity: 1;
}

.share-modal-content {
    background: white;
    border-radius: 16px;
    max-width: 500px;
    width: 90%;
    animation: slideInUp 0.3s ease;
}

.share-modal-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.share-modal-body {
    padding: 1.5rem;
}

.share-buttons-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.share-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    background: white;
    cursor: pointer;
    transition: all 0.3s ease;
}

.share-option:hover {
    border-color: var(--primary-color);
    transform: translateY(-2px);
}

.share-option i {
    font-size: 1.5rem;
}

.share-url-input {
    display: flex;
    gap: 0.5rem;
}

.share-url-input input {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
}

.copy-url-btn {
    padding: 0.75rem 1rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.copy-url-btn:hover {
    background: var(--primary-hover);
}

/* Image Viewer */
.image-viewer {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1060;
    animation: fadeIn 0.3s ease;
}

.image-viewer-content {
    position: relative;
    max-width: 90%;
    max-height: 90%;
}

.image-viewer img {
    max-width: 100%;
    max-height: 90vh;
    transition: transform 0.3s ease;
}

.viewer-close {
    position: absolute;
    top: -40px;
    right: 0;
    background: none;
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
}

.viewer-controls {
    position: absolute;
    bottom: -60px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 1rem;
}

.viewer-controls button {
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.viewer-controls button:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Code Copy Button */
.code-copy-btn {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.25rem 0.5rem;
    background: rgba(0, 0, 0, 0.1);
    border: none;
    border-radius: 4px;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.3s ease;
}

.code-copy-btn:hover {
    background: rgba(0, 0, 0, 0.2);
    color: white;
}

/* Reading Progress */
.reading-progress {
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    background: var(--gradient-primary);
    z-index: 1040;
    transition: width 0.1s ease;
}

/* Comment Animations */
.comment-item {
    opacity: 0;
    transform: translateY(20px);
    animation: fadeInUp 0.5s ease forwards;
}

@keyframes slideInUp {
    from {
        transform: translateY(30px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
`;
document.head.appendChild(style);