/**
 * Система обратной связи
 * Горячие клавиши: Ctrl+Shift+B (Windows/Linux) или Cmd+Shift+B (Mac)
 */

class FeedbackSystem {
    constructor() {
        this.modal = null;
        this.toast = null;
        this.isInitialized = false;
        this.init();
    }

    init() {
        // Инициализация после загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        if (this.isInitialized) return;
        
        // Добавляем модальное окно в body если его нет
        if (!document.getElementById('feedbackModal')) {
            this.loadModal();
        }

        // Инициализация Bootstrap компонентов
        this.modal = new bootstrap.Modal(document.getElementById('feedbackModal'));
        this.toast = new bootstrap.Toast(document.getElementById('feedbackToast'));

        // Обработчики событий
        this.setupEventListeners();
        
        // Горячие клавиши
        this.setupHotkeys();
        
        // Заполнение технической информации
        this.fillTechnicalInfo();
        
        this.isInitialized = true;
        console.log('🚀 Система обратной связи инициализирована');
    }

    loadModal() {
        // Загружаем модальное окно через AJAX
        fetch('/static/components/feedback_modal.html')
            .then(response => response.text())
            .then(html => {
                document.body.insertAdjacentHTML('beforeend', html);
                this.modal = new bootstrap.Modal(document.getElementById('feedbackModal'));
                this.toast = new bootstrap.Toast(document.getElementById('feedbackToast'));
            })
            .catch(error => {
                console.error('Ошибка загрузки модального окна:', error);
            });
    }

    setupEventListeners() {
        // Обработчик отправки формы
        document.addEventListener('click', (e) => {
            if (e.target.id === 'submitFeedback') {
                this.submitFeedback();
            }
        });

        // Обработчик открытия модального окна
        document.addEventListener('show.bs.modal', (e) => {
            if (e.target.id === 'feedbackModal') {
                this.fillTechnicalInfo();
            }
        });

        // Обработчик закрытия модального окна
        document.addEventListener('hidden.bs.modal', (e) => {
            if (e.target.id === 'feedbackModal') {
                this.resetForm();
                this.removeBackdrop();
            }
        });

        // Обработчик клика по backdrop для закрытия
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.closeModal();
            }
        });
    }

    closeModal() {
        if (this.modal) {
            this.modal.hide();
            this.removeBackdrop();
        }
    }

    removeBackdrop() {
        // Удаляем все backdrop элементы
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.remove();
        });
        // Убираем класс modal-open с body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    setupHotkeys() {
        // Проверяем, что это не мобильное устройство
        if (window.innerWidth < 992) {
            console.log('📱 Система обратной связи отключена на мобильных устройствах');
            return;
        }
        
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+B (Windows/Linux) или Cmd+Shift+B (Mac)
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'B') {
                e.preventDefault();
                this.openFeedbackModal();
            }
        });
    }

    openFeedbackModal() {
        // Проверяем, что это не мобильное устройство
        if (window.innerWidth < 992) {
            console.log('📱 Система обратной связи недоступна на мобильных устройствах');
            return;
        }
        
        if (this.modal) {
            this.fillTechnicalInfo();
            this.modal.show();
        }
    }

    fillTechnicalInfo() {
        // Заполняем скрытые поля технической информацией
        const pageUrl = window.location.href;
        const pageTitle = document.title;
        const userAgent = navigator.userAgent;
        const screenSize = `${screen.width}x${screen.height}`;
        
        // Проверяем авторизацию (если есть данные пользователя в сессии)
        const isAuthenticated = this.checkAuthentication();
        const userName = this.getUserName();
        const userEmail = this.getUserEmail();

        // Заполняем поля
        this.setFieldValue('feedbackPageUrl', pageUrl);
        this.setFieldValue('feedbackPageTitle', pageTitle);
        this.setFieldValue('feedbackUserAgent', userAgent);
        this.setFieldValue('feedbackScreenSize', screenSize);
        this.setFieldValue('feedbackIsAuthenticated', isAuthenticated);

        // Заполняем поля пользователя если авторизован
        if (isAuthenticated) {
            this.setFieldValue('feedbackName', userName);
            this.setFieldValue('feedbackEmail', userEmail);
        }
    }

    checkAuthentication() {
        // Проверяем данные пользователя из скрытых полей
        const userData = document.getElementById('userData');
        if (userData) {
            return userData.getAttribute('data-is-authenticated') === 'true';
        }
        return false;
    }

    getUserName() {
        // Получаем имя пользователя из скрытых полей
        const userData = document.getElementById('userData');
        if (userData) {
            return userData.getAttribute('data-user-name') || '';
        }
        return '';
    }

    getUserEmail() {
        // Получаем email пользователя из скрытых полей
        const userData = document.getElementById('userData');
        if (userData) {
            return userData.getAttribute('data-user-email') || '';
        }
        return '';
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
        }
    }

    async submitFeedback() {
        const submitBtn = document.getElementById('submitFeedback');
        const originalText = submitBtn.innerHTML;
        
        // Показываем индикатор загрузки
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Отправка...';
        submitBtn.disabled = true;

        try {
            // Собираем данные формы
            const formData = this.collectFormData();
            
            // Валидация
            if (!this.validateForm(formData)) {
                return;
            }

            // Отправляем данные
            const response = await this.sendFeedback(formData);
            
            if (response.success) {
                this.showSuccess('Сообщение отправлено успешно!');
                this.modal.hide();
                this.resetForm();
            } else {
                this.showError('Ошибка при отправке: ' + response.message);
            }

        } catch (error) {
            console.error('Ошибка отправки обратной связи:', error);
            this.showError('Произошла ошибка при отправке сообщения');
        } finally {
            // Восстанавливаем кнопку
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    collectFormData() {
        return {
            type: document.getElementById('feedbackType').value,
            description: document.getElementById('feedbackDescription').value,
            suggestion: document.getElementById('feedbackSuggestion').value,
            page_url: document.getElementById('feedbackPageUrl').value,
            page_title: document.getElementById('feedbackPageTitle').value,
            user_agent: document.getElementById('feedbackUserAgent').value,
            screen_size: document.getElementById('feedbackScreenSize').value,
            user_name: document.getElementById('feedbackName').value,
            user_email: document.getElementById('feedbackEmail').value,
            is_authenticated: document.getElementById('feedbackIsAuthenticated').value
        };
    }

    validateForm(data) {
        if (!data.type) {
            this.showError('Выберите тип сообщения');
            return false;
        }
        
        if (!data.description.trim()) {
            this.showError('Опишите проблему');
            return false;
        }
        
        return true;
    }

    async sendFeedback(data) {
        const params = new URLSearchParams(data);
        const response = await fetch('/api/v1/feedback?' + params.toString(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        return await response.json();
    }

    resetForm() {
        document.getElementById('feedbackForm').reset();
        this.fillTechnicalInfo();
    }

    showSuccess(message) {
        const toastMessage = document.getElementById('feedbackToastMessage');
        if (toastMessage) {
            toastMessage.textContent = message;
            this.toast.show();
        }
    }

    showError(message) {
        // Показываем ошибку в модальном окне
        const modalBody = document.querySelector('#feedbackModal .modal-body');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        modalBody.insertBefore(errorDiv, modalBody.firstChild);
        
        // Автоматически убираем через 5 секунд
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
}

// Инициализация системы обратной связи
const feedbackSystem = new FeedbackSystem();

// Экспорт для использования в других скриптах
window.feedbackSystem = feedbackSystem; 